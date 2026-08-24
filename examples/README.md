# Examples

| Path | What it is |
| --- | --- |
| [prompts/starter.md](prompts/starter.md) | Copy-paste tasks that fit this harness |
| [real_world/cms_slugify.md](real_world/cms_slugify.md) | Practical CMS slug helper (verify-before-commit) |
| [offline_vfs_demo.py](offline_vfs_demo.py) | VFS + tools with **no** Ollama |
| [sample_transcript.md](sample_transcript.md) | What a good log looks like |
| [artifacts/](artifacts/) | Files a live TDD run actually produced |

## Artifacts

`artifacts/` is not the product. It is evidence: palindrome helper, Fibonacci,
Temperature, a Stack — the sort of tiny TDD jobs `scripts/generate_dataset.sh`
feeds the loop. Quality varies (that is the point of verification).

Do not import these modules as a library.
