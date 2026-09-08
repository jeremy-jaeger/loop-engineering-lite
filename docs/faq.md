# FAQ

**Does this work without the internet?**  
Yes, once Ollama and the model weights are on the machine. Unit tests need
neither (`pytest -q`, `examples/offline_vfs_demo.py`).

**Will it overwrite my files?**  
On success, yes — `commit_to_reality` writes the VFS snapshot into `base_dir`
(default: the current working directory). Run demos in an empty folder.

**Why JSON instead of XML tool calls?**  
Small local models stay on the rails more often with a schema (`format` in
the Ollama chat API) than with free-form prose.

**Can I swap models?**  
Use `agent-loop --model <tag> "…"`. JSON adherence varies wildly under 2B
parameters; expect more harness retries.

**Can I point at LM Studio / another local server?**  
Use `--llm-api-base http://host:port`. The client POSTs Ollama-shaped JSON to
`{base}/api/chat`. Fully OpenAI-compatible adapters are on the [roadmap](ROADMAP.md).

**Can the agent edit multiple files?**  
Yes. VFS keys are path strings (`a.py`, `pkg/b.py`). Nested dirs are created on
simulate/commit. `list_files` is still a flat listing.

**Is the VFS secure?**  
It is a tempdir + dictionary, not gVisor. `shell=True` is used. Do not point
it at sensitive trees. See [SECURITY.md](../SECURITY.md).

**Where are the fancy world models?**  
They are not here. Read [NORTH_STAR.md](NORTH_STAR.md) and
[COMPARISONS.md](COMPARISONS.md). The VFS is the honest stand-in:
action-conditioned rollouts over files and tests.

**Python 2 / `python` vs `python3`?**  
The default prompt forbids `python` and `apt` so tiny models stop trying to
be Debian. Adjust `llm_client.py` if that grounding is wrong for you.
