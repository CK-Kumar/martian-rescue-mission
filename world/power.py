from world.constants import O2_GENERATOR_KWH, RECYCLER_KWH


def dust_today(world):
    storm = world["storm"]
    if storm["start"] <= world["sol"] < storm["start"] + storm["sols"]:
        return storm["dust"]
    return 0.0


def solar_today(world):
    return world["power"]["solar_kwh"] * (1 - dust_today(world))


def machine_fractions(world, kwh):
    # O2 generator is fed first: no O2 kills in a sol, no water takes several.
    split = world["power"]["split"]
    o2_kwh = min(split["o2"], kwh)
    recycler_kwh = min(split["recycler"], kwh - o2_kwh)
    return {
        "o2": min(o2_kwh / O2_GENERATOR_KWH, 1.0),
        "recycler": min(recycler_kwh / RECYCLER_KWH, 1.0),
    }
