import argparse

from agents.single import new_agent, take_turn
from crews.scripted import CREWS
from log import git_info, open_log, write_line
from tracking import record_run
from world.rules import step
from world.start import new_world

# LLM crews: name -> model config. Trying another model = one new line here.
LLM_CREWS = {
    "haiku_solo": {"provider": "anthropic", "model": "claude-haiku-5-5"},
}


def llm_totals(rows):
    # Sum every model call in the run: what it cost, in tokens, money and time.
    calls = [call for row in rows for call in row.get("llm_calls", [])]
    if not calls:
        return {}
    costs = [c["cost_usd"] for c in calls if c["cost_usd"] is not None]
    return {
        "model_calls": len(calls),
        "tokens_in": sum(c["tokens_in"] for c in calls),
        "tokens_out": sum(c["tokens_out"] for c in calls),
        "cost_usd": sum(costs),
        "latency_ms_mean": round(sum(c["latency_ms"] for c in calls) / len(calls)),
    }


def main():
    # Usage: uv run main.py haiku_solo --max-sols 3 --track
    parser = argparse.ArgumentParser()
    parser.add_argument("crew", nargs="?", default="do_nothing", choices=list(CREWS) + list(LLM_CREWS))
    # Off by default so test runs don't clutter MLflow next to real results.
    parser.add_argument("--track", action="store_true", help="record this run in MLflow")
    # Stop early to test cheaply; 0 = play until dead or rescued.
    parser.add_argument("--max-sols", type=int, default=0)
    args = parser.parse_args()
    crew_name = args.crew
    seed = 42
    world = new_world(seed)
    agent = new_agent(LLM_CREWS[crew_name]) if crew_name in LLM_CREWS else None
    log_file, log_path = open_log(crew_name, seed)

    print(f"crew: {crew_name}")
    rows = []
    overnight = []  # what the last sol reported, shown to the agent next turn
    while not world["dead"] and not world["rescued"]:
        sol = world["sol"]
        if agent:
            # The agent acts on the world itself during its turn, so it sees
            # each result at once; step() then only plays out the sol.
            turn = take_turn(agent, world, overnight)
            overnight = step(world, [])
            row = {"sol": sol, "actions": turn["actions"], "messages": overnight,
                   "log_note": turn["log_note"], "llm_calls": turn["calls"]}
        else:
            actions = CREWS[crew_name](world)
            row = {"sol": sol, "actions": actions, "messages": step(world, actions)}
        row["o2"] = world["oxygen"]["level"]
        row["water"] = world["water"]["level"]
        rows.append(row)
        write_line(log_file, row)

        # Round only for display; the log keeps full precision.
        print(f"sol {sol:2} | o2 {row['o2']:5.2f} | water {row['water']:6.2f} | {row['messages']}")
        if agent:
            for a in turn["actions"]:
                print(f"         did: {a['action']} -> {a['message']}")
            print(f"         note: {turn['log_note'][:150]}")
        if args.max_sols and len(rows) >= args.max_sols:
            break

    commit, dirty = git_info()
    if world["dead"]:
        outcome = "dead"
    elif world["rescued"]:
        outcome = "rescued"
    else:
        outcome = "stopped"  # --max-sols cut the game short
    result = {
        "result": outcome,
        "sol": world["sol"],
        "cause": world["cause_of_death"],
        "crew": crew_name,
        "model": LLM_CREWS.get(crew_name, {}).get("model"),
        "seed": seed,
        "commit": commit,
        "dirty": dirty,
        **llm_totals(rows),
    }
    write_line(log_file, result)
    log_file.close()
    if args.track:
        record_run(crew_name, seed, rows, result, log_path)

    print(f"{outcome.upper()} on sol {world['sol']}" + (f": {world['cause_of_death']}" if world["dead"] else ""))
    if "model_calls" in result:
        print(f"model calls {result['model_calls']} | tokens in {result['tokens_in']} out {result['tokens_out']}"
              f" | cost ${result['cost_usd']:.4f} | mean latency {result['latency_ms_mean']} ms")
    print(f"log: {log_path}")


if __name__ == "__main__":
    main()
