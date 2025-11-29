import json
import os
import time
import logging
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from threading import Lock
from datetime import datetime, timedelta

# Import vector store for semantic search
try:
    from utils.vector_db import get_vector_store
    VECTOR_DB_ENABLED = True
except ImportError as e:
    logging.warning(f"Vector DB not available: {e}")
    VECTOR_DB_ENABLED = False

# Import query classifier for cost optimization
try:
    from utils.query_classifier import classify_query, QueryClassifier
    from utils.pandas_executor import PandasExecutor
    from utils.template_engine import TemplateEngine
    QUERY_CLASSIFIER_ENABLED = True
except ImportError as e:
    logging.warning(f"Query classifier not available: {e}")
    QUERY_CLASSIFIER_ENABLED = False

def update_ai_stats(response_type='text', input_tokens=0, output_tokens=0, response_time=0, embeddings_created=0):
    """Update AI usage statistics in session state"""
    if 'ai_stats' not in st.session_state:
        st.session_state.ai_stats = {
            'total_queries': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_embeddings': 0,
            'queries_by_type': {'text': 0, 'visualization': 0, 'analysis': 0},
            'avg_response_time': 0,
            'session_start': datetime.now()
        }
    
    stats = st.session_state.ai_stats
    stats['total_queries'] += 1
    stats['total_input_tokens'] += input_tokens
    stats['total_output_tokens'] += output_tokens
    stats['total_embeddings'] += embeddings_created
    
    # Update query type counters
    if response_type in stats['queries_by_type']:
        stats['queries_by_type'][response_type] += 1
    
    # Update average response time
    total_time = stats['avg_response_time'] * (stats['total_queries'] - 1) + response_time
    stats['avg_response_time'] = total_time / stats['total_queries']

# Rate limiting configuration
MAX_REQUESTS_PER_MINUTE = 60
REQUEST_WINDOW = 60  # seconds
TOKEN_FILL_RATE = MAX_REQUESTS_PER_MINUTE / REQUEST_WINDOW

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not found")
genai.configure(api_key=GEMINI_API_KEY)


def _format_history_for_ai(chat_history):
    """
    Pre-processes the chat history to ensure the 'content' field for every message
    is a simple string, which is required by the Ollama API.
    """
    formatted_history = []
    for msg in chat_history:
        role = msg["role"]
        content = msg["content"]
        if role == "assistant":
            if isinstance(content, dict):
                text_content = content.get("content", "")
                if content.get("response_type") == "chart":
                    text_content += "\n(A chart was generated to visualize this.)"
                formatted_history.append({"role": "assistant", "content": text_content})
        else:
            # User content is always a simple string
            formatted_history.append({"role": "user", "content": content})
    return formatted_history


def _clean_json_response(raw_content):
    """
    Aggressively cleans potential JSON response from various formats.
    Handles: markdown code blocks, escaped quotes, invalid escape sequences, leading/trailing whitespace.
    """
    if not raw_content:
        raise ValueError("Empty response from model")

    cleaned = raw_content.strip()

    # Remove markdown code blocks
    if cleaned.startswith("```"):
        lines = cleaned.split('\n')
        if lines[0].strip().lower() in ['```json', '```']:
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        cleaned = '\n'.join(lines).strip()

    # Handle single backticks
    cleaned = cleaned.strip('`').strip()

    # Remove "json" prefix if present
    if cleaned.lower().startswith('json'):
        cleaned = cleaned[4:].strip()
    
    # Fix invalid escape sequences (common in AI responses with Windows paths, LaTeX, etc.)
    # Only fix invalid escapes, preserve valid ones (\n, \t, \r, \", \\, \/, \b, \f, \uXXXX)
    import re
    
    # Pattern for valid JSON escape sequences
    valid_escapes = r'\\["\\/bfnrtu]'
    
    # Find all backslashes that aren't part of valid escapes
    def replace_invalid_escape(match):
        char_after_backslash = match.group(1)
        # If it's not a valid escape character, escape the backslash
        if not re.match(r'["\\/bfnrtu]', char_after_backslash):
            return '\\\\' + char_after_backslash
        return match.group(0)
    
    # Replace invalid escape sequences
    cleaned = re.sub(r'\\(.)', replace_invalid_escape, cleaned)

    return cleaned


class RateLimiter:
    """
    Token bucket algorithm implementation for rate limiting.
    """
    def __init__(self, tokens_per_second):
        self.tokens = MAX_REQUESTS_PER_MINUTE
        self.tokens_per_second = tokens_per_second
        self.last_update = time.time()
        self.lock = Lock()

    def _add_new_tokens(self):
        now = time.time()
        time_passed = now - self.last_update
        new_tokens = time_passed * self.tokens_per_second
        self.tokens = min(MAX_REQUESTS_PER_MINUTE, self.tokens + new_tokens)
        self.last_update = now

    def acquire(self):
        with self.lock:
            self._add_new_tokens()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

class GeminiClient:
    """
    A singleton client for handling Gemini API interactions.
    Manages chat history, rate limiting, and provides structured responses.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GeminiClient, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Default model - can be changed via set_model
        self.current_model_name = 'gemini-2.5-flash-lite'
        self.model = genai.GenerativeModel(self.current_model_name)
        self.rate_limiter = RateLimiter(TOKEN_FILL_RATE)
        self._initialized = True

    def set_model(self, model_name):
        """Change the active Gemini model"""
        self.current_model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Switched to model: {model_name}")

    def get_chat_session(self):
        """Creates a new chat session with empty history."""
        return self.model.start_chat(history=[])

    def process_messages(self, messages, format="json"):
        """
        Process a sequence of messages with rate limiting.
        
        Args:
            messages (list): List of message dictionaries with 'role' and 'content'
            format (str): Expected response format (default: "json")
            
        Returns:
            str: The model's response text
            
        Raises:
            Exception: If rate limit is exceeded or API error occurs
        """
        if not self.rate_limiter.acquire():
            logger.warning("Rate limit exceeded, waiting for token renewal")
            raise Exception("rate_limit_exceeded")

        try:
            chat = self.get_chat_session()
            system_context = ""

            # Collect system messages as context
            for message in messages:
                if message["role"] == "system":
                    system_context += message["content"] + "\n"

            # Prepend system context to first user message
            if system_context and any(m["role"] == "user" for m in messages):
                for i, message in enumerate(messages):
                    if message["role"] == "user":
                        messages[i]["content"] = f"{system_context}\n{message['content']}"
                        break

            # Send messages
            response = None
            for message in messages:
                if message["role"] != "system":
                    response = chat.send_message(message["content"])

            if response is None:
                raise ValueError("No valid messages to process")

            return response.text

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise


# Initialize global Gemini client
client = GeminiClient()


def get_ai_response(profile, history, domain_info=None, user_id=None, df=None):
    """
    AI response using the centralized system prompt with vector context and domain awareness.
    
    NEW: Includes smart query routing for cost optimization!
    - Simple queries (count, sum, avg) → Execute with Pandas directly (no AI call)
    - Template queries → Use cached community templates
    - Complex queries → Route to Gemini AI
    
    Args:
        profile: Data profile dict or JSON string
        history: Chat message history
        domain_info: Dict with domain detection info
        user_id: User ID for personal workspace
        df: Optional DataFrame for direct Pandas execution (cost savings!)
    """
    start_time = time.time()  # Track response time
    
    # Extract domain info for vector storage
    current_domain = domain_info.get('domain', 'general') if domain_info else 'general'
    
    # Get user ID for personal workspace (HYBRID MODEL)
    current_user = user_id or 'anonymous'
    
    # Get the last user message
    last_user_message = None
    if history:
        for msg in reversed(history):
            if msg.get("role") == "user":
                last_user_message = msg.get("content")
                break
    
    # ============= SMART QUERY ROUTING FOR COST OPTIMIZATION =============
    # Try to handle simple queries with Pandas directly (saves API costs!)
    if QUERY_CLASSIFIER_ENABLED and df is not None and last_user_message:
        try:
            # Get available columns for classification
            available_columns = df.columns.tolist() if hasattr(df, 'columns') else []
            
            # Classify the query
            classification = classify_query(last_user_message, available_columns, current_domain)
            
            if classification.get("query_type") == "simple" and classification.get("confidence", 0) >= 0.8:
                # Execute with Pandas directly - NO AI CALL NEEDED! 💰
                logger.info(f"⚡ Simple query detected: '{last_user_message}' → Executing with Pandas")
                
                executor = PandasExecutor(df)
                operation = classification.get("operation")
                column = classification.get("column")
                
                result = executor.execute(operation, column)
                
                # Add metadata about cost savings
                result["_query_type"] = "simple"
                result["_cost_savings"] = True
                result["_classification"] = classification
                
                # Update AI stats (no AI tokens used!)
                update_ai_stats(
                    response_type='text',
                    input_tokens=0,  # No AI call!
                    output_tokens=0,
                    response_time=time.time() - start_time,
                    embeddings_created=0
                )
                
                logger.info(f"✅ Simple query executed in {time.time() - start_time:.2f}s (no AI call)")
                return result
            
            elif classification.get("query_type") == "template" and classification.get("confidence", 0) >= 0.7:
                # Execute with Template Engine - Uses community templates! 📚
                template_key = classification.get("template_key")
                logger.info(f"📚 Template query detected: '{last_user_message}' → Using template '{template_key}'")
                
                engine = TemplateEngine(df)
                can_execute, missing = engine.can_execute_template(template_key)
                
                if can_execute:
                    result = engine.execute_template(template_key)
                    
                    # Add metadata
                    result["_query_type"] = "template"
                    result["_cost_savings"] = True
                    result["_template_key"] = template_key
                    result["_classification"] = classification
                    
                    # Update AI stats (no AI tokens used!)
                    update_ai_stats(
                        response_type='visualization' if result.get('is_visualizable') else 'text',
                        input_tokens=0,
                        output_tokens=0,
                        response_time=time.time() - start_time,
                        embeddings_created=0
                    )
                    
                    logger.info(f"✅ Template executed in {time.time() - start_time:.2f}s (no AI call)")
                    return result
                else:
                    logger.info(f"Template '{template_key}' missing columns: {missing}, falling back to AI")
                
        except Exception as e:
            logger.warning(f"Query classification failed, falling back to AI: {e}")
            # Fall through to AI processing
    
    # ============= COMPLEX QUERY → ROUTE TO AI =============
    
    try:
        # Read the main system prompt from file
        with open("prompts/system_prompt.txt", "r") as f:
            base_system_prompt = f.read()
        
        # Add dynamic context to the existing prompt
        # FIX: Handle both string and dict profiles
        if isinstance(profile, dict):
            columns_info = profile.get("columns", [])
            # Handle both formats: list of dicts with 'name' key, or list of strings
            if columns_info and isinstance(columns_info[0], dict):
                available_columns = [col.get('name', '') for col in columns_info if isinstance(col, dict)]
            else:
                available_columns = [str(col) for col in columns_info]
            dataset_name = profile.get("filename", "unknown")
        else:
            # If profile is a string, try to parse it
            try:
                import json
                profile_dict = json.loads(profile) if isinstance(profile, str) else {}
                columns_info = profile_dict.get("columns", [])
                # Handle both formats: list of dicts with 'name' key, or list of strings
                if columns_info and isinstance(columns_info[0], dict):
                    available_columns = [col.get('name', '') for col in columns_info if isinstance(col, dict)]
                else:
                    available_columns = [str(col) for col in columns_info]
                dataset_name = profile_dict.get("filename", "unknown")
            except:
                available_columns = []
                dataset_name = "unknown"
                profile_dict = {}
        
        # Clean up column names - remove any empty strings
        available_columns = [col for col in available_columns if col]
        
        # Get the last user message for semantic search
        last_user_message = None
        if history:
            for msg in reversed(history):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content")
                    break
        
        # Try to get relevant context from vector DB
        vector_context = ""
        rag_context_used = False
        rag_context_preview = ""
        
        if VECTOR_DB_ENABLED and last_user_message:
            try:
                vector_store = get_vector_store()
                relevant_context = vector_store.get_relevant_context(last_user_message, limit=2)
                if relevant_context:
                    vector_context = f"""

**RELEVANT PAST CONTEXT:**
{relevant_context}

Use this context to provide more informed and consistent analysis.
"""
                    rag_context_used = True
                    rag_context_preview = relevant_context[:200] + "..." if len(relevant_context) > 200 else relevant_context
                    logger.info("Added vector context to prompt")
            except Exception as ve:
                logger.warning(f"Could not retrieve vector context: {ve}")
        
        # Extract detailed column info from profile
        column_details = ""
        sample_data_preview = ""
        
        if isinstance(profile, dict):
            columns_info = profile.get("columns", [])
            if columns_info:
                column_details = "\n".join([
                    f"- {col.get('name')} ({col.get('dtype')}) - {col.get('non_null_count')} non-null, {col.get('unique_count')} unique"
                    for col in columns_info[:15]  # Show first 15 columns
                ])
            
            sample_data = profile.get("sample_data", [])
            if sample_data and len(sample_data) > 0:
                sample_data_preview = f"\n\nSAMPLE DATA (first 3 rows):\n{json.dumps(sample_data, indent=2, default=str)}"
        
        # Enhance the base prompt with rich data context
        enhanced_prompt = base_system_prompt + f"""

**CURRENT DATA CONTEXT:**
Dataset: {dataset_name}
Available columns: {', '.join(available_columns) if available_columns else 'Loading...'}

COLUMN DETAILS:
{column_details if column_details else 'Column information loading...'}
{sample_data_preview}

**IMPORTANT REMINDERS:**
1. For "count by X" queries → Use df['X'].value_counts() directly
2. For "total/sum" queries → Use df['column'].sum() or .groupby().sum()
3. For "average" queries → Use df['column'].mean() or .groupby().mean()
4. VALIDATE columns exist before using them
5. Keep it simple - don't create new columns for basic aggregations

Common derived columns (if available):
- total_sale (quantity * price)
- month, year, month_name (from date columns)
""" + vector_context
    
        # Format history for AI
        formatted_history = _format_history_for_ai(history)

        # Build messages
        # IMPORTANT: profile is already a JSON string from create_data_profile(), don't double-encode!
        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": f"Here is the profile for the current dataset:\n{profile}"}
        ]
        messages.extend(formatted_history[-4:])  # Use last 4 messages for context

        # Make API call
        with st.spinner("Analyzing your data..."):
            try:
                max_retries = 3
                retry_delay = 2  # seconds
                
                for attempt in range(max_retries):
                    try:
                        response_content = client.process_messages(messages=messages)
                        logger.info("Successfully received response from Gemini API")
                        break
                    except Exception as e:
                        if str(e) == "rate_limit_exceeded" and attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)
                            logger.info(f"Rate limit hit, waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        raise
                
                cleaned_content = _clean_json_response(response_content)
                
                try:
                    ai_response = json.loads(cleaned_content)
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON parsing error: {str(json_err)}")
                    logger.error(f"Raw content preview: {response_content[:200]}...")
                    return {
                        "response_type": "error",
                        "content": "I apologize, but I had trouble formatting my response properly. Could you please try asking your question again?",
                        "reasoning": f"JSON parsing failed: {str(json_err)}. The AI response contained formatting issues that prevented proper parsing.",
                        "is_visualizable": False,
                        "suggested_actions": [
                            "Rephrase your question",
                            "Try breaking complex queries into simpler parts",
                            "Ask the question differently"
                        ]
                    }
                
                # Store interaction in vector DB for future semantic search with domain info
                if VECTOR_DB_ENABLED and last_user_message and isinstance(ai_response, dict):
                    try:
                        from utils.domain_detector import get_schema_signature
                        vector_store = get_vector_store()
                        
                        # Generate schema signature (if we have access to the dataframe)
                        schema_sig = None
                        # Schema would need to be passed in - skip for now, can enhance later
                        
                        # Determine query type from AI response
                        query_type = "complex"
                        if ai_response.get("is_visualizable"):
                            query_type = "chart"
                        
                        # Store user message with HYBRID MODEL metadata
                        vector_store.store_chat_message(
                            role="user",
                            content=last_user_message,
                            dataset_name=dataset_name,
                            domain=current_domain,
                            schema_signature=schema_sig,
                            query_type=query_type,
                            tier="user",  # Personal workspace
                            user_id=current_user
                        )
                        # Store assistant response
                        assistant_content = ai_response.get("content", "")
                        if assistant_content:
                            vector_store.store_chat_message(
                                role="assistant",
                                content=assistant_content[:500],  # Store first 500 chars
                                dataset_name=dataset_name,
                                domain=current_domain,
                                query_type=query_type,
                                tier="user",  # Personal workspace
                                user_id=current_user
                            )
                        logger.info(f"Stored interaction in vector DB (domain: {current_domain})")
                        # Track embedding creation
                        embeddings_created = 2  # User + assistant message
                    except Exception as store_error:
                        logger.warning(f"Could not store in vector DB: {store_error}")
                        embeddings_created = 0
                else:
                    embeddings_created = 0
                
                # Update AI stats (estimate tokens based on content length)
                input_text = str(last_user_message) + str(profile_dict)
                estimated_input_tokens = len(input_text.split()) * 1.3  # Rough estimate
                output_text = str(ai_response.get('content', ''))
                estimated_output_tokens = len(output_text.split()) * 1.3
                
                response_type = 'visualization' if ai_response.get('is_visualizable') else 'text'
                
                update_ai_stats(
                    response_type=response_type,
                    input_tokens=int(estimated_input_tokens),
                    output_tokens=int(estimated_output_tokens),
                    response_time=time.time() - start_time if 'start_time' in locals() else 0,
                    embeddings_created=embeddings_created
                )
                
                # Add RAG context indicator to response
                if rag_context_used:
                    ai_response['_rag_context_used'] = True
                    ai_response['_rag_context_preview'] = rag_context_preview
                
                return ai_response

            except ValueError as ve:
                logger.error(f"Validation error: {str(ve)}")
                return {
                    "response_type": "error",
                    "content": "The request could not be processed. Please try rephrasing your question.",
                    "reasoning": f"Technical error: {str(ve)}",
                    "is_visualizable": False,
                    "suggested_actions": ["Rephrase question", "Try a simpler query"]
                }

            except genai.types.generation_types.BlockedPromptException as bpe:
                logger.error(f"Content blocked: {str(bpe)}")
                return {
                    "response_type": "error",
                    "content": "I cannot process that type of request. Please try a different question.",
                    "reasoning": "Content policy violation detected",
                    "is_visualizable": False,
                    "suggested_actions": ["Ask a different question", "Review content guidelines"]
                }

            except Exception as api_error:
                error_str = str(api_error).lower()
                
                # Handle API quota/rate limit errors gracefully
                if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                    available_models = ["gemini-2.5-flash", "gemini-2.5-flash-8b"]
                    current_model = client.current_model_name
                    
                    # Suggest alternative models
                    alternative_models = [m for m in available_models if m != current_model]
                    model_suggestions = f" Try switching to: {', '.join(alternative_models)}" if alternative_models else ""
                    
                    return {
                        "response_type": "error",
                        "content": f"⚠️ **API Quota Exceeded for {current_model}**\n\nThe free tier limit has been reached for this model.{model_suggestions}\n\n**What you can do:**\n- Wait a few minutes and try again\n- Switch to a different Gemini model in the sidebar\n- Your data and conversation are safe!",
                        "reasoning": f"API returned 429/quota error: {str(api_error)}",
                        "is_visualizable": False,
                        "suggested_actions": ["Switch model", "Wait and retry", "Try simpler query"]
                    }
                
                elif "rate" in error_str or "limit" in error_str:
                    return {
                        "response_type": "error",
                        "content": "⏱️ **Rate Limit Reached**\n\nWe're sending requests too quickly. The system will automatically retry in a moment.",
                        "reasoning": f"Rate limiting detected: {str(api_error)}",
                        "is_visualizable": False,
                        "suggested_actions": ["Wait a moment", "Try again"]
                    }
                
                elif "permission" in error_str or "unauthorized" in error_str or "api_key" in error_str:
                    return {
                        "response_type": "error",
                        "content": "🔑 **Authentication Issue**\n\nThere's a problem with the API key. Please contact the administrator.",
                        "reasoning": f"API authentication error: {str(api_error)}",
                        "is_visualizable": False,
                        "suggested_actions": ["Contact support", "Check API key"]
                    }

                logger.error(f"Gemini API error: {str(api_error)}")
                return {
                    "response_type": "error",
                    "content": "❌ **Unexpected Error**\n\nSomething went wrong while processing your request. Please try again.",
                    "reasoning": f"API error: {str(api_error)}",
                    "is_visualizable": False,
                    "suggested_actions": ["Try again", "Rephrase question", "Contact support"]
                }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "response_type": "error",
            "content": "I encountered an unexpected issue while analyzing your data.",
            "is_visualizable": False,
            "suggested_actions": ["Try again", "Ask a different question"]
        }
