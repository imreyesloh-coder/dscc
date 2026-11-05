import os
import joblib
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ippt_models.joblib")
_bundle = joblib.load(MODEL_PATH)  # loaded once when the app starts
FEATURES = _bundle["features"]
MODELS = _bundle["models"]

BETA_NOTE = ("Beta estimate only. Not a guarantee of your IPPT result. "
             "Accuracy will improve as real training data is collected.")


def predict_future_scores(user):
    """user: dict with age, current_pushups, current_situps,
    current_runtime (seconds), training_frequency (planned sessions per
    week), training_duration (weeks), adherence_pct (0-100)."""
    missing = [f for f in FEATURES if f not in user]
    if missing:
        raise ValueError(f"Missing fields: {missing}")

    row = pd.DataFrame([{f: float(user[f]) for f in FEATURES}])

    pushups = max(0, round(float(MODELS["pushups"].predict(row)[0])))
    situps = max(0, round(float(MODELS["situps"].predict(row)[0])))
    run = max(300, round(float(MODELS["run_seconds"].predict(row)[0])))

    return {
        "predicted_pushups": pushups,
        "predicted_situps": situps,
        "predicted_run_seconds": run,
        "predicted_run_time": f"{run // 60}:{run % 60:02d}",
        "note": BETA_NOTE,
    }
