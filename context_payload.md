[SYSTEM CONTEXT PAYLOAD: INITIALIZE STATE]
Please ingest this project context and act as my expert AI architect and co-developer. 

# PROJECT OVERVIEW
We are building a Lightweight Local AI Agentic Loop in Python, running natively on macOS (Apple Silicon). It uses zero bloated frameworks, relying on `ollama` for local inference and a custom Virtual File System (VFS) as a compositional world model. The goal is verifiable code generation and recursive self-improvement via Direct Preference Optimization (DPO) and Apple MLX fine-tuning.

# ARCHITECTURE & CODEBASE STATE
- `vfs.py`: The World Model. Creates a sandboxed `tempfile` universe to simulate edits and run commands. Only commits to the real hard drive (`commit_to_reality`) upon `[SIMULATION VERIFIED SUCCESS]` (exit code 0).
- `tools.py`: Adapters (`list_files`, `read_file`, `write_file`, `search_and_replace`, `run_command`) that interact strictly with the VFS memory dictionary, keeping the host system safe.
- `loop.py`: The runtime engine. Manages N-iterations, compacts context when memory gets too large, and uses a "Forgiving Finish Line" to handle edge cases when the LLM successfully completes a task but omits final JSON summaries.
- `memory.py`: Handles continuous learning. Extracts prompt-based heuristics into `knowledge.json`, and exports ShareGPT-formatted JSONL trajectories (`export_trajectory_jsonl`) of verified successes for MLX fine-tuning.
- `llm_client.py`: Calls local Ollama models (currently targeting sub-2B models like `qwen3.5:0.8b` for high-speed swarm execution). The system prompt enforces strict structural JSON output and includes environment grounding ("macOS only, use python3, no apt").
- `generate_dataset.sh`: A bash automation script that feeds TDD tasks into the loop to autonomously generate verified execution traces for `data/train.jsonl`.

- `architecture.md`: A pathway of developments continually updated.
- `goal.md`: A final goal clearly and specifically stated

# CORE DESIGN PILLARS (from GOAL.md)
1. Composable World-Model Core (VFS Sandbox).
2. Verification and Safety (Binary reward signals).
3. Self-Improvement Loop (Offline RL updates via Apple MLX).
4. Lightweight Swarm Composability (Run dozens of tiny sub-2B micro-agents in parallel without macOS memory swap death spirals).

# CURRENT STATUS
The pipeline is fully functional. The sub-2B model is successfully running TDD loops, diagnosing its own missing dependencies (like pytest), passing tests in the VFS, committing to reality, and exporting its trajectory to our dataset. 

Acknowledge that you have ingested this context. Ask me what we are building next.