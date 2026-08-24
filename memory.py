"""Heuristics in knowledge.json and reward-labeled trajectory export."""
import json
import os
import urllib.request

KNOWLEDGE_FILE = "knowledge.json"
DATASET_FILE = "dataset.jsonl"
REJECTED_FILE = os.path.join("data", "rejected.jsonl")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:0.8b")


def load_knowledge():
    if not os.path.exists(KNOWLEDGE_FILE):
        return ""
    try:
        with open(KNOWLEDGE_FILE, encoding="utf-8") as f:
            knowledge = json.load(f)
        if not knowledge:
            return ""
        rules = "\n".join([f"- {k['lesson']}" for k in knowledge])
        return f"\n\nCRITICAL PAST LEARNINGS:\n{rules}\n"
    except Exception as exc:
        print(f"[MEMORY ERROR] Could not load knowledge: {exc}")
        return ""


def save_knowledge(task, lesson):
    knowledge = []
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE, encoding="utf-8") as f:
                knowledge = json.load(f)
        except Exception:
            pass
    knowledge.append({"task": task, "lesson": lesson})
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, indent=4)
        f.write("\n")
    print(f"[MEMORY SAVED] New heuristic committed to {KNOWLEDGE_FILE}.")


def export_trajectory_jsonl(messages, reward=1.0, task="", verified_command=None, path=None):
    """
    Serialize a trace with an explicit binary reward.
    reward 1.0 -> dataset.jsonl (verified / chosen)
    reward 0.0 -> data/rejected.jsonl (unverified / rejected)
    """
    try:
        reward = 1.0 if float(reward) == 1.0 else 0.0
        dest = path
        if dest is None:
            dest = DATASET_FILE if reward == 1.0 else REJECTED_FILE
        parent = os.path.dirname(dest)
        if parent:
            os.makedirs(parent, exist_ok=True)
        trajectory = {
            "messages": messages,
            "reward": reward,
            "task": task,
            "verified_command": verified_command,
        }
        with open(dest, "a", encoding="utf-8") as f:
            f.write(json.dumps(trajectory) + "\n")
        label = "chosen / verified" if reward == 1.0 else "rejected / unverified"
        print(f"[DATASET EXPORT] {label} trajectory saved to {dest} (reward={reward}).")
    except Exception as exc:
        print(f"[DATASET ERROR] Could not export trajectory: {exc}")


def reflect_on_trace(messages, original_prompt, model=None):
    print("\n[REFLECTION PASS] Analyzing execution trace for capability growth...")
    model = model or DEFAULT_MODEL
    trace_summary = []
    for msg in messages:
        if msg["role"] == "assistant" and "tool_call" in msg["content"]:
            trace_summary.append(f"Agent Action: {msg['content']}")
        elif msg["role"] == "user" and "Observation" in msg["content"]:
            trace_summary.append(f"Environment: {msg['content']}")
    compressed_trace = "\n".join(trace_summary[-10:])
    reflection_prompt = (
        f"You are an AI architect analyzing an agent's execution trace. "
        f"The original task was: {original_prompt}\n\n"
        f"Here is the execution trace:\n{compressed_trace}\n\n"
        f"If the agent made mistakes but eventually succeeded, identify the core "
        f"architectural mistake and the fix. Write a 1-to-2 sentence generalized "
        f"rule so the agent NEVER makes this mistake again. "
        f"If the agent performed perfectly on the first try, reply exactly with: 'NO_NEW_RULE'."
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": reflection_prompt}],
        "stream": False,
        "options": {"temperature": 0.3},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            lesson = result.get("message", {}).get("content", "").strip()
            if "NO_NEW_RULE" not in lesson:
                print(f"\n[LESSON LEARNED]\n{lesson}")
                save_knowledge(original_prompt, lesson)
            else:
                print("\n[REFLECTION] Perfect execution. No new heuristics required.")
    except Exception as exc:
        print(f"[REFLECTION ERROR] Failed to generate reflection: {exc}")
