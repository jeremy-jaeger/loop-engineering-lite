import json
from llm_client import call_ollama
from tools import execute_tool
from memory import reflect_on_trace, export_trajectory_jsonl
from vfs import VirtualFileSystem, is_verification_command
from search import best_of_n, collect_candidates
from world_model import MUTATING_TOOLS

UNVERIFIED_COMPLETE_MSG = (
    "Error: status 'complete' is not allowed until the last run_command is a "
    "passing verification command (python3 -m pytest / unittest) that returned "
    "[SIMULATION VERIFIED SUCCESS]. Keep working."
)
MISSING_ANSWER_MSG = (
    "Error: the task is verified but you omitted 'final_answer'. "
    "Set status to 'complete' and include a non-empty final_answer."
)

def truncate_text(text, max_chars=3000):
    """Protects against horizontal context overflow."""
    text = str(text)
    if len(text) > max_chars:
        half = max_chars // 2
        return text[:half] + "\n\n...[TRUNCATED BY HARNESS TO SAVE MEMORY]...\n\n" + text[-half:]
    return text

def last_observation_verified(messages):
    if not messages:
        return False
    return "[SIMULATION VERIFIED SUCCESS]" in str(messages[-1].get("content", ""))


def infer_verify_command(vfs, explicit=None):
    if explicit:
        return explicit
    for item in reversed(vfs.command_history or []):
        if is_verification_command(item.get("command", "")):
            return item["command"]
    return None

def _export_rejected(messages, task, vfs):
    last = vfs.last_command() if vfs else None
    export_trajectory_jsonl(
        messages,
        reward=0.0,
        task=task,
        verified_command=last["command"] if last else None,
    )

def _finish_verified(messages, initial_prompt, vfs, final_ans, enable_reflection):
    committed = vfs.commit_to_reality()
    if not committed:
        return None
    export_trajectory_jsonl(
        messages,
        reward=1.0,
        task=initial_prompt,
        verified_command=vfs.verified_command(),
    )
    if enable_reflection:
        reflect_on_trace(messages, initial_prompt, model="qwen3.5:0.8b")
    return final_ans

def run_agent_loop(
    initial_prompt,
    max_iterations=10,
    max_memory_items=8,
    workspace=".",
    call_model=None,
    enable_reflection=True,
    search_width=1,
    verify_command=None,
):
    print(f"\n[START] Agent initialized with prompt:\n> {initial_prompt}\n")
    call_model = call_model or call_ollama

    # --- 1. INITIALIZE WORLD MODEL ---
    vfs = VirtualFileSystem(base_dir=workspace)
    print("[WORLD MODEL] Virtual File System loaded. Reality is sandboxed.\n")
    # ---------------------------------

    messages = [{"role": "user", "content": initial_prompt}]

    for i in range(max_iterations):
        print(f"--- Iteration {i+1} ---")

        # --- VERTICAL CONTEXT COMPACTION ---
        if len(messages) > max_memory_items:
            print(f"[HARNESS INTERVENTION] Memory reached {len(messages)} items. Compacting context...")
            original_prompt = messages[0]
            recent_context = messages[-4:]

            messages = [
                original_prompt,
                {"role": "user", "content": "[SYSTEM NOTE: Intermediate execution steps were purged from memory to save context space. Continue based on recent observations.]"}
            ] + recent_context
        # -----------------------------------

        response = call_model(messages)
        reasoning = response.get("thought_process", "No reasoning provided.")
        print(f"[REASONING]\n{reasoning}\n")

        # --- SMART COMPLETION CHECK ---
        if response.get("status") == "complete":
            final_ans = response.get("final_answer")
            verified = vfs.is_task_verified()

            if not verified:
                print("[HARNESS INTERVENTION] Refusing unverified completion. Forcing retry...")
                messages.append({"role": "user", "content": UNVERIFIED_COMPLETE_MSG})
                continue

            if not final_ans:
                if last_observation_verified(messages):
                    final_ans = "Task successfully completed and verified by VFS."
                else:
                    print("[HARNESS INTERVENTION] Verified, but final_answer missing. Forcing retry...")
                    messages.append({"role": "user", "content": MISSING_ANSWER_MSG})
                    continue

            print(f"[SUCCESS - TASK COMPLETE]\nFinal Answer: {final_ans}\n")
            finished = _finish_verified(messages, initial_prompt, vfs, final_ans, enable_reflection)
            if finished is not None:
                return finished
            messages.append({"role": "user", "content": UNVERIFIED_COMPLETE_MSG})
            continue
        # ------------------------------

        # --- TOOL DISPATCH ---
        if response.get("tool_call"):
            tool_call = response["tool_call"]
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            print(f"[ACTION] Calling tool '{tool_name}' with args: {tool_args}")

            observation = None
            if search_width > 1 and tool_name in MUTATING_TOOLS:
                candidates = collect_candidates(call_model, messages, response, search_width)
                if len(candidates) > 1:
                    chosen, observation, report = best_of_n(
                        vfs,
                        candidates,
                        verify_command=infer_verify_command(vfs, verify_command),
                        task=initial_prompt,
                    )
                    if chosen is not None:
                        response = chosen
                        tool_name = (chosen.get("tool_call") or {}).get("name") or tool_name
                        print(f"[SEARCH] considered {report.get('tried')} unique actions")

            if observation is None:
                observation = execute_tool(vfs, tool_name, tool_args)

            safe_observation = truncate_text(observation)
            if len(observation) != len(safe_observation):
                print(f"[HARNESS INTERVENTION] Truncated massive observation from {len(observation)} to {len(safe_observation)} characters.")

            print(f"[OBSERVATION]\n{safe_observation}\n")

            messages.append({"role": "assistant", "content": json.dumps(response)})
            messages.append({"role": "user", "content": f"Observation from {tool_name}: {safe_observation}"})

        else:
            print("[HARNESS INTERVENTION] No tool call specified while in progress.")
            messages.append({
                "role": "user",
                "content": "Error: Status is 'in_progress' but no 'tool_call' object was provided. Specify a valid tool."
            })

    print("\n[ABORT] Maximum iterations reached without verified task completion.")
    _export_rejected(messages, initial_prompt, vfs)
    return None


run_agent_loop = run_agent_loop
run_agent_loop = run_agent_loop
