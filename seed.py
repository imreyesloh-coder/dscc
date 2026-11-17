"""
Demo data created the first time the app starts on an empty database, so the
site has something to show without a login or sign-up flow.

Scores are never stored: they are worked out from these station readings with
the official tables, so the demo can never disagree with the scoring code.
"""

from datetime import datetime, time, timedelta, timezone

from models import Plan, Result, User, db
from services import SGT, today_sg

DEMO_USERNAME = "Zane"

# (days before today, push-ups, sit-ups, 2.4 km seconds)
_HISTORY = [
    (150, 28, 30, 800),
    (120, 30, 32, 790),
    (90, 31, 34, 780),
    (60, 32, 36, 770),
    (40, 33, 37, 760),
    (25, 34, 38, 755),
    (12, 34, 40, 750),
    (0, 36, 42, 730),
]

# week -> (interval reps, easy run km, tempo time in seconds, push-up reps per set)
_WEEKS = {
    1: (6, 4.0, 705, 18),
    2: (7, 4.4, 700, 20),
    3: (8, 4.8, 695, 22),
    4: (5, 3.0, 690, 24),
}


def _session(week, day, kind, title, **fields):
    return {"session_id": f"w{week}-{day.lower()}", "day": day, "type": kind, "title": title, **fields}


def _demo_plan():
    weeks = []
    for number, (reps, easy_km, tempo_sec, pushup_reps) in _WEEKS.items():
        sessions = [
            _session(number, "Mon", "interval", "Interval run", reps=reps, rep_distance_m=400,
                     rep_target_time_sec=115, rest_time_sec=90, target_heart_rate_bpm="165-180"),
            _session(number, "Tue", "strength", "Push-up sets", rest_time_sec=60,
                     exercises=[{"name": "Push-ups", "sets": 5, "target_reps": pushup_reps}]),
            _session(number, "Wed", "run_steady", "Easy run", distance_km=easy_km,
                     target_heart_rate_bpm="135-150"),
            _session(number, "Thu", "strength", "Sit-ups & core", rest_time_sec=60,
                     exercises=[{"name": "Sit-ups", "sets": 4, "target_reps": 30},
                                {"name": "Leg raises", "sets": 3, "target_reps": 15}]),
            _session(number, "Fri", "run_steady", "Tempo run", distance_km=2.4,
                     target_time_sec=tempo_sec, target_heart_rate_bpm="160-172"),
        ]
        weeks.append({"week_number": number, "sessions": sessions})

    # Monday and Tuesday of week 1 already done for demo
    weeks[0]["sessions"][0]["done"] = True
    weeks[0]["sessions"][1]["done"] = True

    return {
        "duration_weeks": len(weeks),
        "goal": {"target_award": "Silver", "target_score": 75},
        "focus": {
            "station": "2.4 km run",
            "reason": "Your weakest station right now",
            "goal": "11:30",
            "current": "12:10",
        },
        "explanation": (
            "Your 2.4 km run is your weakest station, about 40 seconds off your 11:30 target, "
            "while push-ups and sit-ups are closer to their ceilings. So three of this week's "
            "five sessions are runs: intervals to build speed, an easy run for endurance, and "
            "a tempo run to practise goal pace. Push-ups and sit-ups get one session each so "
            "they don't slip."
        ),
        "weeks": weeks,
    }


def seed_demo_data():
    if User.query.first() is not None:
        return

    today = today_sg()
    user = User(
        username=DEMO_USERNAME,
        age=20,
        height_cm=175,
        weight_kg=68,
        pushups_baseline=_HISTORY[0][1],
        situps_baseline=_HISTORY[0][2],
        run_2_4km_baseline_sec=_HISTORY[0][3],
    )
    db.session.add(user)
    db.session.flush()

    for days_ago, pushups, situps, run_seconds in _HISTORY:
        db.session.add(
            Result(user_id=user.id, taken_on=today - timedelta(days=days_ago),
                   pushups=pushups, situps=situps, run_seconds=run_seconds)
        )

    # The plan starts on this week's Monday, so "Plan for the week" is always week 1.
    monday = today - timedelta(days=today.weekday())
    started = datetime.combine(monday, time(0, 0), tzinfo=SGT).astimezone(timezone.utc)
    db.session.add(
        Plan(user_id=user.id, status="active", plan_json=_demo_plan(),
             created_at=started.replace(tzinfo=None))
    )
    db.session.commit()
