const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:5000/api').replace(/\/+$/, '');

async function request(path, { body, ...options } = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    ...(body !== undefined && {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.error) message = data.error;
    } catch {
    }
    throw new Error(message);
  }
  return res.json();
}

/* Home */

export const getHomeData = () => request('/home');

export const updateStations = (stations) =>
  request('/stations', { method: 'PUT', body: stations });

/* Training plan */

export const getTrainingPlan = () => request('/plan');

export const setDayDone = (day, done) =>
  request(`/plan/days/${encodeURIComponent(day)}`, { method: 'PATCH', body: { done } });

// The back end asks Claude for a new plan, which can take a while.
export const requestPlanChange = ({ reasons, other }) =>
  request('/plan/change', { method: 'POST', body: { reasons, other } });

/* Statistics */

export const getStats = () => request('/stats');

/* Wake-up */

export function wakeBackend() {
  fetch(`${API_URL}/health`).catch(() => {});
}
