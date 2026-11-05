import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression

# Run this file ONCE to create ippt_models.joblib (the saved model).
# The model is trained on synthetic data, so it is a BETA placeholder.
# When real data is available, replace the data section with
# pd.read_csv(...) and run this again.

np.random.seed(42)
n = 500

age = np.random.randint(18, 40, n)
current_pushups = np.random.randint(10, 60, n)
current_situps = np.random.randint(20, 70, n)
current_runtime = np.random.randint(600, 900, n)
training_frequency = np.random.randint(0, 7, n)
training_duration = np.random.randint(0, 13, n)
adherence_pct = np.random.randint(30, 101, n)
adh = adherence_pct / 100

future_pushups = np.clip(
    current_pushups + training_frequency * training_duration * 0.30 * adh
    - 0.05 * current_pushups - 0.10 * (age - 18)
    + np.random.normal(0, 3, n), 0, None)
future_situps = np.clip(
    current_situps + training_frequency * training_duration * 0.25 * adh
    - 0.04 * current_situps - 0.08 * (age - 18)
    + np.random.normal(0, 3, n), 0, None)
future_runtime = np.clip(
    current_runtime - training_frequency * training_duration * 1.2 * adh
    + 0.5 * (age - 18) + np.random.normal(0, 10, n), 300, None)

FEATURES = ["age", "current_pushups", "current_situps", "current_runtime",
            "training_frequency", "training_duration", "adherence_pct"]

X = pd.DataFrame({
    "age": age, "current_pushups": current_pushups,
    "current_situps": current_situps, "current_runtime": current_runtime,
    "training_frequency": training_frequency,
    "training_duration": training_duration, "adherence_pct": adherence_pct,
})

models = {
    "pushups": LinearRegression().fit(X, future_pushups),
    "situps": LinearRegression().fit(X, future_situps),
    "run_seconds": LinearRegression().fit(X, future_runtime),
}

joblib.dump({"features": FEATURES, "models": models}, "ippt_models.joblib")
print("Saved ippt_models.joblib")
