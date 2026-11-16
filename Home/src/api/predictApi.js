// Calls the backend's /predict route (the predictive model).
// Set VITE_API_URL when the backend is deployed. Locally it falls back to
// the Flask dev server, which serves the API under /api.
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// values needs: age, current_pushups, current_situps, current_runtime
// (seconds), training_frequency, training_duration, adherence_pct
export async function getPrediction(values) {
  const res = await fetch(`${BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(values),
  });
  if (!res.ok) throw new Error('Could not load prediction');
  return res.json();
}
