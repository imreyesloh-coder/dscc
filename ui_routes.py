"""Endpoints used by the React app (Home/src/api/realApi.js)."""

from flask import Blueprint, current_app, jsonify, request

from extensions import ai_limit
from services import (
    active_plan,
    build_home,
    build_stats,
    get_demo_user,
    plan_to_frontend,
    request_plan_change,
    save_stations,
    set_day_done,
)

ui = Blueprint("ui", __name__)


@ui.get("/health")
def health():
    return jsonify({"ok": True})


@ui.get("/home")
def home():
    return jsonify(build_home(get_demo_user()))


@ui.put("/stations")
def stations():
    try:
        return jsonify(save_stations(get_demo_user(), request.get_json(silent=True) or {}))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@ui.get("/plan")
def plan():
    current = active_plan(get_demo_user())
    if current is None:
        return jsonify({"error": "No active plan yet."}), 404
    return jsonify(plan_to_frontend(current))


@ui.patch("/plan/days/<day>")
def plan_day(day):
    current = active_plan(get_demo_user())
    if current is None:
        return jsonify({"error": "No active plan yet."}), 404
    done = (request.get_json(silent=True) or {}).get("done")
    if not isinstance(done, bool):
        return jsonify({"error": "done must be true or false"}), 400
    try:
        return jsonify(set_day_done(current, day, done))
    except LookupError as e:
        return jsonify({"error": str(e)}), 404


@ui.post("/plan/change")
@ai_limit
def plan_change():
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(request_plan_change(get_demo_user(), data.get("reasons"), data.get("other")))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        current_app.logger.exception("Plan change failed")
        return jsonify(
            {"error": "AI plan generation is temporarily unavailable, please try again shortly."}
        ), 502


@ui.get("/stats")
def stats():
    return jsonify(build_stats(get_demo_user()))
