# How this differs

Short comparisons so readers do not confuse this repo with latent world-model
papers or general agent frameworks.

## Research world models

| Project | Substrate | How Loop Lite differs |
| --- | --- | --- |
| **Genie / JEPA** | Latent video / representation models | We use a **compositional file VFS**, not a latent video model. Easier to reason about; no visual reasoning yet. |
| **Dreamer** | Model-based RL in latent dynamics | Focused on offline RL agents; we focus on **agent scaffolding** with a binary verify signal (tests/commands). |
| **Classical planners** | Symbolic state | Same spirit (simulate before act), but our state is **files + shell**, not PDDL. |

## Agent frameworks

| Project | Default disk behavior | How Loop Lite differs |
| --- | --- | --- |
| **LangChain / LlamaIndex agents** | Tools often hit the real FS / APIs | Disk safety is **mandatory**: mutate VFS → simulate → maybe commit. |
| **AutoGPT-style loops** | Long-running tool use on the host | We stay a **tiny** harness (~500 lines), offline-first, stdlib runtime. |
| **Cloud coding agents** | Remote sandboxes / proprietary | No account, no remote IDE — **Ollama on your machine**. |

## What we are not claiming

- We are **not** a general video/action world model.
- We are **not** recursive self-improvement of weights (see [self-improvement.md](self-improvement.md)).
- We are **not** a hardened security sandbox (see [SECURITY.md](../SECURITY.md)).

Ambition lives in [NORTH_STAR.md](NORTH_STAR.md). Shipping truth lives in the README.
