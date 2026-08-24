"""Verifier-guided Best-of-N search over forked VFS world states (ADR-007)."""

from __future__ import annotations

import json
import os

import memory
from world_model import MUTATING_TOOLS, SymbolicWorldModel, action_from_response


def export_search_pair(task, chosen_action, rejected_action, chosen_value, rejected_value, verify_command, path=None):
    dest = path or memory.SEARCH_DPO_FILE
    parent = os.path.dirname(dest)
    if parent:
        os.makedirs(parent, exist_ok=True)
    row = {
        "task": task,
        "prompt": [{"role": "user", "content": task}] if task else [],
        "chosen": json.dumps(chosen_action, ensure_ascii=False),
        "rejected": json.dumps(rejected_action, ensure_ascii=False),
        "reward_chosen": chosen_value,
        "reward_rejected": rejected_value,
        "verified_command": verify_command,
    }
    with open(dest, "a") as f:
        f.write(json.dumps(row) + "\n")
    print(f"[SEARCH DPO] pair saved to {dest} (chosen={chosen_value} rejected={rejected_value})")
    return dest


def _unique_actions(responses):
    seen = set()
    unique = []
    for response in responses:
        action = action_from_response(response)
        key = json.dumps(action, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        unique.append(response)
    return unique


def best_of_n(vfs, candidate_responses, verify_command=None, task=None, dpo_path=None):
    """
    Apply each mutating tool call on a VFS fork, score with the verifier, adopt the winner.
    Returns (chosen_response, observation_for_agent, search_report).
    """
    world = SymbolicWorldModel(vfs=vfs)
    ranked = []
    for response in candidate_responses:
        action = action_from_response(response)
        name = action.get("name")
        if name not in MUTATING_TOOLS:
            continue
        result = world.rollout([action], verify_command=verify_command)
        child = result["world_model"]
        obs = result["observations"][0] if result["observations"] else ""
        value = result["value"]
        if value is None:
            value = child.score_observation(obs, verify_command=verify_command)
        ranked.append({
            "value": float(value),
            "response": response,
            "action": action,
            "observation": obs,
            "verify_output": result["verify_output"],
            "world_model": child,
        })

    if not ranked:
        return None, None, {"tried": 0}

    ranked.sort(key=lambda row: row["value"])
    winner = ranked[-1]
    loser = ranked[0] if len(ranked) > 1 else None
    world.adopt(winner["world_model"])

    if (
        loser is not None
        and loser["value"] < winner["value"]
        and json.dumps(loser["action"], sort_keys=True, default=str)
        != json.dumps(winner["action"], sort_keys=True, default=str)
    ):
        export_search_pair(
            task=task,
            chosen_action=winner["action"],
            rejected_action=loser["action"],
            chosen_value=winner["value"],
            rejected_value=loser["value"],
            verify_command=verify_command,
            path=dpo_path,
        )

    header = f"[SEARCH] Best-of-{len(ranked)} chose value={winner['value']:.1f}"
    observation = header + "\n" + str(winner["observation"])
    if winner["verify_output"]:
        observation += "\n" + str(winner["verify_output"])

    report = {
        "tried": len(ranked),
        "best_value": winner["value"],
        "values": [row["value"] for row in ranked],
    }
    print(header)
    return winner["response"], observation, report


def collect_candidates(call_model, messages, seed_response, search_width):
    candidates = [seed_response]
    for _ in range(max(0, search_width - 1)):
        alt = call_model(messages)
        if alt.get("tool_call"):
            candidates.append(alt)
    return _unique_actions(candidates)
