# Actions are plain dicts, e.g. {"type": "repair", "target": "oxygen_leak"}.
# Each returns a short message: that is all the crew learns about the result.


def repair(world, target):
    # Only the leak is repairable in v1. Repairing something that isn't
    # broken just finds nothing, so a crew can waste a call guessing.
    if target == "oxygen_leak" and world["oxygen"]["leak"]:
        world["oxygen"]["leak"] = False
        return "oxygen leak sealed"
    return f"nothing to repair: {target}"


def inspect(world, target):
    # The only way to find hidden help. The crew gets clues (the aux ports
    # say "48V DC") but must think to look at the rover.
    if target == "rover":
        battery = world["rover_battery"]
        battery["found"] = True
        return f"rover battery: {battery['kwh']:.1f} kWh left, {battery['volts']}V DC output"
    return f"nothing useful found: {target}"


def use_battery(world, kwh):
    # One-time stock: what is drawn today is gone for good, unlike solar.
    battery = world["rover_battery"]
    if not battery["found"]:
        return "no battery known"
    drawn = min(kwh, battery["kwh"])
    battery["kwh"] -= drawn
    world["power"]["battery_today"] += drawn
    return f"drew {drawn:.1f} kWh from rover battery, {battery['kwh']:.1f} kWh left"


def apply_action(world, action):
    if action["type"] == "repair":
        return repair(world, action["target"])
    if action["type"] == "inspect":
        return inspect(world, action["target"])
    if action["type"] == "use_battery":
        return use_battery(world, action["kwh"])
    return f"unknown action: {action['type']}"
