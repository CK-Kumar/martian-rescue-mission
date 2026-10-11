# The tools an agent may call, in the common format from agents/llm.py.
# Each tool name matches an action type in world/actions.py, so a tool call
# {"name": "repair", "args": {"target": "rover"}} becomes the action
# {"type": "repair", "target": "rover"}.

INSPECT = {
    "name": "inspect",
    "description": "Look closely at one visible object to learn what it is and what state it is in.",
    "params": {
        "type": "object",
        "properties": {"target": {"type": "string", "description": "One of the visible objects."}},
        "required": ["target"],
    },
}

REPAIR = {
    "name": "repair",
    "description": "Check one visible object for faults and fix any you find.",
    "params": {
        "type": "object",
        "properties": {"target": {"type": "string", "description": "One of the visible objects."}},
        "required": ["target"],
    },
}

SET_POWER = {
    "name": "set_power",
    "description": "Set how many kWh per sol go to the O2 generator and the recycler. Stays until changed.",
    "params": {
        "type": "object",
        "properties": {
            "o2": {"type": "number", "description": "kWh per sol for the O2 generator."},
            "recycler": {"type": "number", "description": "kWh per sol for the water recycler."},
        },
        "required": ["o2", "recycler"],
    },
}

USE = {
    "name": "use",
    "description": "Use one visible object for something, today. What the amount means depends on the object.",
    "params": {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "One of the visible objects."},
            "amount": {"type": "number"},
        },
        "required": ["target", "amount"],
    },
}


def tools(world):
    # The same list every sol, on purpose: Claude rejects a conversation
    # whose tool list changes, and a tool named after a hidden thing (say,
    # "use_battery") would give it away. `use` covers what the crew finds.
    # world is unused today; a future world could still vary its tools.
    return [INSPECT, REPAIR, SET_POWER, USE]
