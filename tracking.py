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
            "seed": seed,
            "commit": result["commit"],
            "dirty": result["dirty"],
        })
        # step=sol makes MLflow draw these as lines over sols.
        for row in rows:
            mlflow.log_metric("o2", row["o2"], step=row["sol"])
            mlflow.log_metric("water", row["water"], step=row["sol"])
        mlflow.log_metric("last_sol", result["sol"])
        mlflow.log_metric("rescued", 1 if result["result"] == "rescued" else 0)
        mlflow.log_artifact(str(log_path))
