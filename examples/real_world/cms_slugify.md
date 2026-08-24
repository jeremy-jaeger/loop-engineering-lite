# Real-world use: CMS URL slugify (verify before commit)

## The problem

You run a small CMS / blog / docs site. Authors type titles like
`Hello, World!` or `  API_v2 Release  `. Those titles must become URL paths:

| Title | Expected slug |
| --- | --- |
| `Hello, World!` | `hello-world` |
| `  API_v2 Release  ` | `api-v2-release` |
| `---` | `""` (empty) |

If a coding agent writes `slugify.py` straight onto disk, a buggy
implementation can ship path-breaking URLs or silently drop characters.
You want the agent to **prove** the helper with tests first.

## Why this loop is a good fit

Loop Engineering Lite does exactly that:

1. The model writes `slugify.py` and `test_slugify.py` inside an in-memory VFS.
2. It runs `python3 -m pytest` in a **temp copy** of that VFS.
3. Files hit your real working directory **only after** pytest succeeds.
4. A failed simulation leaves your disk untouched.

That is the practical pattern: **local agent as a verified micro-PR factory**
for small, testable utilities (slugs, money parsers, filename sanitizers,
retry helpers) where wrong code is cheap to regenerate and expensive to ship.

## Prompt (run from an empty directory)

```bash
mkdir -p /tmp/lel-cms-slug && cd /tmp/lel-cms-slug

python3 /path/to/loop-engineering-lite/main.py \
  "Use TDD to write slugify(text) in slugify.py for a CMS URL helper.
Rules: lowercase; spaces and underscores become hyphens; keep only
letters, digits, and hyphens; collapse repeated hyphens; strip leading
and trailing hyphens. Empty or punctuation-only input returns ''.
Write tests in test_slugify.py for: 'Hello, World!' -> 'hello-world',
'  API_v2 Release  ' -> 'api-v2-release', '---' -> ''.
Use python3 -m pytest. Do not mark complete until tests pass."
```

## What success looks like

- Log contains `[SIMULATION VERIFIED SUCCESS]`
- Then `[VFS COMMIT]` / `[SUCCESS - TASK COMPLETE]`
- `/tmp/lel-cms-slug/slugify.py` and `test_slugify.py` exist
- Re-running `python3 -m pytest -q` in that directory still passes
