# Architecture Decision Records

Decisions that shaped the lite harness.

| ID | Title | Status |
| --- | --- | --- |
| [001](001-tool-enforcement.md) | Self-correction loop for tool enforcement | Accepted |
| [002](002-path-jailing.md) | Path-jailing and dedicated file creation | Accepted |
| [003](003-memory-window.md) | Sliding-window memory and truncation | Accepted |
| [004](004-experience-replay.md) | Trajectory abstraction / experience replay | Accepted (heuristics in `knowledge.json`) |
| [005](005-sft-export.md) | Trajectory serialization + adapter flywheel | Implemented (`improve/`; MLX on Apple Silicon) |
| [006](006-verification-gate.md) | Gate commit/export on pytest/unittest | Accepted |
| [007](007-test-time-search.md) | Best-of-N search over VFS forks | Accepted |
