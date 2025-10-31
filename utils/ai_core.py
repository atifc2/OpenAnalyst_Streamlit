import ollama
import json

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
        # Remove opening ```json or ```
        lines = cleaned.split('\n')
        if lines[0].strip().lower() in ['```json', '```']:
            lines = lines[1:]
        # Remove closing ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        cleaned = '\n'.join(lines).strip()
    
    # Handle single backticks
    cleaned = cleaned.strip('`').strip()
    
    # Remove "json" prefix if present
    if cleaned.lower().startswith('json'):
        cleaned = cleaned[4:].strip()
    
    return cleaned

def get_ai_response(data_profile, chat_history, model="llama3:latest"):
    """
    Generates a structured AI response using Ollama.
    Returns a dict with response_type, content, is_visualizable, and suggested_actions.
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

        # Format chat history
        formatted_history = _format_history_for_ai(chat_history)

        # Build messages array
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the profile for the current dataset:\n{data_profile}"}
        ]
        messages.extend(formatted_history[-4:])  # Last 4 messages for context

        # Make API call to Ollama
        try:
            response = ollama.chat(model=model, messages=messages, format="json")
        except Exception as api_error:
            error_str = str(api_error).lower()
            
            if "connection refused" in error_str or "connect" in error_str:
                return {
                    "response_type": "error",
                    "content": "I'm having trouble connecting to the AI service. This usually resolves itself in a moment.",
                    "is_visualizable": False,
                    "suggested_actions": ["Try again in a moment", "Ask a different question"]
                }
            elif "not found" in error_str or "model" in error_str:
                return {
                    "response_type": "error",
                    "content": "The AI model is currently unavailable. Please try again shortly.",
                    "is_visualizable": False,
                    "suggested_actions": ["Try again", "Upload a different file"]
                }
            else:
                return {
                    "response_type": "error",
                    "content": "I encountered an unexpected issue. Please try rephrasing your question.",
                    "is_visualizable": False,
                    "suggested_actions": ["Try a different question", "Rephrase your request"]
                }

        # Extract and parse response
        message_content = response.get("message", {}).get("content")
        
        if not message_content:
            return {
                "response_type": "error",
                "content": "I couldn't generate a response. Please try asking in a different way.",
                "is_visualizable": False,
                "suggested_actions": ["Rephrase your question", "Try a simpler query"]
            }

        # If already a dict, return it
        if isinstance(message_content, dict):
            return message_content

        # Parse JSON string
        if isinstance(message_content, str):
            try:
                cleaned_content = _clean_json_response(message_content)
                return json.loads(cleaned_content)
            except json.JSONDecodeError:
                return {
                    "response_type": "error",
                    "content": "I had trouble understanding the data. Could you try asking your question differently?",
                    "is_visualizable": False,
                    "suggested_actions": ["Ask in a different way", "Try a more specific question"]
                }

        return {
            "response_type": "error",
            "content": "Something unexpected happened. Please try your question again.",
            "is_visualizable": False,
            "suggested_actions": ["Try again", "Ask a different question"]
        }

    except Exception as e:
        return {
            "response_type": "error",
            "content": "I encountered an unexpected issue while analyzing your data.",
            "is_visualizable": False,
            "suggested_actions": ["Try again", "Ask a different question"]
        }