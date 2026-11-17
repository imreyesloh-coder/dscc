from flask import Blueprint, jsonify, request
from sqlalchemy.orm.attributes import flag_modified
 
from claude_client import adjust_plan, generate_plan
from extensions import ai_limit
from models import Checkin, Plan, Result, User, db
from predictive_model import predict_future_scores
from services import current_summary, today_sg
 
api = Blueprint("api", __name__)
 
 
@api.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    user = User(
        username=data.get("username"),
        age=data.get("age"),
        height_cm=data["height_cm"],
        weight_kg=data["weight_kg"],
        pushups_baseline=data.get("pushups_baseline"),
        situps_baseline=data.get("situps_baseline"),
        run_2_4km_baseline_sec=data.get("run_2_4km_baseline_sec"),
        test_date=data.get("test_date"),
        injury_notes=data.get("injury_notes"),
    )
    db.session.add(user)
    db.session.flush()
    # The baselines are the user's first reading, so the stats pages have something to show.
    if None not in (user.pushups_baseline, user.situps_baseline, user.run_2_4km_baseline_sec):
        db.session.add(
            Result(
                user_id=user.id,
                taken_on=today_sg(),
                pushups=user.pushups_baseline,
                situps=user.situps_baseline,
                run_seconds=user.run_2_4km_baseline_sec,
            )
        )
    db.session.commit()
    return jsonify({"user_id": user.id}), 201
 
 
@api.route("/users/<int:user_id>/plans", methods=["POST"])
@ai_limit
def create_plan(user_id):
    user = User.query.get_or_404(user_id)
 
    try:
        plan_data = generate_plan(user, current_summary=current_summary(user))
    except Exception:
        return jsonify(
            {"error": "AI plan generation is temporarily unavailable, please try again shortly."}
        ), 502
 
    plan = Plan(user_id=user.id, plan_json=plan_data, status="active")
    db.session.add(plan)
    db.session.commit()
    return jsonify({"plan_id": plan.id, "plan": plan.plan_json}), 201
 
 
@api.route("/plans/<int:plan_id>", methods=["GET"])
def get_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    return jsonify({"plan_id": plan.id, "status": plan.status, "plan": plan.plan_json})
 
 
@api.route("/plans/<int:plan_id>/checkins", methods=["POST"])
@ai_limit
def create_checkin(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    message = request.get_json()["message"]
 
    try:
        result = adjust_plan(plan.plan_json, message)
    except Exception:
        return jsonify(
            {"error": "AI check-in processing is temporarily unavailable, please try again shortly."}
        ), 502

    sessions_by_id = {
        session["session_id"]: session
        for week in plan.plan_json["weeks"]
        for session in week["sessions"]
    }
    for adj in result["adjustments"]:
        session = sessions_by_id.get(adj["session_id"])
        if session is None:
            continue
        session["status"] = adj["new_status"]
        session["adjustment"] = {"reason": adj["reason"], "source": "checkin"}
        if adj.get("changes"):
            session.update(adj["changes"])
    flag_modified(plan, "plan_json")
 
    checkin = Checkin(
        plan_id=plan.id,
        user_id=plan.user_id,
        message=message,
        resulting_adjustment=result["adjustments"],
    )
    db.session.add(checkin)
    db.session.commit()
 
    return jsonify({"reply": result["reply_to_user"], "plan": plan.plan_json})


@api.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(predict_future_scores(data))
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


 
