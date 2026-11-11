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

  plan: {
    focus: {
      station: '2.4 km run',
      reason: 'Your weakest station right now',
      goal: '10:30',
      current: '11:30',
    },
    week: [
      { day: 'Mon', title: 'Interval run', detail: '6 × 400 m at goal pace, 90 s rest', done: true },
      { day: 'Tue', title: 'Push-up sets', detail: '5 sets to near-failure, 60 s rest', done: true },
      { day: 'Wed', title: 'Easy run', detail: '4 km at a conversational pace', done: false },
      { day: 'Thu', title: 'Sit-ups & core', detail: '4 × 30 sit-ups, 3 × 45 s plank', done: false },
      { day: 'Fri', title: 'Tempo run', detail: '2.4 km at 10:45 pace', done: false },
    ],
    explanation:
      "Your 2.4 km run is about a minute off your 10:30 target, while push-ups and sit-ups are " +
      "already close to their goals. So three of this week's five sessions are runs: intervals " +
      'to build speed, an easy run for endurance, and a tempo run to practise goal pace. ' +
      "Push-ups and sit-ups get one session each so they don't slip.",
  },
 
  stats: {
    highest: { score: 72, when: 'June 2026' },
    lowest: { score: 58, when: 'January 2026' },
    // score: null = no test that month yet
    monthly: [
      { label: 'Jan', score: 58 }, { label: 'Feb', score: 63 }, { label: 'Mar', score: 61 },
      { label: 'Apr', score: 67 }, { label: 'May', score: 66 }, { label: 'Jun', score: 72 },
      { label: 'Jul', score: null }, { label: 'Aug', score: null }, { label: 'Sep', score: null },
      { label: 'Oct', score: null }, { label: 'Nov', score: null }, { label: 'Dec', score: null },
    ],
    // One entry per day of the current month
    daily: Array.from({ length: 30 }, (_, i) => {
      const day = i + 1;
      const scores = { 1: 66, 5: 68, 10: 67, 15: 70, 20: 71, 25: 72 };
      return { label: String(day), score: scores[day] ?? null };
    }),
    // previous = second-latest test, current = latest test
    stations: {
      runSeconds: { previous: 730, current: 690 },
      pushUps: { previous: 37, current: 38 },
      sitUps: { previous: 42, current: 40 },
    },
  },
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
