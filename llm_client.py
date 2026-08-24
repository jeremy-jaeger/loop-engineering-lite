import json
from pyexpat.errors import messages
import urllib.request
import urllib.error
from xml.parsers.expat import model
from memory import load_knowledge

OLLAMA_URL = "http://localhost:11434/api/chat"

# The expanded JSON Schema
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "thought_process": {
            "type": "string",
            "description": "Your step-by-step reasoning for what to do next."
        },
        "tool_call": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "args": {"type": "object"}
            },
            "description": "Include this only if you need to use a tool."
        },
        "status": {
            "type": "string",
            "enum": ["in_progress", "complete"]
        },
        "final_answer": {
            "type": "string"
        }
    },
    "required": ["thought_process", "status"]
}

def call_ollama(messages, model="qwen3.5:0.8b"):
    
    # Load past learnings dynamically
    past_learnings = load_knowledge()
    
    system_prompt = {
        "role": "system",
        "content": (
            "You are an autonomous AI coding assistant running entirely locally. "
            "You have access to the following tools:\n"
            "1. list_files(directory: string)\n"
            "2. read_file(filepath: string)\n"
            "3. write_file(filepath: string, content: string)\n"
            "4. search_and_replace(filepath: string, old_code: string, new_code: string)\n"
            "5. run_command(command: string)\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "- You MUST respond with a single, valid JSON object. No Markdown, no conversational text.\n"
            "- Your JSON MUST contain these exact keys: 'thought_process' (string), 'status' (string), and 'tool_call' (object).\n"
            "- Set 'status' to 'in_progress' when using a tool.\n"
            "- Set 'status' to 'complete' ONLY when the task is verified.\n"
            "- The 'tool_call' object MUST contain 'name' (string) and 'args' (object of key-value pairs).\n"
            "- ENVIRONMENT GROUNDING: You are running on macOS. You MUST use `python3` and `python3 -m pytest`. NEVER use `python`, `pip`, or `apt`."
            f"{past_learnings}"
        )
    }
    
    full_messages = [system_prompt] + messages

    payload = {
        "model": model,
        "messages": full_messages,
        "stream": False,
        "format": RESPONSE_SCHEMA, 
        "options": {
            "temperature": 0.0 
        }
    }

    req = urllib.request.Request(
        OLLAMA_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            message_content = result.get('message', {}).get('content', '{}')
            return json.loads(message_content)
            
    except Exception as e:
        print(f"\n[ERROR] Inference failed: {e}")
        return {"status": "complete", "final_answer": "Execution failed."}