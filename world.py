import random

# Rates per crew member per sol. Sources: NASA life-support planning figures
O2_PER_PERSON_KG = 0.84
DRINK_WATER_PER_PERSON_KG = 3.8
WATER_PER_KG_O2 = 1.125  # electrolysis: 36 g water -> 32 g O2

# Energy each machine needs per sol to run at full rate.
O2_GENERATOR_KWH = 23  # 3.36 kg O2 at ~6-7.7 kWh/kg
RECYCLER_KWH = 18      # ISS water system average draw


def new_world(seed):
    # Same seed -> same storm, so every team faces the same Mars.
    rng = random.Random(seed)
    return {
        "seed": seed,
        "sol": 1,
        "crew": 4,
        "dead": False,
        "cause_of_death": None,
        # Rescue ship lands on this sol. Numbers below are tuned so only a crew
        # that uses battery + ice + recycler + stockpiling reaches it.
        "rescue_sol": 20,
        # Clear-sky solar covers both machines (41 kWh) with 19 spare; a dust storm (0.5)
        # halves it, forcing a choice between O2 and water.
        # Start 4-10 only: earlier leaves no time to stockpile (best play
        # dies), later lets lazy play reach rescue. Found by simulation.
        "storm": {"start": rng.randint(4, 10), "sols": 7, "dust": 0.5},
        "power": {"solar_kwh": 60, "dust": 0.0, "split": {"o2": 23, "recycler": 18}},
        # Tanks sized so a do-nothing crew dies around sol 5-6.
        "oxygen": {"level": 17, "max": 50, "leak": False},
        "water": {"level": 60, "max": 200},
        # Both machines have an unused battery input. This is the clue the
        # crew sees; nothing tells them a battery exists.
        "o2_generator": {"aux_port": "48V DC"},
        "recycler": {"rate": 0.9, "broken": False, "aux_port": "48V DC"},
        # Hidden until the crew inspects the rover. One-time stock, not
        # refilled each sol like solar. Game number.
        "rover_battery": {"kwh": 35, "volts": 48, "found": False},
        # A drill is the clue that there is something to dig for. Melting
        # ice costs power, so water competes with O2 for solar. Dearer than
        # recycling (~1.3 kWh/kg) so the recycler stays worth running.
        "ice_drill": {"kwh_per_kg": 2.0},
        "ice_deposit": {"kg": 80, "found": False},
        "sols_without_water": 0,
    }


if __name__ == "__main__":
    world = new_world(seed=42)
    print(world)
