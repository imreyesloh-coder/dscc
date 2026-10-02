/*
 * MOCK API. Every page gets its data from this file only.
 *
 * When the back end is ready, keep the function names the same and swap
 * each body for a real request, e.g.
 *
 *   export async function getHomeData() {
 *     const res = await fetch(`${import.meta.env.VITE_API_URL}/home`);
 *     if (!res.ok) throw new Error('Could not load home data');
 *     return res.json();
 *   }
 *
 * Agree the JSON shapes below with your back-end teammate so nothing else
 * in the app has to change.
 */

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Pretend database
let db = {
  user: { username: 'Zane' },
  score: { current: 70, previous: 66 },
  stations: { pushUps: 57, sitUps: 26, runSeconds: 710 },
};

/**
 * Shape returned:
 * {
 *   user:     { username: string },
 *   score:    { current: number, previous: number },
 *   stations: { pushUps: number, sitUps: number, runSeconds: number }
 * }
 */
export async function getHomeData() {
  await wait(400); // fake network delay, so you can see the loading state
  return structuredClone(db);
}

/** Saves updated station results. Returns the saved stations object. */
export async function updateStations(stations) {
  await wait(300);
  db.stations = { ...stations };
  return structuredClone(db.stations);
}
