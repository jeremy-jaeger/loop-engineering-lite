"""Think → act → simulate → commit only after a passing verification command."""
import json

from llm_client import call_ollama
from memory import export_trajectory_jsonl, reflect_on_trace
from tools import execute_tool
from vfs import VirtualFileSystem

UNVERIFIED_COMPLETE_MSG = (
    "Error: status 'complete' is not allowed until the last run_command is a "
    "passing verification command (python3 -m pytest or python3 -m unittest) "
    "that returned [SIMULATION VERIFIED SUCCESS]. Keep working."
)
MISSING_ANSWER_MSG = (
    "Error: the task is verified but you omitted 'final_answer'. "
    "Set status to 'complete' and include a non-empty final_answer."
)
INFERENCE_ERROR_MSG = (
    "Error: the previous model response was invalid JSON or inference failed. "
    "Respond again with a single valid JSON object and continue the task."
)
NO_TOOL_MSG = (
    "Error: Status is 'in_progress' but no 'tool_call' object was provided. "
    "Specify a valid tool."
)


def truncate_text(text, max_chars=3000):
    """Keep head and tail when an observation would blow a small context window."""
    text = str(text)
    if len(text) > max_chars:
        half = max_chars // 2
        return (
            text[:half]
            + "\n\n...[TRUNCATED BY HARNESS TO SAVE MEMORY]...\n\n"
            + text[-half:]
        )
    return text


def last_observation_verified(messages):
    if not messages:
        return False
    return "[SIMULATION VERIFIED SUCCESS]" in str(messages[-1].get("content", ""))


def _nudge_for_observation(observation):
    """Steer local models out of failure loops we have actually seen."""
    if "`old_code` block not found" in observation:
        return (
            "\n\n[SYSTEM NOTE: Stop retrying search_and_replace. "
            "Call read_file on that path, then write_file with the full corrected file.]"
        )
    if "[SIMULATION FAILED]" not in observation:
        return ""
    extra = (
        "\n\n[SYSTEM NOTE: Tests failed. Read the failing file(s), fix the "
        "implementation or missing imports with write_file, then re-run pytest.]"
    )
    lower = observation.lower()
    if (
        "no tests ran" in lower
        or "collected 0 items" in lower
        or "no tests collected" in lower
    ):
        extra += (
            " Pytest collected zero tests — rewrite test_*.py using "
            "`def test_...():` functions with asserts inside, not bare asserts "
            "and not tests that only run under `if __name__ == '__main__'`."
        )
    return extra


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
        reflect_on_trace(messages, initial_prompt)
    return final_ans


def run_agent_loop(
    initial_prompt,
    max_iterations=10,
    max_memory_items=8,
    workspace=".",
    call_model=None,
    enable_reflection=True,
):
    print(f"\n[START] Agent initialized with prompt:\n> {initial_prompt}\n")
    call_model = call_model or call_ollama

    vfs = VirtualFileSystem(base_dir=workspace)
    print("[WORLD MODEL] Virtual File System loaded. Reality is sandboxed.\n")

    messages = [{"role": "user", "content": initial_prompt}]

    for i in range(max_iterations):
        print(f"--- Iteration {i + 1} ---")

        if len(messages) > max_memory_items:
            print(
                f"[HARNESS INTERVENTION] Memory reached {len(messages)} items. "
                "Compacting context..."
            )
            original_prompt = messages[0]
            recent_context = messages[-4:]
            messages = [
                original_prompt,
                {
                    "role": "user",
                    "content": (
                        "[SYSTEM NOTE: Intermediate execution steps were purged "
                        "from memory to save context space. Continue based on "
                        "recent observations.]"
                    ),
                },
            ] + recent_context

        response = call_model(messages)
        if not isinstance(response, dict):
            response = {
                "thought_process": "Model returned a non-object payload.",
                "status": "in_progress",
                "_inference_error": True,
            }

        reasoning = response.get("thought_process", "No reasoning provided.")
        print(f"[REASONING]\n{reasoning}\n")

        if response.get("_inference_error"):
            print("[HARNESS INTERVENTION] Inference error — retry without committing.")
            messages.append({"role": "user", "content": INFERENCE_ERROR_MSG})
            continue

        if response.get("status") == "complete":
            final_ans = response.get("final_answer")
            verified = vfs.is_task_verified()

            if not verified:
                print("[HARNESS INTERVENTION] Refusing unverified completion.")
                messages.append({"role": "user", "content": UNVERIFIED_COMPLETE_MSG})
                continue

            if not final_ans:
                if last_observation_verified(messages):
                    final_ans = "Task successfully completed and verified by VFS."
                else:
                    print("[HARNESS INTERVENTION] Verified, but final_answer missing.")
                    messages.append({"role": "user", "content": MISSING_ANSWER_MSG})
                    continue

            print(f"[SUCCESS - TASK COMPLETE]\nFinal Answer: {final_ans}\n")
            finished = _finish_verified(
                messages, initial_prompt, vfs, final_ans, enable_reflection
            )
            if finished is not None:
                return finished
            messages.append({"role": "user", "content": UNVERIFIED_COMPLETE_MSG})
            continue

        if response.get("tool_call"):
            tool_call = response["tool_call"]
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            print(f"[ACTION] Calling tool '{tool_name}' with args: {tool_args}")
            observation = execute_tool(vfs, tool_name, tool_args)
            safe_observation = truncate_text(observation)
            if len(observation) != len(safe_observation):
                print(
                    "[HARNESS INTERVENTION] Truncated massive observation from "
                    f"{len(observation)} to {len(safe_observation)} characters."
                )

            print(f"[OBSERVATION]\n{safe_observation}\n")
            messages.append({"role": "assistant", "content": json.dumps(response)})
            observation_msg = f"Observation from {tool_name}: {safe_observation}"
            observation_msg += _nudge_for_observation(safe_observation)
            messages.append({"role": "user", "content": observation_msg})
        else:
            print("[HARNESS INTERVENTION] No tool call specified while in progress.")
            messages.append({"role": "user", "content": NO_TOOL_MSG})

    print("\n[ABORT] Maximum iterations reached without verified task completion.")
    _export_rejected(messages, initial_prompt, vfs)
    return None
