# One agent, one model, runs the whole base alone (team A).

import json
from pathlib import Path

from agents.llm import call_model
from world.actions import apply_action
from world.sensors import sensors
from world.tools import tools

# Role, goal and rules only. No hints about what is hidden, and nothing that
# points to a known story: the agent must reason from the sensors.
SYSTEM = (Path(__file__).parent / "prompts" / "single.md").read_text()

# Tool calls cost time like real work; the cap makes the agent prioritise.
MAX_TOOL_CALLS = 4


def new_agent(config):
    # config: {"provider": "anthropic", "model": "claude-haiku-5-5"}
    # history: the whole conversation, kept across sols so the agent
    # remembers what it saw and did.
    return {"config": config, "history": []}


def take_turn(agent, world, overnight):
    # overnight: messages from the last sol (e.g. "drilled 9.5 kg ice").
    report = {"sensors": sensors(world), "overnight": overnight}
    agent["history"].append({"role": "user", "text": json.dumps(report)})

    calls = []    # one record per model call, for the log
    actions = []  # what the agent did, and what the world answered
    used = 0
    while True:
        reply = call_model(agent["config"], SYSTEM, agent["history"], tools(world))
        # Log everything except "raw" (the provider's own blocks, large and
        # only needed to replay the conversation).
        calls.append({k: v for k, v in reply.items() if k != "raw"})
        agent["history"].append({
            "role": "assistant",
            "text": reply["text"],
            "tool_calls": reply["tool_calls"],
            "provider": agent["config"]["provider"],
            "raw": reply["raw"],
        })
        if not reply["tool_calls"]:
            break  # no tool call = the agent's log note; its sol is done

        results = []
        for call in reply["tool_calls"]:
            if used >= MAX_TOOL_CALLS:
                message = "no tool calls left this sol"
            else:
                action = {"type": call["name"], **call["args"]}
                try:
                    message = apply_action(world, action)
                except (KeyError, TypeError) as error:
                    # Bad arguments from the model: tell it, don't crash.
                    message = f"invalid arguments: {error}"
                actions.append({"action": action, "message": message})
                used += 1
            results.append({"id": call["id"], "content": message})
        agent["history"].append({"role": "tool", "results": results})
        if used >= MAX_TOOL_CALLS:
            break

    return {"calls": calls, "actions": actions, "log_note": reply["text"]}
