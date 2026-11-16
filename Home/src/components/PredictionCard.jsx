import { useEffect, useState } from 'react';
import { getPrediction } from '../api/predictApi.js';
import { formatRunTime } from '../utils/format.js';
import './PredictionCard.css';

// The app does not collect these four yet, so the card uses demo values.
// Replace them with the user's real answers once the intake form asks.
const DEMO_DETAILS = {
  age: 22,
  training_frequency: 4,
  training_duration: 6,
  adherence_pct: 90,
};

// Shows the model's estimate of the user's future station results.
// stations: { pushUps, sitUps, runSeconds } from the Home page.
export default function PredictionCard({ stations }) {
  const [result, setResult] = useState(null);
  const [failed, setFailed] = useState(false);

  // Ask the model again whenever the stations change (after a short pause)
  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(() => {
      getPrediction({
        ...DEMO_DETAILS,
        current_pushups: stations.pushUps,
        current_situps: stations.sitUps,
        current_runtime: stations.runSeconds,
      })
        .then((data) => {
          if (!cancelled) {
            setResult(data);
            setFailed(false);
          }
        })
        .catch(() => {
          if (!cancelled) setFailed(true);
        });
    }, 400);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [stations.pushUps, stations.sitUps, stations.runSeconds]);

  return (
    <section className="card prediction-card">
      <div className="prediction-card__top">
        <h2 className="section-label">Predicted results</h2>
        <span className="prediction-card__badge">Beta</span>
      </div>

      {failed && (
        <p className="prediction-card__status" role="alert">
          Prediction is unavailable right now.
        </p>
      )}

      {!failed && !result && (
        <p className="prediction-card__status">Loading…</p>
      )}

      {!failed && result && (
        <>
          <div className="prediction-card__grid">
            <div className="prediction-card__tile">
              <span className="prediction-card__value">{result.predicted_pushups}</span>
              <span className="prediction-card__label">Push-ups</span>
            </div>
            <div className="prediction-card__tile">
              <span className="prediction-card__value">{result.predicted_situps}</span>
              <span className="prediction-card__label">Sit-ups</span>
            </div>
            <div className="prediction-card__tile">
              <span className="prediction-card__value">
                {formatRunTime(result.predicted_run_seconds)}
              </span>
              <span className="prediction-card__label">2.4 km</span>
            </div>
          </div>

          <p className="prediction-card__note">{result.note}</p>
          <p className="prediction-card__note">
            Demo details used: age {DEMO_DETAILS.age}, {DEMO_DETAILS.training_frequency} sessions
            a week for {DEMO_DETAILS.training_duration} weeks, {DEMO_DETAILS.adherence_pct}% adherence.
          </p>
        </>
      )}
    </section>
  );
}
