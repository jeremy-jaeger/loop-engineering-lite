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
**Status:** Accepted (implemented in `memory.py` / `knowledge.json`; effectiveness not yet verified)

### 1. Context
While the agent successfully performs autonomous Self-Healing TDD, it suffers from terminal amnesia. Successful debugging trajectories are discarded upon process exit, meaning the runtime does not demonstrate verifiable capability growth over time. 

### 2. Decision
Implement a persistent Reflection Layer. Upon successful task completion, the loop will execute a secondary LLM call to synthesize the execution trace into a generalized "heuristic." This heuristic will be saved to a local `knowledge.json` file. Future instantiations of the agent will dynamically inject this knowledge base into the system prompt.

### 3. Consequences
*   **Positive:** The system transitions from a static inference loop to a self-improving runtime. It effectively "learns" environment constraints and edge cases without requiring weight fine-tuning.
*   **Negative:** The system prompt will grow over time as more rules are learned, requiring a future vector-search implementation (RAG) to only inject *relevant* rules to prevent context bloat.
## ADR-005: Trajectory Serialization for Supervised Fine-Tuning (SFT)

**Date:** 2026-08-23
**Status:** Implemented (2026-08-24) — reward-gated prepare, MLX LoRA train path, held-out eval, promote gate

### 1. Context
The VFS integration (ADR-004) successfully filters hallucinated or buggy paths, ensuring that only verified execution traces (`Score: 1.0`) are committed to reality. However, relying purely on context-window injection for capability growth does not permanently alter the model's base distribution, leading to prompt bloat and static baseline intelligence.

### 2. Decision
*   **Dataset Generation:** Implement a trajectory exporter that serializes every successful VFS rollout into the standard ShareGPT JSONL format. 
*   **Apple MLX Pipeline:** Utilize the `mlx-lm` framework to perform localized Low-Rank Adaptation (LoRA) on the M-series unified memory architecture. 
*   **Hot-Swapping:** Fuse the trained adapters into a standard GGUF file format to be hot-swapped back into the local Ollama inference engine as an improved base checkpoint.

**Implemented as `python3 -m improve {prepare,train,eval,promote}`:**
1. `prepare` keeps only `reward==1.0` traces that include a `verified_command` and a tool call. Same-task failures become DPO pairs (`data/mlx/dpo.jsonl`).
2. `train` runs `mlx_lm lora` + `fuse` on Apple Silicon. If MLX is absent it writes `adapters/train_spec.json` and **does not** pretend weights were updated. PEFT/CUDA is documented, not silently faked.
3. `eval` scores a held-out TDD suite (`clamp` / `unique` / `anagram`) whose success metric is VFS pytest/unittest — never self-graded `complete`.
4. `promote` writes `adapters/current.json` + `Modelfile` only when train status is a real adapter **and** held-out win_rate beats baseline by `PROMOTE_DELTA`. `llm_client` reads that file at inference.

### 3. Consequences
*   **Positive:** The runtime achieves true, weight-based recursive self-improvement. The agent permanently learns the nuances of the JSON harness, reducing failed JSON decode errors and iteration loops over time.
*   **Negative:** Requires periodic offline computation time (training runs). The loop must be paused while the new checkpoint is being fused and loaded. On machines without MLX, prepare still works; fuse/GGUF/Ollama create remains an operator step after `promote`.

---

## Current-state audit (2026-08-24)

What actually exists, versus what `goal.md` and `context_payload.md` claim:

| Pillar | Claimed | In the repo today |
|---|---|---|
| World-model core | Compositional latent/symbolic WM with rollouts | In-memory file dict + tempdir `subprocess` (`vfs.py`). No latents, no progress head, no counterfactual API. |
| Trajectory / self-improvement | Offline RL / DPO / MLX adapters | Reward-gated JSONL + DPO pairs + MLX/PEFT train plan + eval/promote gate (`improve/`). Weights update only on Apple Silicon / PEFT hosts; this environment writes a plan. |
| Harness | Drop-in adapters for other frameworks | Single Ollama JSON ReAct loop (`loop.py` + `main.py`). |
| Verification / safety | Sandbox + consistency + HITL + rollback | Tempdir sim for `run_command`. Commit/export/reflect gated on last passing pytest/unittest (ADR-006). |
| Benchmarks | Open long-horizon tasks with strict metrics | Held-out TDD suite in `improve/evaluate.py` (pytest/unittest only). `generate_dataset.sh` remains the train-set generator. |
| Swarm | Parallel isolated VFS micro-agents | Sequential single process. |

**Integrity bug (fixed by ADR-006):** the loop used to commit and export on model-declared `complete`, including via `len(messages) > 3`. That path is closed.

---

## ADR-006: Gate Reality and Learning on Binary Verification

**Date:** 2026-08-24
**Status:** Implemented (2026-08-24)

### 1. Context
`goal.md` states that verification is the crux of self-improvement: without a cheap, truthful signal that a trajectory improved capability, the rest of the flywheel is RAG-over-transcripts. The VFS already produces a binary score (`1.0` / `0.0`) per `simulate_command`, but the runtime does not treat that score as the commit/export/reflect gate. Until it does, ADR-004 heuristics and ADR-005 JSONL are not "verifiable capability growth."

### 2. Decision
Implement **verified-success gating** as a first-class loop invariant before any weight-training work:

1. **Do not `commit_to_reality` unless** the current VFS rollout has at least one `[SIMULATION VERIFIED SUCCESS]` **and** the last `run_command` (if any) did not fail. Prefer: last verification command is the task's test command (`python3 -m pytest …`) with score `1.0`.
2. **Do not `export_trajectory_jsonl` or `reflect_on_trace` on unverified completions.** Export a structured record: `{messages, reward, task, verified_command}` with `reward ∈ {0.0, 1.0}`.
3. **Narrow the forgiving finish line.** Empty `final_answer` may be filled in only when the last observation is verified success — never via `len(messages) > 3`.
4. **Commit only agent-touched paths**, not the entire `_load_substrate()` snapshot (avoids rewriting unrelated repo files).
5. **Capture rejected traces** (score `0.0` at max iterations or failed final tests) into a paired DPO/preference file (`data/rejected.jsonl`), so the next stage after this one can train DPO instead of SFT-on-successes-only.

Out of scope for this stage: MLX/LoRA, GGUF fusion, swarm spawning, framework adapters, latent world models.

### 3. Consequences
*   **Positive:** The dataset and `knowledge.json` become honest. Failed TDD runs stop polluting the host tree. ADR-005 (weight updates) and DPO become possible without poisoning the base model. This is the smallest change that makes the North Star's "verifiable" clause true.
*   **Negative:** Many current loop exits will correctly become `[ABORT]` instead of fake success, so `generate_dataset.sh` will look "worse" until the agent actually passes tests. That is the intended signal.

### 4. Stage sequence after ADR-006
1. **ADR-006:** verification gate + reward-labeled trajectories + DPO reject set + scoped commits.
2. **ADR-005:** offline adapter training + held-out eval + promote gate (implemented).
3. **ADR-007 (next):** verifier-guided test-time search over forked VFS states — the lite-model capability multiplier.
4. **Then:** parallel VFS swarm workers, then framework adapters.

---

## ADR-007: Verifier-Guided Test-Time Search (Next — top of lite-model loop engineering)

**Date:** 2026-08-24
**Status:** Accepted as next stage (not yet implemented)

### 1. Context
ADR-005 updates weights from verified traces. That mostly teaches a 0.8B–2B model the *harness* (JSON, pytest, TDD order). It does not buy much *solution search*. Sub-2B policies are weak one-shot TDD solvers; they become strong when a cheap, exact verifier scores many candidate rollouts — the same pattern as AlphaZero / Best-of-N / process-reward methods, except our world model is a copy-on-write file dict plus `python3 -m pytest` in a tempdir.

That is the distinctive engineering feat for *this* repo: not a bigger LoRA, not a generic swarm wrapper, but making the VFS a first-class search substrate at inference time.

### 2. Decision
Implement **Best-of-N (then MCTS-lite) over forked VFS states**:

1. **COW fork:** `VirtualFileSystem.fork()` copies `state`, `touched_paths`, and `command_history` without touching the host.
2. **Branch at action time:** when the policy emits a `write_file` / `search_and_replace` / `run_command`, sample K candidates (temperature > 0). Apply each on a fork.
3. **Score with the existing binary verifier:** run the task's test command via `simulate_command`. Keep argmax; discard losers.
4. **Online DPO:** export (winner, loser) pairs for the same task prefix into `data/rejected.jsonl` / chosen JSONL so ADR-005 trains on *search leftovers*, not just full-episode outcomes.
5. **Budget:** cap K and wall time so a swarm of 0.8B workers still fits in laptop RAM — search is the multiplier, not parameter count.

Out of scope here: latent video world models, multi-framework adapters.

### 3. Consequences
*   **Positive:** A 0.8B model can beat a larger one-shot model on harnessed TDD because the loop, not the weights, does the search. Combined with ADR-005, format is learned in weights and solutions are found at test time. This is the actual "loop engineering" product.
*   **Negative:** K rollouts multiply `simulate_command` cost. Requires a real `fork()` that does not leak forks into `commit_to_reality`.

### 4. Why this sits above swarm
Swarm (N isolated agents) is scale-out of the same one-shot policy. Test-time VFS search is scale-*in* intelligence per token. Do search first; then spawn many searchers.