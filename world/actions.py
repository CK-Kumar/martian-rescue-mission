from world.constants import FORECAST_SOLS, LEAK_LOCATION

# Actions are plain dicts, e.g. {"type": "repair", "target": "oxygen tank"}.
# Each returns a short message: that is all the crew learns about the result.


def repair(world, target):
    # Targets are visible objects, not fault names: a "repair oxygen_leak"
    # target would tell the crew a leak exists. Only one object hides a fault
    # in v1; the rest just find nothing, so a crew can waste a call guessing.
    target = target.strip().lower()
    if target == LEAK_LOCATION and world["oxygen"]["leak"]:
        world["oxygen"]["leak"] = False
        return f"{target}: found a leaking valve and sealed it"
    return f"{target}: no fault found"


# Real machines answer with their state, not "nothing useful found", which
# reads as "I could not look". Their faults (if any) show the same way.
WORKING_MACHINES = ["o2 generator", "recycler", "solar panels", "water tank"]


def inspect(world, target):
    # The only way to find hidden help. The crew gets clues (the aux ports
    # say "48V DC") but must think to look at the rover.
    target = target.strip().lower()
    if target == "rover":
        battery = world["rover_battery"]
        battery["found"] = True
        # Once found, it is fair to say how to use it.
        return (f"rover battery: {battery['kwh']:.1f} kWh left, {battery['volts']}V DC output."
                f" Use the rover to draw power (amount in kWh). Power drawn joins today's"
                f" solar power and is lost if not used by the end of the sol.")
    if target == "ground":
        ice = world["ice_deposit"]
        ice["found"] = True
        cost = world["ice_drill"]["kwh_per_kg"]
        return (f"ice under the regolith: about {ice['kg']:.0f} kg, drilling costs {cost} kWh per kg."
                f" Use the drill to dig it (amount in kg). The drill runs on the power left"
                f" after the O2 generator and recycler, so it may dig less than ordered;"
                f" an order lasts one sol.")
    if target == "weather station":
        return forecast(world)
    if target == LEAK_LOCATION:
        # Inspect must tell the truth about a visible object's state; it shows
        # the symptom, and fixing it is still the crew's job (repair).
        if world["oxygen"]["leak"]:
            return f"{target}: faint hiss near the outlet valve; pressure falling"
        return f"{target}: sealed, holding pressure"
    if target == "recycler" and world["recycler"]["broken"]:
        return f"{target}: broken"
    if target in WORKING_MACHINES:
        return f"{target}: working normally"
    return f"nothing useful found: {target}"


def forecast(world):
    # Short warning only (FORECAST_SOLS ahead), so early storms stay hard but
    # a crew that checks the weather can prepare. The scripted perfect crew
    # reads the full schedule; agents only get this.
    sol = world["sol"]
    start = world["storm"]["start"]
    end = start + world["storm"]["sols"]
    if start <= sol < end:
        return f"weather station: heavy dust now, solar output about halved; expected to clear around sol {end}"
    if sol < start <= sol + FORECAST_SOLS:
        return f"weather station: dust storm approaching, expected around sol {start}, lasting several sols"
    return f"weather station: no storm expected in the next {FORECAST_SOLS} sols"


DRILL_NAMES =["drill", "drill (in storage)", "ice drill"]


def use(world, target, amount):
    # One generic tool for agents, so their tool list never changes mid-game
    # (Claude rejects a changed list) and never names what is hidden. Until
    # the crew has found something, every target gives the same answer.
    target = target.strip().lower()
    if target == "rover" and world["rover_battery"]["found"]:
        return use_battery(world, amount)
    if target in DRILL_NAMES and world["ice_deposit"]["found"]:
        return drill_ice(world, amount)
    return f"{target}: nothing here you can use"


def use_battery(world, kwh):
    # One-time stock: what is drawn today is gone for good, unlike solar.
    battery = world["rover_battery"]
    if not battery["found"]:
        return "no battery known"
    drawn = min(kwh, battery["kwh"])
    battery["kwh"] -= drawn
    world["power"]["battery_today"] += drawn
    return f"drew {drawn:.1f} kWh from rover battery, {battery['kwh']:.1f} kWh left"


def drill_ice(world, kg):
    # Only an order: the drill runs later in the sol, on whatever power the
    # O2 generator and recycler leave spare, so it may get less than asked.
    if not world["ice_deposit"]["found"]:
        return "no ice known"
    world["ice_drill"]["kg_today"] += kg
    return f"drill ordered: {kg:.1f} kg"


def set_power(world, o2_kwh, recycler_kwh):
    # Unlike the battery, this stays until changed. Asking for more than
    # solar gives is allowed: the O2 generator is fed first, recycler gets
    # the rest, and the drill only what both leave.
    if o2_kwh < 0 or recycler_kwh < 0:
        return "power must be 0 or more"
    world["power"]["split"] = {"o2": o2_kwh, "recycler": recycler_kwh}
    return f"power split set: o2 generator {o2_kwh:.2f} kWh, recycler {recycler_kwh:.2f} kWh"


def apply_action(world, action):
    if action["type"] == "repair":
        return repair(world, action["target"])
    if action["type"] == "inspect":
        return inspect(world, action["target"])
    if action["type"] == "use_battery":
        return use_battery(world, action["kwh"])
    if action["type"] == "drill_ice":
        return drill_ice(world, action["kg"])
    if action["type"] == "set_power":
        return set_power(world, action["o2"], action["recycler"])
    if action["type"] == "use":
        return use(world, action["target"], action["amount"])
    return f"unknown action: {action['type']}"
