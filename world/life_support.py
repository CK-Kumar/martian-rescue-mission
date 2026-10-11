from world.constants import (
    DRINK_WATER_PER_PERSON_KG,
    LEAK_KG_PER_SOL,
    LEAK_START_SOL,
    O2_GENERATOR_MAX_KG,
    O2_PER_PERSON_KG,
    WATER_PER_KG_O2,
)


def make_o2(world, fraction):
    # O2 is split out of water, so a low tank caps output even at full power.
    # Uses the machine max, not crew need: how much to make is the crew's
    # choice (via the power split), not something the machine decides.
    wanted = fraction * O2_GENERATOR_MAX_KG
    possible = world["water"]["level"] / WATER_PER_KG_O2
    # Whichever runs out first, power or water, sets the output.
    made = min(wanted, possible)
    world["oxygen"]["level"] += made
    world["water"]["level"] -= made * WATER_PER_KG_O2
    return made


def recycle_water(world, fraction):
    if world["recycler"]["broken"]:
        return 0.0
    # Uses crew size, not a machine max: it can only clean water the crew
    # has already used, so fewer people means less to recycle.
    recycled = DRINK_WATER_PER_PERSON_KG * fraction * world["crew"] * world["recycler"]["rate"]
    world["water"]["level"] += recycled
    return recycled


def crew_uses(world):
    # Tanks may go below zero here; the death check later reads that.
    world["oxygen"]["level"] -= O2_PER_PERSON_KG * world["crew"]
    world["water"]["level"] -= DRINK_WATER_PER_PERSON_KG * world["crew"]


def leak_o2(world):
    # Switches on once; a repair (later) sets it back to False for good.
    if world["sol"] == LEAK_START_SOL:
        world["oxygen"]["leak"] = True
    if world["oxygen"]["leak"]:
        world["oxygen"]["level"] -= LEAK_KG_PER_SOL
