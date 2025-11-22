import json
import os
import time
import logging
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from threading import Lock
from datetime import datetime, timedelta

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
    Handles: markdown code blocks, escaped quotes, leading/trailing whitespace.
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

        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.rate_limiter = RateLimiter(TOKEN_FILL_RATE)
        self._initialized = True

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


def get_ai_response(data_profile, chat_history, model=None):
    """
    Generates a structured AI response using Gemini API.
    """
    try:
        # Load system prompt
        try:
            with open("prompts/system_prompt.txt", "r") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            return {
                "response_type": "error",
                "content": "The AI assistant is temporarily unavailable. Please try again in a moment.",
                "is_visualizable": False,
                "suggested_actions": ["Try again", "Upload your data again"]
            }

        # Extract column information from data profile
        try:
            import json
            profile_data = json.loads(data_profile)
            available_columns = [col["name"] for col in profile_data.get("columns", [])]
        except:
            available_columns = []

        # Enhance system prompt with column information
        if available_columns:
            column_info = f"\n\n**AVAILABLE COLUMNS IN CURRENT DATASET:**\n{', '.join(available_columns)}\n\nIMPORTANT: Only use these exact column names in chart_data. Do not invent new columns."
            system_prompt += column_info

        # Format chat history
        formatted_history = _format_history_for_ai(chat_history)

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the profile for the current dataset:\n{data_profile}"}
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
                return json.loads(cleaned_content)

            except ValueError as ve:
                logger.error(f"Validation error: {str(ve)}")
                return {
                    "response_type": "error",
                    "content": "The request could not be processed. Please try rephrasing your question.",
                    "is_visualizable": False,
                    "suggested_actions": ["Rephrase question", "Try a simpler query"]
                }

            except genai.types.generation_types.BlockedPromptException as bpe:
                logger.error(f"Content blocked: {str(bpe)}")
                return {
                    "response_type": "error",
                    "content": "I cannot process that type of request. Please try a different question.",
                    "is_visualizable": False,
                    "suggested_actions": ["Ask a different question", "Review content guidelines"]
                }

            except Exception as api_error:
                error_str = str(api_error).lower()
                if "permission" in error_str or "unauthorized" in error_str:
                    return {
                        "response_type": "error",
                        "content": "There's an issue with the API authentication. Please check your API key.",
                        "is_visualizable": False,
                        "suggested_actions": ["Verify API key", "Contact support"]
                    }
                elif "quota" in error_str or "rate" in error_str:
                    return {
                        "response_type": "error",
                        "content": "We've hit the API rate limit. Please wait a moment before trying again.",
                        "is_visualizable": False,
                        "suggested_actions": ["Wait a moment", "Try later"]
                    }

                logger.error(f"Gemini API error: {str(api_error)}")
                return {
                    "response_type": "error",
                    "content": "An error occurred while processing your request. Please try again.",
                    "is_visualizable": False,
                    "suggested_actions": ["Try again", "Contact support"]
                }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "response_type": "error",
            "content": "I encountered an unexpected issue while analyzing your data.",
            "is_visualizable": False,
            "suggested_actions": ["Try again", "Ask a different question"]
        }


def get_ai_response(profile, history):
    """AI response using the centralized system prompt"""
    
    try:
        # Read the main system prompt from file
        with open("prompts/system_prompt.txt", "r") as f:
            base_system_prompt = f.read()
        
        # Add dynamic context to the existing prompt
        # FIX: Handle both string and dict profiles
        if isinstance(profile, dict):
            available_columns = profile.get("columns", [])
        else:
            # If profile is a string, try to parse it or use empty list
            try:
                import json
                profile_dict = json.loads(profile) if isinstance(profile, str) else {}
                available_columns = profile_dict.get("columns", [])
            except:
                available_columns = []
        
        # FIX: Ensure available_columns contains only strings
        if available_columns:
            # Convert any non-string items to strings
            available_columns = [str(col) if not isinstance(col, str) else col for col in available_columns]
        
        # Enhance the base prompt with current data context
        enhanced_prompt = base_system_prompt + f"""

**CURRENT DATA CONTEXT:**
Available columns: {', '.join(available_columns)}

Common derived columns available:
- total_sale (if quantity * price was calculated)
- month, year, month_name (if date columns exist)

Remember to validate column existence before creating charts.
"""
    
        # Format history for AI
        formatted_history = _format_history_for_ai(history)

        # Build messages
        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": f"Here is the profile for the current dataset:\n{json.dumps(profile)}"}
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
                return json.loads(cleaned_content)

            except ValueError as ve:
                logger.error(f"Validation error: {str(ve)}")
                return {
                    "response_type": "error",
                    "content": "The request could not be processed. Please try rephrasing your question.",
                    "is_visualizable": False,
                    "suggested_actions": ["Rephrase question", "Try a simpler query"]
                }

            except genai.types.generation_types.BlockedPromptException as bpe:
                logger.error(f"Content blocked: {str(bpe)}")
                return {
                    "response_type": "error",
                    "content": "I cannot process that type of request. Please try a different question.",
                    "is_visualizable": False,
                    "suggested_actions": ["Ask a different question", "Review content guidelines"]
                }

            except Exception as api_error:
                error_str = str(api_error).lower()
                if "permission" in error_str or "unauthorized" in error_str:
                    return {
                        "response_type": "error",
                        "content": "There's an issue with the API authentication. Please check your API key.",
                        "is_visualizable": False,
                        "suggested_actions": ["Verify API key", "Contact support"]
                    }
                elif "quota" in error_str or "rate" in error_str:
                    return {
                        "response_type": "error",
                        "content": "We've hit the API rate limit. Please wait a moment before trying again.",
                        "is_visualizable": False,
                        "suggested_actions": ["Wait a moment", "Try later"]
                    }

                logger.error(f"Gemini API error: {str(api_error)}")
                return {
                    "response_type": "error",
                    "content": "An error occurred while processing your request. Please try again.",
                    "is_visualizable": False,
                    "suggested_actions": ["Try again", "Contact support"]
                }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "response_type": "error",
            "content": "I encountered an unexpected issue while analyzing your data.",
            "is_visualizable": False,
            "suggested_actions": ["Try again", "Ask a different question"]
        }
