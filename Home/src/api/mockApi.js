const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

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
    monthly: [
      { label: 'Jan', score: 58 }, { label: 'Feb', score: 63 }, { label: 'Mar', score: 61 },
      { label: 'Apr', score: 67 }, { label: 'May', score: 66 }, { label: 'Jun', score: 72 },
      { label: 'Jul', score: null }, { label: 'Aug', score: null }, { label: 'Sep', score: null },
      { label: 'Oct', score: null }, { label: 'Nov', score: null }, { label: 'Dec', score: null },
    ],
    daily: Array.from({ length: 30 }, (_, i) => {
      const day = i + 1;
      const scores = { 1: 66, 5: 68, 10: 67, 15: 70, 20: 71, 25: 72 };
      return { label: String(day), score: scores[day] ?? null };
    }),
    stations: {
      runSeconds: { previous: 730, current: 690 },
      pushUps: { previous: 37, current: 38 },
      sitUps: { previous: 42, current: 40 },
    },
  },
};

export async function getHomeData() {
  await wait(400);
  return structuredClone({ user: db.user, score: db.score, stations: db.stations });
}

export async function updateStations(stations) {
  await wait(300);
  db.stations = { ...stations };
  return structuredClone(db.stations);
}

export async function getTrainingPlan() {
  await wait(400);
  return structuredClone({ username: db.user.username, ...db.plan });
}

export async function setDayDone(day, done) {
  await wait(200);
  const item = db.plan.week.find((d) => d.day === day);
  if (!item) throw new Error(`No session on ${day}`);
  item.done = done;
  return structuredClone(item);
}

export async function requestPlanChange({ reasons, other }) {
  await wait(800);
  console.log('Plan change requested:', { reasons, other });
  db.plan.week = db.plan.week.map((d) => ({ ...d, done: false }));
  return structuredClone({ username: db.user.username, ...db.plan });
}

export async function getStats() {
  await wait(400);
  return structuredClone({ username: db.user.username, ...db.stats });
}
