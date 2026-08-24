# North star

**A general-purpose, open-source compositional world-model runtime and
self-improving agent loop.**

The objective is a runtime any model or framework can plug into — turning
inference trajectories into continuous, **verifiable** capability growth.

This file is the ambition. [architecture.md](architecture.md) is what ships today.

---

## Why this exists

The current agent ecosystem is full of unsolved research problems sold as
product features. This repository names them:

- **"World-model runtime" is unsolved.** Dreamer, JEPA, Genie and friends are
  narrow and expensive. Nobody has a working *general* compositional world model.
- **"Self-improving loops" are mostly fake.** Genuine recursive self-improvement
  is among the hardest problems in the field. Most GitHub "self-improving
  agents" are RAG over past transcripts.
- **Pluggability vs grounding.** The more framework-agnostic you go, the less
  you can verify, because you lose the substrate.
- **Verification is the crux.** If you could cheaply verify that a trajectory
  improved capability, a lot of RL would collapse into an engineering problem.
  We want real, checkable examples — not slides.

## Target pillars

1. **Composable world-model core** — latent + symbolic state, action-conditioned
   rollouts, a progress head. *Shipped stand-in:* the VFS sandbox (`fork` /
   `adopt` exist; a learned value head does not).
2. **Trajectory engine** — capture, filter, optional offline update of
   checkpoints or adapters. *Shipped:* reward-labeled JSONL. *Not shipped:*
   a bundled trainer.
3. **Harness layer** — drop-in adapters so existing tools get planning/learning.
4. **Verification and safety** — sandboxes, consistency checks, HITL for
   high-stakes domains. *Shipped:* pytest/unittest gate + path jail.
5. **Benchmark suite** — long-horizon tasks with strict success metrics.
   *Shipped:* the [case studies](case-studies/README.md), not a public leaderboard.
6. **Lightweight swarm composability** — stay fast enough for sub-2B models and
   many isolated sandboxes without swap death.

## Flywheel (when it is real)

- Simulate before destructive actions.
- Distill only trajectories with verifiable signals (tests, judges, invariants).
- Measure improvement on held-out tasks, not vibes.

Until those measurements exist, this project will keep the marketing quieter
than the logs.
