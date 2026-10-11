import sys

from crews.scripted import CREWS
from log import git_info, open_log, write_line
from world.rules import step
from world.start import new_world


def main():
    # Usage: uv run main.py <crew>   e.g. uv run main.py repair_only
    crew_name = sys.argv[1] if len(sys.argv) > 1 else "do_nothing"
    crew = CREWS[crew_name]
    seed = 42
    world = new_world(seed)
    log_file, log_path = open_log(crew_name, seed)

    print(f"crew: {crew_name}")
    print("sol | o2    | water  | messages")
    while not world["dead"] and not world["rescued"]:
        sol = world["sol"]
        actions = crew(world)
        messages = step(world, actions)
        write_line(log_file, {
            "sol": sol,
            "o2": world["oxygen"]["level"],
            "water": world["water"]["level"],
            "actions": actions,
            "messages": messages,
        })
        # Round only for display; the log keeps full precision.
        print(f"{sol:3} | {world['oxygen']['level']:5.2f} | {world['water']['level']:6.2f} | {messages}")

    commit, dirty = git_info()
    write_line(log_file, {
        "result": "dead" if world["dead"] else "rescued",
        "sol": world["sol"],
        "cause": world["cause_of_death"],
        "crew": crew_name,
        "seed": seed,
        "commit": commit,
        "dirty": dirty,
    })
    log_file.close()

    if world["dead"]:
        print(f"DEAD on sol {world['sol']}: {world['cause_of_death']}")
    else:
        print(f"RESCUED on sol {world['sol']}")
    print(f"log: {log_path}")


if __name__ == "__main__":
    main()
