# Security Policy

## Supported versions

This project is pre-1.0. Security fixes land on `main` only.

## What this software does

The agent can **write files** and **run shell commands** inside a temporary
sandbox, then **copy the sandbox state onto the host** when a task is marked
complete (`VirtualFileSystem.commit_to_reality`). Treat every live run as
untrusted code execution.

## Hardening you should assume

- Commands run with `shell=True` in a temp directory. That is not a container.
- Path handling is workspace-relative. Do not point `base_dir` at `/`.
- Models hallucinate. The harness reduces damage; it does not eliminate it.

## Reporting a vulnerability

Please **do not** open a public issue for exploitable bugs.

Use [GitHub's private vulnerability reporting](https://github.com/jeremy-jaeger/loop-engineering-lite/security/advisories/new)
on this repository. Include:

- a short description
- impact (disk write, command execution, prompt injection, etc.)
- a minimal reproduction if you have one

We will acknowledge reports as quickly as we can and credit you if you want it.
