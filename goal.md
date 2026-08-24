# The North Star

**A general-purpose, open-source compositional world-model runtime and self-improving agent loop.** 

The ultimate objective of this project is to create a runtime that any model or framework can plug into—turning inference trajectories into continuous, verifiable capability growth. 

---

## The Reality Check (Why This Exists)

The current state of autonomous agents is plagued by unsolved research problems masquerading as solved features. This repository acknowledges the following realities:

*   **"World-Model Runtime" is unsolved:** Nobody has a working general compositional world model. State-of-the-art models (Dreamer, JEPA, Genie) are narrow, expensive, and nowhere near "general-purpose."
*   **"Self-Improving Loops" are mostly fake:** Genuine recursive self-improvement is arguably the single hardest problem in the field. Every "self-improving agent" repository on GitHub today is really just RAG-over-past-transcripts wearing a trenchcoat.
*   **Pluggability vs. Grounding:** There is a direct tension between building a framework-agnostic system and verifying the world model. The more agnostic you go, the less you can actually verify because you lose access to the underlying substrate.
*   **Verifiable Capability Growth:** Verification is the actual crux of the self-improvement problem. If you could cheaply verify that a trajectory improved capability, RL would largely be solved. We require real, verifiable examples, not theoretical assumptions.

---

## System Architecture

To solve these gaps, this runtime is built on five modular pillars designed to run locally on consumer hardware or modest cloud instances:

1.  **Composable World-Model Core**
    *   Maintains latent and symbolic state representations.
    *   Provides multi-view dynamics prediction and action-conditioned rollouts.
    *   Includes a progress/value head to evaluate states.
    *   *Goal:* Make existing open video/action models agent-native (queryable via a clean API or MCP-style interface).
2.  **Trajectory Engine & Self-Improvement Loop**
    *   Captures agent–environment interactions.
    *   Filters high-quality trajectories.
    *   Runs offline RL or supervised updates to publish improved checkpoints or adapters.
3.  **Harness Layer**
    *   Provides drop-in adapters for popular agent frameworks.
    *   Grants existing tools planning and learning capabilities for free.
4.  **Verification and Safety**
    *   Enforces execution sandboxes and consistency checks.
    *   Supports rollback states and human-in-the-loop (HITL) gates for high-stakes domains.
5.  **Benchmark Suite**
    *   Evaluates progress via open, long-horizon tasks (e.g., coding projects, simulated embodied control, multi-agent collaboration) using strict success metrics.
6. **Lightweight Swarm Composability**
    * The runtime must remain performant enough to execute sub-2B parameter models natively.
    * *Goal:* Enable "Agentic Spawning," where a primary orchestrator can spin up dozens of isolated VFS sandboxes simultaneously, allowing micro-agents to solve parallel sub-tasks (e.g., writing individual React components) without memory swap death spirals.
---

## The Execution Flywheel

A clean, modular implementation creates an immediate network effect:

*   **Simulation Over Trial-and-Error:** Agents (coding, research, browser) query the shared world model for counterfactual rollouts and progress estimation before executing destructive actions.
*   **Continuous Distillation:** The system collects trajectories, evaluates them against verifiable signals (execution success, consistency checks, automated judges), and feeds improved data back into the world model and policy via distillation or lightweight fine-tuning loops.
*   **Qualitative Payoff:** Agents plan more reliably over hours or days, recover from errors by simulating alternatives, and measurably improve over time without constant human redesign.

