import sys

from crews.scripted import CREWS
from world.rules import step
from world.start import new_world


def main():
    # Usage: uv run main.py <crew>   e.g. uv run main.py repair_only
    crew_name = sys.argv[1] if len(sys.argv) > 1 else "do_nothing"
    crew = CREWS[crew_name]
    world = new_world(seed=42)
    print(f"crew: {crew_name}")
    print("sol | o2    | water  | messages")
    while not world["dead"] and not world["rescued"]:
        sol = world["sol"]
        messages = step(world, crew(world))
        # Round only for display; the world keeps full precision.
        print(f"{sol:3} | {world['oxygen']['level']:5.2f} | {world['water']['level']:6.2f} | {messages}")
    if world["dead"]:
        print(f"DEAD on sol {world['sol']}: {world['cause_of_death']}")
    else:
        print(f"RESCUED on sol {world['sol']}")


if __name__ == "__main__":
    main()
