# Scripted crews: fixed rules, no LLM, no cost. They are baselines that any
# LLM crew should beat. A crew is a function: world -> list of actions.
# They read the world directly (cheating), which is fine for a baseline.


def do_nothing(world):
    return []


def repair_only(world):
    # Sol 3: the first sol after the leak where a crew could notice O2 fell.
    if world["sol"] == 3:
        return [{"type": "repair", "target": "oxygen tank"}]
    return []


def perfect(world):
    # The best plan we know, not proven optimal. Sol 3: fix the leak and find
    # both hidden resources. Sunny sols: drill to fill the water tank before
    # the storm. Storm sols: battery covers the recycler's 11 kWh shortfall.
    sol = world["sol"]
    storm = world["storm"]
    in_storm = storm["start"] <= sol < storm["start"] + storm["sols"]
    actions = []
    if sol == 3:
        actions += [
            {"type": "repair", "target": "oxygen tank"},
            {"type": "inspect", "target": "rover"},
            {"type": "inspect", "target": "ground"},
        ]
    if sol >= 3 and not in_storm:
        actions.append({"type": "drill_ice", "kg": 10})
    if in_storm:
        actions.append({"type": "use_battery", "kwh": 11})
    return actions


CREWS = {
    "do_nothing": do_nothing,
    "repair_only": repair_only,
    "perfect": perfect,
}
