# Martian Rescue Mission

A crew of 4 LLM agents, each from a different model family, runs a small
simulated Mars base. A rescue ship lands on **sol 20** (a sol is a Mars day).
Can they keep everyone alive until then?

The world is plain Python with no LLM inside. Agents will only see sensor
readings and act through tools, so every claim they make can be checked
against the world's true state.

## Run it

```
uv run main.py
```

## The world (v1)

- **Crew:** 4 people sharing one O₂ tank and one water tank.
- **Power:** solar panels give 60 kWh per sol. They feed two machines:
  - **O₂ generator:** splits water into oxygen.
  - **Water recycler:** cleans used water so it can be drunk again.
- **Dust storm:** halves solar power for 7 sols. When it starts depends on the seed.
- **O₂ leak:** starts on sol 2 and drains 2 kg per sol until repaired. It is
  never announced; the crew only sees O₂ falling.
- **Hidden help:** a rover battery and an ice deposit exist, but nothing tells
  the crew. They have to notice the clues.
- **Death:** O₂ tank empty, or water tank empty for 3 sols in a row. The whole
  crew lives or dies together.

All numbers are in `world/constants.py` and `world/start.py`, with the reason
for each one.

## Layout

```
main.py               runs one game and prints each sol
world/
  constants.py        all numbers
  start.py            new_world(seed): starting state
  power.py            weather and how much power each machine gets
  life_support.py     make O₂, recycle water, crew use, leak
  rules.py            tank limits, death check, step() for one sol
```

## Results

See [RESULTS.md](RESULTS.md).
