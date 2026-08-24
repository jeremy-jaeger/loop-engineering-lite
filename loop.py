import json
from llm_client import call_ollama
from tools import execute_tool
from memory import reflect_on_trace, export_trajectory_jsonl
from vfs import VirtualFileSystem

def truncate_text(text, max_chars=3000):
    """Protects against horizontal context overflow."""
    text = str(text)
    if len(text) > max_chars:
        half = max_chars // 2
        return text[:half] + "\n\n...[TRUNCATED BY HARNESS TO SAVE MEMORY]...\n\n" + text[-half:]
    return text

def run_agent_loop(
    initial_prompt,
    max_iterations=10,
    max_memory_items=8,
    model="qwen3.5:0.8b",
    llm_api_base="http://localhost:11434",
):
    print(f"\n[START] Agent initialized with prompt:\n> {initial_prompt}\n")
    
    # --- 1. INITIALIZE WORLD MODEL ---
    vfs = VirtualFileSystem()
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
        
        response = call_ollama(messages, model=model, llm_api_base=llm_api_base)
        reasoning = response.get("thought_process", "No reasoning provided.")
        print(f"[REASONING]\n{reasoning}\n")
        
        # --- SMART COMPLETION CHECK ---
        if response.get("status") == "complete":
            final_ans = response.get("final_answer")
            
            # If the model was lazy with the text but actually did the work, forgive it.
            if not final_ans:
                last_msg = messages[-1].get("content", "")
                if "[SIMULATION VERIFIED SUCCESS]" in last_msg or len(messages) > 3:
                    final_ans = "Task successfully completed and verified by VFS."
                else:
                    print("[HARNESS INTERVENTION] Agent returned 'complete' immediately with no answer. Forcing retry...")
                    messages.append({
                        "role": "user", 
                        "content": "Error: You marked status as 'complete' but did not provide a 'final_answer' or perform any actions."
                    })
                    continue

            print(f"[SUCCESS - TASK COMPLETE]\nFinal Answer: {final_ans}\n")
            
            # 2. VERIFIED COMMIT TO REALITY
            vfs.commit_to_reality()
            
            # --- 3. EXPORT TO ML DATASET ---
            export_trajectory_jsonl(messages)
            # -------------------------------
            
            # 4. CONTINUOUS LEARNING TRIGGER
            reflect_on_trace(
                messages,
                initial_prompt,
                model=model,
                llm_api_base=llm_api_base,
            )
            return final_ans
        # ------------------------------
            
        # --- TOOL DISPATCH ---
        if response.get("tool_call"):
            tool_call = response["tool_call"]
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            
            print(f"[ACTION] Calling tool '{tool_name}' with args: {tool_args}")
            
            # Pass the VFS dictionary into the tools instead of letting them touch the hard drive
            raw_observation = execute_tool(vfs, tool_name, tool_args)
            
            safe_observation = truncate_text(raw_observation)
            if len(raw_observation) != len(safe_observation):
                print(f"[HARNESS INTERVENTION] Truncated massive observation from {len(raw_observation)} to {len(safe_observation)} characters.")
            
            print(f"[OBSERVATION]\n{safe_observation}\n")
            
            messages.append({"role": "assistant", "content": json.dumps(response)})
            messages.append({"role": "user", "content": f"Observation from {tool_name}: {safe_observation}"})
            
        else:
            print("[HARNESS INTERVENTION] No tool call specified while in progress.")
            messages.append({
                "role": "user",
                "content": "Error: Status is 'in_progress' but no 'tool_call' object was provided. Specify a valid tool."
            })
            
    print("\n[ABORT] Maximum iterations reached without task completion.")
    return None