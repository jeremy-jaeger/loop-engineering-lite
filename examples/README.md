# Examples

| Path | What it is |
| --- | --- |
| [prompts/starter.md](prompts/starter.md) | Copy-paste tasks that fit this harness |
| [offline_vfs_demo.py](offline_vfs_demo.py) | VFS + tools with **no** Ollama |
| [sample_transcript.md](sample_transcript.md) | Shape of a verified log |
| [real_world/checkout_money.md](real_world/checkout_money.md) | Checkout cents parser |
| [artifacts/](artifacts/) | Files live TDD runs actually produced |

## Artifacts

`artifacts/` is evidence, not a library. Quality is mixed on purpose:
palindrome helper, Fibonacci, Temperature, a broken Stack, a money parser
that uses `float`. That mix is why the loop simulates pytest before it
commits. See [docs/case-studies](../docs/case-studies/README.md).
