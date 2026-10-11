import argparse

from crews.scripted import CREWS
from log import git_info, open_log, write_line
from tracking import record_run
from world.rules import step
from world.start import new_world


def main():
    # Usage: uv run main.py repair_only --track
    parser = argparse.ArgumentParser()
    parser.add_argument("crew", nargs="?", default="do_nothing", choices=CREWS)
    # Off by default so test runs don't clutter MLflow next to real results.
    parser.add_argument("--track", action="store_true", help="record this run in MLflow")
    args = parser.parse_args()
    crew_name = args.crew
    crew = CREWS[crew_name]
    seed = 42
    world = new_world(seed)
    log_file, log_path = open_log(crew_name, seed)

    print(f"crew: {crew_name}")
    print("sol | o2    | water  | messages")
    rows = []
    while not world["dead"] and not world["rescued"]:
        sol = world["sol"]
        actions = crew(world)
        messages = step(world, actions)
        row = {
            "sol": sol,
            "o2": world["oxygen"]["level"],
            "water": world["water"]["level"],
            "actions": actions,
            "messages": messages,
        }
        rows.append(row)
        write_line(log_file, row)
        # Round only for display; the log keeps full precision.
        print(f"{sol:3} | {world['oxygen']['level']:5.2f} | {world['water']['level']:6.2f} | {messages}")

    commit, dirty = git_info()
    result = {
        "result": "dead" if world["dead"] else "rescued",
        "sol": world["sol"],
        "cause": world["cause_of_death"],
        "crew": crew_name,
        "seed": seed,
        "commit": commit,
        "dirty": dirty,
    }
    write_line(log_file, result)
    log_file.close()
    if args.track:
        record_run(crew_name, seed, rows, result, log_path)

    if world["dead"]:
        print(f"DEAD on sol {world['sol']}: {world['cause_of_death']}")
    else:
        print(f"RESCUED on sol {world['sol']}")
    print(f"log: {log_path}")


if __name__ == "__main__":
    main()
