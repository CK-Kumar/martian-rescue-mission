# Rates per crew member per sol. Sources: NASA life-support planning figures
O2_PER_PERSON_KG = 0.84
DRINK_WATER_PER_PERSON_KG = 3.8
WATER_PER_KG_O2 = 1.125  # electrolysis: 36 g water -> 32 g O2

# Energy each machine needs per sol to run at full rate.
O2_GENERATOR_KWH = 28.75  # 4.2 kg O2 at ~6.8 kWh/kg
RECYCLER_KWH = 18         # ISS water system average draw

# Most O2 the generator can make per sol at full power. 25% above what 4 crew
# breathe (3.36), so the crew can rebuild the O2 tank, at a cost in power and
# water. It belongs to the machine, so it stays fixed if the crew changes.
O2_GENERATOR_MAX_KG = 4.2

# Hidden fault. Bigger than the generator's 0.84 kg headroom, so the crew can't
# out-produce it and must find and repair it. Starts before the earliest storm
# (sol 4). Ignored, it kills around sol 10-11. Game numbers.
LEAK_START_SOL = 2
LEAK_LOCATION = "oxygen tank"  # a visible object; repair it to seal the leak
LEAK_KG_PER_SOL = 2.0

# Sols the crew survives with an empty water tank (about the human limit).
WATER_GRACE_SOLS = 3

# How many sols ahead the weather station can see a storm coming.
FORECAST_SOLS = 2
