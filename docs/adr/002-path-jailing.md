# ADR-002: Path-jailing and dedicated file creation

**Date:** 2026-08-23  
**Status:** Accepted

## Context

Without `write_file`, models reached for `echo > file`. Unjailed shell
access is a footgun when paths hallucinate. An earlier commit wrote the
entire VFS snapshot, including files the agent never touched.

## Decision

- Add `write_file(filepath, content)`.
- Keep host I/O behind the VFS: tools mutate a dict; `simulate_command`
  materializes a tempdir; `commit_to_reality` is the only host write.
- Resolve paths against `base_dir` and reject anything that escapes it.
- Commit only paths in `touched_paths`.

## Consequences

The agent can scaffold multi-file projects. It cannot edit `~/.zshrc`
unless you launch with that directory as `--workspace` *and* then pass
the verification gate. Pre-existing host files the agent never wrote
are left alone.
