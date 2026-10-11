import mlflow

# One local database file. MLflow 3.7+ uses this by default; set it explicitly
# so the location never depends on the MLflow version.
mlflow.set_tracking_uri("sqlite:///mlflow.db")


def record_run(crew_name, seed, rows, result, log_path):
    # MLflow holds the summary for comparing runs; the JSONL file attached at
    # the end holds the full story.
    mlflow.set_experiment("martian-rescue")
    with mlflow.start_run(run_name=f"{crew_name}_seed{seed}"):
        mlflow.log_params({
            "crew": crew_name,
            "model": result["model"],
            "seed": seed,
            "commit": result["commit"],
            "dirty": result["dirty"],
        })
        # step=sol makes MLflow draw these as lines over sols.
        for row in rows:
            mlflow.log_metric("o2", row["o2"], step=row["sol"])
            mlflow.log_metric("water", row["water"], step=row["sol"])
            calls = row.get("llm_calls", [])
            if calls:
                mlflow.log_metric("tokens_in", sum(c["tokens_in"] for c in calls), step=row["sol"])
                mlflow.log_metric("cost_usd", sum(c["cost_usd"] or 0 for c in calls), step=row["sol"])
        mlflow.log_metric("last_sol", result["sol"])
        mlflow.log_metric("rescued", 1 if result["result"] == "rescued" else 0)
        # Run totals, only present for LLM crews.
        for key in ["model_calls", "tokens_in", "tokens_out", "cost_usd", "latency_ms_mean"]:
            if key in result:
                mlflow.log_metric(f"total_{key}", result[key])
        mlflow.log_artifact(str(log_path))
