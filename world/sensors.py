from world.constants import (
    DRINK_WATER_PER_PERSON_KG,
    O2_GENERATOR_KWH,
    O2_GENERATOR_MAX_KG,
    O2_PER_PERSON_KG,
    RECYCLER_KWH,
    WATER_PER_KG_O2,
)
from world.power import dust_today

# Everything the crew can see around the base. Only "rover" and "ground"
# hide something; the rest are decoys, so finding help takes reasoning, and
# every crew (LLM or decision model) picks inspect targets from this same list.
VISIBLE_OBJECTS = [
    "airlock", "antenna", "comms dish", "drill (in storage)", "ground",
    "habitat wall", "medical kit", "rover", "solar panels", "spare suits",
    "supply crate", "toolbox", "water tank", "oxygen tank", "weather station",
]


def sensors(world):
    # What instruments on a real base would show. Never the leak flag, the
    # storm schedule, or hidden resources until the crew has found them.
    # Rounded: agents read text, and long decimals waste tokens.
    reading = {
        "sol": world["sol"],
        "rescue_ship_sol": world["rescue_sol"],
        "crew": world["crew"],
        # A real crew knows its life-support specs; without them an agent can
        # only react, not plan. None of this gives away a hidden resource.
        "crew_needs_per_sol": {
            "oxygen_kg": round(O2_PER_PERSON_KG * world["crew"], 2),
            "water_kg": round(DRINK_WATER_PER_PERSON_KG * world["crew"], 2),
        },
        "oxygen_kg": round(world["oxygen"]["level"], 2),
        "oxygen_max_kg": world["oxygen"]["max"],
        "water_kg": round(world["water"]["level"], 2),
        "water_max_kg": world["water"]["max"],
        "sky_dust": dust_today(world),
        "solar_panels_max_kwh": world["power"]["solar_kwh"],
        "power_split_kwh": world["power"]["split"],
        "o2_generator": {
            "max_o2_kg_per_sol": O2_GENERATOR_MAX_KG,
            "full_power_kwh": O2_GENERATOR_KWH,
            "water_used_per_kg_o2": WATER_PER_KG_O2,
            "aux_port": "48V DC, unused",
        },
        "recycler": {
            "status": "broken" if world["recycler"]["broken"] else "ok",
            "full_power_kwh": RECYCLER_KWH,
            "recovers_of_drinking_water": world["recycler"]["rate"],
            "aux_port": "48V DC, unused",
        },
        "visible_objects": VISIBLE_OBJECTS,
    }
    if world["rover_battery"]["found"]:
        reading["rover_battery_kwh"] = round(world["rover_battery"]["kwh"], 2)
    if world["ice_deposit"]["found"]:
        reading["ice_deposit_kg"] = round(world["ice_deposit"]["kg"], 2)
    return reading
