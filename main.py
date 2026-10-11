from world.rules import step
from world.start import new_world


def main():
    world = new_world(seed=42)
    print("sol | o2    | water")
    while not world["dead"] and not world["rescued"]:
        sol = world["sol"]
        step(world, [])  # do-nothing crew: no actions
        # Round only for display; the world keeps full precision.
        print(f"{sol:3} | {world['oxygen']['level']:5.2f} | {world['water']['level']:6.2f}")
    if world["dead"]:
        print(f"DEAD on sol {world['sol']}: {world['cause_of_death']}")
    else:
        print(f"RESCUED on sol {world['sol']}")


if __name__ == "__main__":
    main()
