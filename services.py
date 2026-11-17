"""
Glue between the database, the IPPT scoring tables and the JSON shapes the
React app expects (see Home/src/api/mockApi.js for the contract).
"""

import calendar
from datetime import datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from sqlalchemy.orm.attributes import flag_modified

from claude_client import generate_plan
from ippt_scoring import get_total_score
from models import Plan, Result, User, db

SGT = ZoneInfo("Asia/Singapore")
DEFAULT_AGE = 20            # used when a user has no age on file
DEFAULT_RUN_SECONDS = 720   # 12:00, only used when a user has no results at all
DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DEFAULT_TITLES = {
    "run_steady": "Steady run",
    "interval": "Interval run",
    "strength": "Strength session",
    "rest": "Rest day",
}
EMPTY_FOCUS = {"station": "Your plan", "reason": "", "goal": "", "current": ""}


# users, dates, scoring 

def today_sg():
    return datetime.now(SGT).date()


def get_demo_user():
    """The app has no login yet, so every request is about the first user."""
    return User.query.order_by(User.id).first_or_404()


def active_plan(user):
    return (
        Plan.query.filter_by(user_id=user.id, status="active")
        .order_by(Plan.id.desc())
        .first()
    )


def _age(user):
    return user.age or DEFAULT_AGE


def _points(user, result):
    return get_total_score(_age(user), result.pushups, result.situps, result.run_seconds)


def _total(user, result):
    return _points(user, result)["total_score"]


def _stations(result):
    return {"pushUps": result.pushups, "sitUps": result.situps, "runSeconds": result.run_seconds}


def _recent_results(user, limit):
    return (
        Result.query.filter_by(user_id=user.id)
        .order_by(Result.taken_on.desc())
        .limit(limit)
        .all()
    )


def _baseline(user):
    """Stand-in result for a user who has not saved any station readings yet."""
    return SimpleNamespace(
        pushups=user.pushups_baseline or 0,
        situps=user.situps_baseline or 0,
        run_seconds=user.run_2_4km_baseline_sec or DEFAULT_RUN_SECONDS,
        taken_on=today_sg(),
    )


def _fmt_mmss(seconds):
    seconds = int(round(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def current_summary(user):
    """Derived text for the AI. It sees points, never the scoring tables."""
    rows = _recent_results(user, 1)
    result = rows[0] if rows else _baseline(user)
    p = _points(user, result)
    return (
        f"Current stations (latest test): push-ups {result.pushups} ({p['pushup_score']}/25 pts), "
        f"sit-ups {result.situps} ({p['situp_score']}/25 pts), "
        f"2.4 km run {_fmt_mmss(result.run_seconds)} ({p['run_score']}/50 pts). "
        f"Total {p['total_score']}/100."
    )


# Home

def build_home(user):
    rows = _recent_results(user, 2) or [_baseline(user)]
    current = rows[0]
    previous = rows[1] if len(rows) > 1 else current
    return {
        "user": {"username": user.username or "Athlete"},
        "score": {"current": _total(user, current), "previous": _total(user, previous)},
        "stations": _stations(current),
    }


def _read_int(data, key, low, high):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{key} must be a whole number")
    value = int(value)
    if not low <= value <= high:
        raise ValueError(f"{key} must be between {low} and {high}")
    return value


def save_stations(user, data):
    """Saves today's reading. Tapping the steppers all day updates one row
    for today instead of creating one row per tap."""
    pushups = _read_int(data, "pushUps", 0, 99)
    situps = _read_int(data, "sitUps", 0, 99)
    run_seconds = _read_int(data, "runSeconds", 300, 3600)

    today = today_sg()
    result = Result.query.filter_by(user_id=user.id, taken_on=today).first()
    if result is None:
        result = Result(user_id=user.id, taken_on=today)
        db.session.add(result)
    result.pushups, result.situps, result.run_seconds = pushups, situps, run_seconds
    db.session.commit()
    return _stations(result)


# Statistics

def build_stats(user):
    rows = (
        Result.query.filter_by(user_id=user.id).order_by(Result.taken_on).all()
    ) or [_baseline(user)]
    scored = [(r, _total(user, r)) for r in rows]

    best = max(scored, key=lambda x: (x[1], x[0].taken_on))
    worst = min(scored, key=lambda x: (x[1], x[0].taken_on))

    today = today_sg()
    by_month = {m: [] for m in range(1, 13)}
    by_day = {}
    for result, score in scored:
        if result.taken_on.year == today.year:
            by_month[result.taken_on.month].append(score)
            if result.taken_on.month == today.month:
                by_day[result.taken_on.day] = score

    monthly = [
        {
            "label": MONTH_LABELS[m - 1],
            # average of that month's tests, rounded half up
            "score": int(sum(by_month[m]) / len(by_month[m]) + 0.5) if by_month[m] else None,
        }
        for m in range(1, 13)
    ]
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    daily = [{"label": str(d), "score": by_day.get(d)} for d in range(1, days_in_month + 1)]

    current = rows[-1]
    previous = rows[-2] if len(rows) > 1 else current
    return {
        "username": user.username or "Athlete",
        "highest": {"score": best[1], "when": best[0].taken_on.strftime("%B %Y")},
        "lowest": {"score": worst[1], "when": worst[0].taken_on.strftime("%B %Y")},
        "monthly": monthly,
        "daily": daily,
        "stations": {
            "runSeconds": {"previous": previous.run_seconds, "current": current.run_seconds},
            "pushUps": {"previous": previous.pushups, "current": current.pushups},
            "sitUps": {"previous": previous.situps, "current": current.situps},
        },
    }


# Training plan

def _day_key(day):
    return str(day or "").strip()[:3].title()


def _day_rank(day):
    key = _day_key(day)
    return DAY_ORDER.index(key) if key in DAY_ORDER else len(DAY_ORDER)


def _week_index(plan, week_count):
    """Which week of the plan today falls in (the plan starts the day it was made)."""
    created = plan.created_at or datetime.utcnow()
    start = created.replace(tzinfo=timezone.utc).astimezone(SGT).date()
    index = (today_sg() - start).days // 7
    return max(0, min(index, week_count - 1))


def _visible_sessions(plan):
    """This week's sessions, in day order, rest days left out. These are the
    live dicts inside plan_json, so editing them edits the plan."""
    weeks = (plan.plan_json or {}).get("weeks") or []
    if not weeks:
        return []
    sessions = weeks[_week_index(plan, len(weeks))].get("sessions") or []
    sessions = [s for s in sessions if s.get("type") != "rest"]
    return sorted(sessions, key=lambda s: _day_rank(s.get("day")))


def _heart_rate_text(session):
    hr = session.get("target_heart_rate_bpm")
    if not hr:
        return None
    hr = str(hr).strip()
    return f"HR {hr}" if "bpm" in hr.lower() else f"HR {hr} bpm"


def _session_detail(session):
    kind = session.get("type")
    main = None

    if kind == "interval":
        reps, dist = session.get("reps"), session.get("rep_distance_m")
        if reps and dist:
            main = f"{reps} × {dist} m"
            if session.get("rep_target_time_sec"):
                main += f" in {_fmt_mmss(session['rep_target_time_sec'])}"
            if session.get("rest_time_sec"):
                main += f", {session['rest_time_sec']} s rest"
    elif kind == "run_steady":
        if session.get("distance_km"):
            main = f"{session['distance_km']:g} km"
            if session.get("target_time_sec"):
                main += f" in {_fmt_mmss(session['target_time_sec'])}"
    elif kind == "strength":
        parts = []
        for ex in session.get("exercises") or []:
            name = (ex.get("name") or "").lower()
            if ex.get("sets") and ex.get("target_reps"):
                parts.append(f"{ex['sets']} × {ex['target_reps']} {name}".strip())
            elif name:
                parts.append(name)
        if parts:
            main = ", ".join(parts)
            if session.get("rest_time_sec"):
                main += f", {session['rest_time_sec']} s rest"

    return " · ".join(p for p in (main, _heart_rate_text(session)) if p)


def _session_item(session):
    return {
        "day": _day_key(session.get("day")),
        "title": session.get("title") or DEFAULT_TITLES.get(session.get("type"), "Session"),
        "detail": _session_detail(session),
        "done": bool(session.get("done")),
    }


def plan_to_frontend(plan):
    data = plan.plan_json or {}
    return {
        "username": (plan.user.username if plan.user else None) or "Athlete",
        "focus": {**EMPTY_FOCUS, **(data.get("focus") or {})},
        "week": [_session_item(s) for s in _visible_sessions(plan)],
        "explanation": data.get("explanation") or "",
    }


def set_day_done(plan, day, done):
    key = _day_key(day)
    matches = [s for s in _visible_sessions(plan) if _day_key(s.get("day")) == key]
    if not matches:
        raise LookupError(f"No session on {key}")
    for session in matches:
        session["done"] = bool(done)
    flag_modified(plan, "plan_json")
    db.session.commit()
    return _session_item(matches[0])


def request_plan_change(user, reasons, other):
    """Asks Claude for a replacement plan. The old plan is only archived once
    the new one has been generated, so a failed call changes nothing."""
    reasons = [r.strip()[:100] for r in (reasons or []) if isinstance(r, str) and r.strip()][:10]
    other = other.strip()[:500] if isinstance(other, str) else ""
    if not reasons and not other:
        raise ValueError("Tell us what you would like to change.")

    feedback = ""
    if reasons:
        feedback += "Reasons: " + "; ".join(reasons) + "."
    if other:
        feedback += f"{' ' if feedback else ''}Other comments: {other}"

    old = active_plan(user)
    new_data = generate_plan(
        user,
        current_summary=current_summary(user),
        feedback=feedback,
        previous_plan=old.plan_json if old else None,
    )

    if old:
        old.status = "archived"
    plan = Plan(user_id=user.id, plan_json=new_data, status="active")
    db.session.add(plan)
    db.session.commit()
    return plan_to_frontend(plan)
