"""
Symbolic world-model API over the VFS.

This is the grounded, code-domain instance of pillar 1: state, action-conditioned
rollouts, and a progress/value head. The head is the binary test verifier — not a
learned latent — because verification is the North Star's actual constraint.
"""

from __future__ import annotations

from tools import execute_tool
from vfs import VirtualFileSystem

MUTATING_TOOLS = {
    "write_file", "write_file",
    "search_and_replace", "search_and_replace",
    "run_command", "run_command",
}


def action_from_response(response):
    call = (response or {}).get("tool_call") or {}
    return {"name": call.get("name"), "args": call.get("args") or {}}


class SymbolicWorldModel:
    def __init__(self, vfs=None, base_dir="."):
        self.vfs = vfs or VirtualFileSystem(base_dir=base_dir)

    def fork(self):
        return SymbolicWorldModel(vfs=self.vfs.fork())

    def adopt(self, other):
        self.vfs.adopt(other.vfs)

    def value(self):
        return self.vfs.value()

    def step(self, action):
        name = action.get("name")
        args = action.get("args") or {}
        observation = execute_tool(self.vfs, name, args)
        return observation, self.value()

    def rollout(self, actions, verify_command=None):
        """Counterfactual: apply actions on a fork, optionally score with tests."""
        child = self.fork()
        observations = []
        for action in actions:
            obs, _value = child.step(action)
            observations.append(obs)
        verify_output = None
        if verify_command:
            verify_output, _value = child.step({
                "name": "run_command",
                "args": {"command": verify_command},
            })
        return {
            "world_model": child,
            "value": child.value(),
            "observations": observations,
            "verify_output": verify_output,
        }

    def score_observation(self, observation, verify_command=None):
        if verify_command:
            return self.value() if self.value() is not None else 0.0
        if str(observation).startswith("Error"):
            return 0.0
        last = self.vfs.last_command()
        if last:
            return float(last["score"])
        return 0.5
