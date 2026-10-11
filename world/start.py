import random


def new_world(seed):
    # Same seed -> same storm, so every team faces the same Mars.
    rng = random.Random(seed)
    return {
        "seed": seed,
        "sol": 1,
        "crew": 4,
        "dead": False,
        "cause_of_death": None,
        "rescued": False,
        # Rescue ship lands on this sol. Numbers below are tuned so only a crew
        # that uses battery + ice + recycler + stockpiling reaches it.
        "rescue_sol": 20,
        # Clear-sky solar covers both machines (41 kWh) with 19 spare; a dust storm (0.5)
        # halves it, forcing a choice between O2 and water.
        # Start 4-10 only: earlier leaves no time to stockpile (best play
        # dies), later lets lazy play reach rescue. Found by simulation.
        "storm": {"start": rng.randint(4, 10), "sols": 7, "dust": 0.5},
        # Default o2 split 23 kWh = 0.8 of the generator = 3.36 kg, exactly what
        # the crew breathes. Giving it more power stockpiles O2.
        # battery_today: kWh the crew drew from the rover battery this sol.
        "power": {"solar_kwh": 60, "dust": 0.0, "split": {"o2": 23, "recycler": 18}, "battery_today": 0.0},
        # Machines start on: a real base never has life support off, and we
        # test crisis handling, not pressing "on". A do-nothing crew dies of
        # the leak around sol 10; to be confirmed when step() runs.
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
