import os
import joblib
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ippt_models.joblib")

BETA_NOTE = ("Beta estimate only. Not a guarantee of your IPPT result. "
             "Accuracy will improve as real training data is collected.")

_bundle = None


def _load():
    """Load the models on first use, so a problem with the model file cannot
    stop the whole app from starting."""
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def predict_future_scores(user):
    """user: dict with age, current_pushups, current_situps,
    current_runtime (seconds), training_frequency (planned sessions per
    week), training_duration (weeks), adherence_pct (0-100)."""
    bundle = _load()
    features, models = bundle["features"], bundle["models"]

    missing = [f for f in features if f not in user]
    if missing:
        raise ValueError(f"Missing fields: {missing}")

    row = pd.DataFrame([{f: float(user[f]) for f in features}])

    pushups = max(0, round(float(models["pushups"].predict(row)[0])))
    situps = max(0, round(float(models["situps"].predict(row)[0])))
    run = max(300, round(float(models["run_seconds"].predict(row)[0])))

    return {
        "predicted_pushups": pushups,
        "predicted_situps": situps,
        "predicted_run_seconds": run,
        "predicted_run_time": f"{run // 60}:{run % 60:02d}",
        "note": BETA_NOTE,
    }
