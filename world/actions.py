# Actions are plain dicts, e.g. {"type": "repair", "target": "oxygen_leak"}.
# Each returns a short message: that is all the crew learns about the result.


def repair(world, target):
    # Only the leak is repairable in v1. Repairing something that isn't
    # broken just finds nothing, so a crew can waste a call guessing.
    if target == "oxygen_leak" and world["oxygen"]["leak"]:
        world["oxygen"]["leak"] = False
        return "oxygen leak sealed"
    return f"nothing to repair: {target}"


def apply_action(world, action):
    if action["type"] == "repair":
        return repair(world, action["target"])
    return f"unknown action: {action['type']}"
