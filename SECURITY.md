# Security Policy

## Supported versions

This project is pre-1.0. Security fixes land on `main` only.

## What this software does

The agent can **write files** and **run shell commands** inside a temporary
sandbox, then **copy the sandbox state onto the host** when a task is marked
complete (`VirtualFileSystem.commit_to_reality`). Treat every live run as
untrusted code execution.

## Isolation model (honest)

This is **tempdir + commit**, not a container, VM, or seccomp jail.

| What the VFS protects against | What it does **not** protect against |
| --- | --- |
| Filesystem mutation while the model is still failing tests | Prompt injection that tricks the agent into bad tools |
| Committing broken edits without a successful `run_command` score | Code injection / malware in model-generated scripts |
| Accidental clobber of host files mid-iteration | Escaping the tempdir via `shell=True` (absolute paths, `cd`, network, etc.) |
| Shipping hallucinations as “done” without a verify signal | Running an untrusted model on a machine you care about |

A capable or malicious model prompt can leave the tempdir. Path handling is
workspace-relative for VFS keys; the shell is not confined beyond `cwd=temp_dir`.

## Recommended mitigations

1. **Always demo in a throwaway directory** (`mkdir /tmp/lel-demo && cd …`).
2. **Run untrusted models inside a VM or container** you are willing to wipe.
3. Do **not** point `base_dir` at `/`, `$HOME`, or production trees.
4. Prefer small local models you control; treat API-backed models as equally untrusted.
5. Review `dataset.jsonl` / committed files before promoting them elsewhere.

## Reporting a vulnerability

Please **do not** open a public issue for exploitable bugs.

Use [GitHub's private vulnerability reporting](https://github.com/jeremy-jaeger/loop-engineering-lite/security/advisories/new)
on this repository. Include:

- a short description
- impact (disk write, command execution, prompt injection, etc.)
- a minimal reproduction if you have one

We will acknowledge reports as quickly as we can and credit you if you want it.
