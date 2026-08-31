import json
import os
import urllib.request
import urllib.error

KNOWLEDGE_FILE = "knowledge.json"
DATASET_FILE = "dataset.jsonl"
REJECTED_FILE = os.path.join("data", "rejected.jsonl")
SEARCH_DPO_FILE = os.path.join("data", "search_dpo.jsonl")
SEARCH_DPO_FILE = SEARCH_DPO_FILE
DATASET_FILE = DATASET_FILE
REJECTED_FILE = REJECTED_FILE
OLLAMA_URL = "http://localhost:11434/api/chat"

def load_knowledge():
    if not os.path.exists(KNOWLEDGE_FILE):
        return ""
    try:
        with open(KNOWLEDGE_FILE, "r") as f:
            knowledge = json.load(f)
        if not knowledge: 
            return ""
        rules = "\n".join([f"- {k['lesson']}" for k in knowledge])
        return f"\n\nCRITICAL PAST LEARNINGS:\n{rules}\n"
    except Exception as e:
        print(f"[MEMORY ERROR] Could not load knowledge: {e}")
        return ""

def save_knowledge(task, lesson):
    knowledge = []
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE, "r") as f:
                knowledge = json.load(f)
        except Exception:
            pass
    
    knowledge.append({"task": task, "lesson": lesson})
    with open(KNOWLEDGE_FILE, "w") as f:
        json.dump(knowledge, f, indent=4)
    print(f"[MEMORY SAVED] New heuristic committed to {KNOWLEDGE_FILE}.")

def export_trajectory_jsonl(messages, reward=1.0, task="", verified_command=None, path=None):
    """
    Serialize an execution trace with an explicit binary reward.
    reward 1.0 -> dataset.jsonl (SFT / chosen)
    reward 0.0 -> data/rejected.jsonl (DPO rejected)
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

        with open(dest, 'a') as f:
            f.write(json.dumps(trajectory) + "\n")

        label = "chosen / verified" if reward == 1.0 else "rejected / unverified"
        print(f"[DATASET EXPORT] {label} trajectory saved to {dest} (reward={reward}).")
    except Exception as e:
        print(f"[DATASET ERROR] Could not export trajectory: {e}")

export_trajectory_jsonl = export_trajectory_jsonl
export_trajectory_jsonl = export_trajectory_jsonl


def reflect_on_trace(messages, original_prompt, model="qwen3.5:0.8b"):
    print("\n[REFLECTION PASS] Analyzing execution trace for capability growth...")
    
    trace_summary = []
    for m in messages:
        if m["role"] == "assistant" and "tool_call" in m["content"]:
            trace_summary.append(f"Agent Action: {m['content']}")
        elif m["role"] == "user" and "Observation" in m["content"]:
            trace_summary.append(f"Environment: {m['content']}")
            
    compressed_trace = "\n".join(trace_summary[-10:])
    
    reflection_prompt = (
        f"You are an AI architect analyzing an agent's execution trace. "
        f"The original task was: {original_prompt}\n\n"
        f"Here is the execution trace:\n{compressed_trace}\n\n"
        f"If the agent made mistakes but eventually succeeded, identify the core architectural mistake and the fix. "
        f"Write a 1-to-2 sentence generalized rule so the agent NEVER makes this mistake again. "
        f"If the agent performed perfectly on the first try, reply exactly with: 'NO_NEW_RULE'."
    )

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": reflection_prompt}],
        "stream": False,
        "options": {"temperature": 0.3}
    }
    
    req = urllib.request.Request(
        OLLAMA_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            lesson = result.get('message', {}).get('content', '').strip()
            
            if "NO_NEW_RULE" not in lesson:
                print(f"\n[LESSON LEARNED]\n{lesson}")
                save_knowledge(original_prompt, lesson)
            else:
                print("\n[REFLECTION] Perfect execution. No new heuristics required.")
    except Exception as e:
        print(f"[REFLECTION ERROR] Failed to generate reflection: {e}")


reflect_on_trace = reflect_on_trace
