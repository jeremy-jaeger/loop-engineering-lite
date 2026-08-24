# FAQ

**Does this work without the internet?**  
Yes, once Ollama and the model weights are on the machine. Unit tests need
neither.

**Will it overwrite my files?**  
On a *verified* success, yes — `commit_to_reality` writes agent-touched
files into `--workspace`. Unverified loops write nothing. Run demos in an
empty folder.

**Can a successful `python3 hello.py` trigger a commit?**  
No. The last command must be a pytest/unittest (or `test_*.py`) run with
exit code 0. See [case study 4](case-studies/README.md).

**Why JSON instead of XML tool calls?**  
Small local models stay on the rails more often with a schema (`format` in
the Ollama chat API) than with free-form prose.

**Can I swap models?**  
`export OLLAMA_MODEL=your-tag`. JSON adherence varies wildly under 2B
parameters; expect more harness retries, not silent commits.

**Is the VFS secure?**  
It is a tempdir + dictionary, not gVisor. `shell=True` is used. Do not
point it at sensitive trees. See [SECURITY.md](../SECURITY.md).

**Where are the fancy world models?**  
They are not here. Read [NORTH_STAR.md](NORTH_STAR.md). The VFS is the
honest stand-in: action-conditioned rollouts over files and tests.

**Why is it called Lite?**  
The loop is small. It is not a demo for a private product. Comparison to
larger agents: [comparison.md](comparison.md).
