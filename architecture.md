# Architecture Log

This document tracks the major architectural decisions and evolution of the lightweight local agent harness.

---

## ADR-001: Implement Self-Correction Loop for Tool Enforcement

**Date:** 2026-08-23
**Status:** Accepted

### 1. Context
During early testing with the local `qwen2.5` model, the agent successfully reasoned about which tool to use (e.g., using a bash command to create a file) but failed to actually execute the tool. It bypassed the JSON `tool_call` object, immediately set its `status` to `complete`, and returned `None` as the final answer. This caused the ReAct loop to exit prematurely without accomplishing the user's task.

### 2. Decision
We decided to enforce tool execution at both the prompt level and the engine level:
*   **System Prompt Upgrade:** We added a "CRITICAL INSTRUCTIONS" block to `llm_client.py`, explicitly forbidding the model from describing actions without invoking tools, and strictly defining the difference between `in_progress` and `complete`.
*   **Harness Intervention:** We updated the core execution engine (`loop.py`) to include a programmatic self-correction check. If the model attempts to exit with `status: complete` but leaves the `final_answer` empty, the harness intercepts the exit, injects an error message into the model's memory, and forces it to retry.

### 3. Consequences
*   **Positive:** The agent is now highly resilient to "lazy completions" and is algorithmically forced to use tools to generate artifacts. It turns human frustration into an automatic programmatic feedback loop.
*   **Negative:** If the model hallucinates or gets genuinely stuck, it will bounce against the error handler until the `max_iterations` cap is reached, slightly increasing compute time on outright failures.

## ADR-002: Implement Path-Jailing and Dedicated File Creation

**Date:** 2026-08-23
**Status:** Accepted

### 1. Context
The agent previously lacked a native file creation tool, leading it to attempt shell workarounds (e.g., `echo > file`). Furthermore, granting an autonomous agent read/write access to the host file system introduces severe security risks if the model hallucinates paths outside the intended workspace (e.g., overwriting system configurations).

### 2. Decision
*   **Dedicated Tool:** Introduced `write_file(filepath, content)` to cleanly handle file generation and automatic directory creation.
*   **Path-Jailing (Sandbox):** Implemented an `is_safe_path()` guardrail function in `tools.py`. Using `os.path.abspath`, it verifies that all file operations (`read`, `write`, `replace`, `list`) resolve to a path strictly within the current working directory.
*   **Process Confinement:** Forced the `subprocess.run` command in `run_command` to default to `cwd='.'`.

### 3. Consequences
*   **Positive:** The agent can now securely scaffold out multi-file projects (like React components or Python modules). The host machine is protected from path-traversal hallucinations.
*   **Negative:** The agent cannot be used for system-wide configuration tasks (like editing shell profiles in `~/.zshrc`) unless explicitly launched from those directories.

## ADR-003: Implement Sliding-Window Memory and Horizontal Truncation

**Date:** 2026-08-23
**Status:** Accepted

### 1. Context
As the agent engages in extended multi-step tasks (like scaffolding projects or debugging code), the `messages` array grows continuously. This leads to two critical failure modes:
1. **Vertical Overflow:** The model gets "lost in the middle," forgetting the initial user prompt as context grows.
2. **Horizontal Overflow:** Tools like `read_file` or `run_command` returning massive text blobs instantly exceed the LLM's context window, causing inference crashes.

### 2. Decision
*   **Horizontal Defense (Truncation):** Implemented a `truncate_text()` function that intercepts any string exceeding 3,000 characters. It splices the first half and last half, dropping the middle. For code/terminal outputs, errors usually live at the end and setup lives at the beginning, making this heuristic effective.
*   **Vertical Defense (Sliding Window):** Modified the main execution cycle in `loop.py` to monitor the length of the `messages` array. Once `max_memory_items` (default 8) is reached, it purges intermediate reasoning steps while preserving the original user prompt, an injected system note regarding the purge, and the most recent 4 steps.

### 3. Consequences
*   **Positive:** The agent can now theoretically run infinitely without blowing up the local context window limit. Heavy file reads no longer crash the process.
*   **Negative:** The agent loses historical context of tools it tried 5+ steps ago, potentially leading to repetitive behavior if it gets stuck on a persistent bug.

## ADR-004: Implementation of Trajectory Abstraction (Experience Replay)

**Date:** 2026-08-23
**Status:** Proposed

### 1. Context
While the agent successfully performs autonomous Self-Healing TDD, it suffers from terminal amnesia. Successful debugging trajectories are discarded upon process exit, meaning the runtime does not demonstrate verifiable capability growth over time. 

### 2. Decision
Implement a persistent Reflection Layer. Upon successful task completion, the loop will execute a secondary LLM call to synthesize the execution trace into a generalized "heuristic." This heuristic will be saved to a local `knowledge.json` file. Future instantiations of the agent will dynamically inject this knowledge base into the system prompt.

### 3. Consequences
*   **Positive:** The system transitions from a static inference loop to a self-improving runtime. It effectively "learns" environment constraints and edge cases without requiring weight fine-tuning.
*   **Negative:** The system prompt will grow over time as more rules are learned, requiring a future vector-search implementation (RAG) to only inject *relevant* rules to prevent context bloat.
## ADR-005: Trajectory Serialization for Supervised Fine-Tuning (SFT)

**Date:** 2026-08-23
**Status:** Proposed Pipeline

### 1. Context
The VFS integration (ADR-004) successfully filters hallucinated or buggy paths, ensuring that only verified execution traces (`Score: 1.0`) are committed to reality. However, relying purely on context-window injection for capability growth does not permanently alter the model's base distribution, leading to prompt bloat and static baseline intelligence.

### 2. Decision
*   **Dataset Generation:** Implement a trajectory exporter that serializes every successful VFS rollout into the standard ShareGPT JSONL format. 
*   **Apple MLX Pipeline:** Utilize the `mlx-lm` framework to perform localized Low-Rank Adaptation (LoRA) on the M-series unified memory architecture. 
*   **Hot-Swapping:** Fuse the trained adapters into a standard GGUF file format to be hot-swapped back into the local Ollama inference engine as an improved base checkpoint.

### 3. Consequences
*   **Positive:** The runtime achieves true, weight-based recursive self-improvement. The agent permanently learns the nuances of the JSON harness, reducing failed JSON decode errors and iteration loops over time.
*   **Negative:** Requires periodic offline computation time (training runs). The loop must be paused while the new checkpoint is being fused and loaded.