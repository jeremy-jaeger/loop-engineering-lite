# FAQ

**Does this work without the internet?**  
Yes, once Ollama and the model weights are on the machine. Unit tests need
neither.

**Will it overwrite my files?**  
On success, yes — `commit_to_reality` writes the VFS snapshot into `base_dir`
(default: the current working directory). Run demos in an empty folder.

**Why JSON instead of XML tool calls?**  
Small local models stay on the rails more often with a schema (`format` in
the Ollama chat API) than with free-form prose.

**Can I swap models?**  
Change the `model` argument in `call_ollama` / `reflect_on_trace`. JSON
adherence varies wildly under 2B parameters; expect more harness retries.

**Is the VFS secure?**  
It is a tempdir + dictionary, not gVisor. `shell=True` is used. Do not point
it at sensitive trees. See [SECURITY.md](../SECURITY.md).

**Where are the fancy world models?**  
They are not here. Read [NORTH_STAR.md](NORTH_STAR.md). The VFS is the honest
stand-in: action-conditioned rollouts over files and tests.

**Python 2 / `python` vs `python3`?**  
The default prompt forbids `python` and `apt` so tiny models stop trying to
be Debian. Adjust `llm_client.py` if that grounding is wrong for you.
