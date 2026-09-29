from datetime import datetime
 
from flask_sqlalchemy import SQLAlchemy
 
db = SQLAlchemy()
 
 
class User(db.Model):
    __tablename__ = "users"
 
    id = db.Column(db.Integer, primary_key=True)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    pushups_baseline = db.Column(db.Integer)
    situps_baseline = db.Column(db.Integer)
    run_2_4km_baseline_sec = db.Column(db.Integer)
    test_date = db.Column(db.Date)
    injury_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    plans = db.relationship("Plan", backref="user", lazy=True)
 
 
class Plan(db.Model):
    __tablename__ = "plans"
 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="active")  # active/ completed/ archived
    plan_json = db.Column(db.JSON, nullable=False)
 
    checkins = db.relationship("Checkin", backref="plan", lazy=True)
 
 
class Checkin(db.Model):
    __tablename__ = "checkins"
 
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    resulting_adjustment = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 