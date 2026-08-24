# Security Policy

## Supported versions

Fixes land on `main` only.

## What this software does

The agent can **write files** and **run shell commands** inside a temporary
sandbox, then **copy agent-touched files onto the host** when a
pytest/unittest run in that sandbox exits 0
(`VirtualFileSystem.commit_to_reality`). Treat every live run as untrusted
code execution.

## Hardening you should assume

- Commands run with `shell=True` in a temp directory. That is not a container.
- Paths are jailed to `--workspace`. Do not point it at `/`.
- A passing test suite is not a proof of correctness and not a sandbox escape
  prevention story. Models hallucinate tests too.
- Inference failures must not commit. If you find a path that does, that is
  a vulnerability.

## Reporting a vulnerability

Please **do not** open a public issue for exploitable bugs.

Use [GitHub's private vulnerability reporting](https://github.com/jeremy-jaeger/loop-engineering-lite/security/advisories/new)
on this repository. Include:

- a short description
- impact (disk write, command execution, prompt injection, etc.)
- a minimal reproduction if you have one

We will acknowledge reports as quickly as we can and credit you if you want it.
