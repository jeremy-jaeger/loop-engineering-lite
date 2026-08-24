"""Ollama chat client with a strict JSON response schema."""
import json
import os
import urllib.error
import urllib.request

from memory import load_knowledge

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:0.8b")

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "thought_process": {
            "type": "string",
            "description": "Your step-by-step reasoning for what to do next.",
        },
        "tool_call": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "args": {"type": "object"},
            },
            "description": "Include this only if you need to use a tool.",
        },
        "status": {
            "type": "string",
            "enum": ["in_progress", "complete"],
        },
        "final_answer": {"type": "string"},
    },
    "required": ["thought_process", "status"],
}

SYSTEM_PROMPT = (
    "You are an autonomous AI coding assistant running entirely locally. "
    "You have access to the following tools:\n"
    "1. list_files(directory: string)\n"
    "2. read_file(filepath: string)\n"
    "3. write_file(filepath: string, content: string)\n"
    "4. search_and_replace(filepath: string, old_code: string, new_code: string)\n"
    "5. run_command(command: string)\n\n"
    "CRITICAL INSTRUCTIONS:\n"
    "- You MUST respond with a single, valid JSON object. No Markdown, no conversational text.\n"
    "- Your JSON MUST contain these exact keys: 'thought_process' (string), "
    "'status' (string), and 'tool_call' (object) when a tool is needed.\n"
    "- Set 'status' to 'in_progress' when using a tool.\n"
    "- Set 'status' to 'complete' ONLY after a passing verification command "
    "(`python3 -m pytest` or `python3 -m unittest`) returned [SIMULATION VERIFIED SUCCESS].\n"
    "- The 'tool_call' object MUST contain 'name' (string) and 'args' (object).\n"
    "- ENVIRONMENT GROUNDING: Prefer `python3` and `python3 -m pytest`. "
    "Do not use `python`, `pip`, or `apt` unless the user explicitly asks."
)


def inference_error(reason):
    return {
        "thought_process": f"Inference failed: {reason}",
        "status": "in_progress",
        "tool_call": None,
        "final_answer": None,
        "_inference_error": True,
    }


def call_ollama(messages, model=None):
    model = model or DEFAULT_MODEL
    past_learnings = load_knowledge()
    system_prompt = {
        "role": "system",
        "content": SYSTEM_PROMPT + past_learnings,
    }
    payload = {
        "model": model,
        "messages": [system_prompt] + messages,
        "stream": False,
        "format": RESPONSE_SCHEMA,
        "options": {"temperature": 0.0},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            message_content = result.get("message", {}).get("content", "{}")
            parsed = json.loads(message_content)
            if not isinstance(parsed, dict):
                return inference_error("model returned a non-object JSON payload")
            return parsed
    except Exception as exc:
        print(f"\n[ERROR] Inference failed: {exc}")
        return inference_error(str(exc))
