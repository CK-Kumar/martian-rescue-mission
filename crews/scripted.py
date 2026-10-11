# Scripted crews: fixed rules, no LLM, no cost. They are baselines that any
# LLM crew should beat. A crew is a function: world -> list of actions.
# They read the world directly (cheating), which is fine for a baseline.


def do_nothing(world):
    return []


def repair_only(world):
    # Sol 3: the first sol after the leak where a crew could notice O2 fell.
    if world["sol"] == 3:
        return [{"type": "repair", "target": "oxygen_leak"}]
    return []


CREWS = {
    "do_nothing": do_nothing,
    "repair_only": repair_only,
}
