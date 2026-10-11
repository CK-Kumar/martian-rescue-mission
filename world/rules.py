from world.actions import apply_action
from world.constants import WATER_GRACE_SOLS
from world.life_support import crew_uses, leak_o2, make_o2, recycle_water, run_drill
from world.power import machine_fractions, solar_today


def clamp_tanks(world):
    # Above max is lost (no room to store it); below 0 means the tank is empty.
    for tank in ["oxygen", "water"]:
        level = world[tank]["level"]
        world[tank]["level"] = min(world[tank]["max"], max(0, level))


def check_death(world):
    # Runs after clamp_tanks, so a tank that ran short reads exactly 0.
    # v1: shared tanks, so the whole crew lives or dies together.
    if world["oxygen"]["level"] <= 0:
        world["dead"] = True
        world["cause_of_death"] = "suffocation"
        return
    if world["water"]["level"] <= 0:
        world["sols_without_water"] += 1
    else:
        world["sols_without_water"] = 0
    if world["sols_without_water"] >= WATER_GRACE_SOLS:
        world["dead"] = True
        world["cause_of_death"] = "dehydration"


def step(world, actions):
    # The crew acts at the start of the sol, then the sol plays out. A crew
    # may also act before calling step (LLM agents do, to see results at once).
    messages = [apply_action(world, action) for action in actions]
    # Make before use: the crew gets today's O2 and water first.
    # Battery joins the same pool as solar; the split decides where it goes.
    kwh = solar_today(world) + world["power"]["battery_today"]
    fractions = machine_fractions(world, kwh)
    make_o2(world, fractions["o2"])
    recycle_water(world, fractions["recycler"])
    if world["ice_drill"]["kg_today"] > 0:
        kg = run_drill(world, fractions["spare_kwh"])
        messages.append(f"drilled {kg:.1f} kg ice, {world['ice_deposit']['kg']:.1f} kg left")
    # Battery power and drill orders only last the sol they were made in.
    # Reset here, at the end, so orders placed before step() still count.
    world["power"]["battery_today"] = 0.0
    world["ice_drill"]["kg_today"] = 0.0
    crew_uses(world)
    leak_o2(world)
    clamp_tanks(world)
    check_death(world)
    if world["dead"]:
        return messages
    world["sol"] += 1
    if world["sol"] >= world["rescue_sol"]:
        world["rescued"] = True
    return messages
