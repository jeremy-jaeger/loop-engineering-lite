# ADR-002: Path-jailing and dedicated file creation

**Date:** 2026-08-23  
**Status:** Accepted (evolved)

## Context

Without `write_file`, models reached for `echo > file`. Unjailed shell access
is a footgun when paths hallucinate.

## Decision

- Add `write_file(filepath, content)`.
- Keep host I/O behind the VFS: tools mutate a dict; `simulate_command` materializes
  a tempdir; `commit_to_reality` is the only host write of the snapshot.

Early drafts jailed `os.path.abspath` against cwd. The current design is
stricter for *commands* (they never see the real tree until commit) and broader
for *commit* (the whole snapshot is written).

## Consequences

The agent can scaffold multi-file projects. It cannot edit `~/.zshrc` unless
you launch with that directory as `base_dir` and then commit.
