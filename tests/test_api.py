"""
Run from the repo root:  python -m unittest discover -s tests -v

Claude is mocked, so these tests never call the API or cost anything.
"""

import logging
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.disable(logging.CRITICAL)
os.environ["AI_RATE_LIMIT"] = "3 per hour"

from app import create_app
from config import Config
from extensions import Limiter
from ippt_scoring import get_total_scoreLimiter

# What Claude's create_training_plan tool returns
FAKE_PLAN = {
    "duration_weeks": 2,
    "goal": {"target_award": "Silver", "target_score": 75},
    "focus": {"station": "2.4 km run", "reason": "Weakest station", "goal": "11:30", "current": "12:10"},
    "explanation": "Fewer sessions, since you said you lack time.",
    "weeks": [
        {"week_number": w, "sessions": [
            {"session_id": f"w{w}-mon", "day": "Mon", "title": "Easy run", "type": "run_steady",
             "distance_km": 3, "target_heart_rate_bpm": "135-150"},
            {"session_id": f"w{w}-wed", "day": "Wed", "title": "Strength", "type": "strength",
             "exercises": [{"name": "Push-ups", "sets": 4, "target_reps": 20}]},
            {"session_id": f"w{w}-fri", "day": "Fri", "title": "Rest", "type": "rest"},
        ]}
        for w in (1, 2)
    ],
}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self._db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self._db_file.name}"
        self.app = create_app()
        limiter.reset()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            from models import db
            db.session.remove()
            db.engine.dispose()
        os.unlink(self._db_file.name)

    # scoring

    def test_scoring_reads_tables(self):
        self.assertEqual(get_total_score(20, 60, 60, 510)["total_score"], 100)
        self.assertEqual(get_total_score(20, 36, 42, 730)["total_score"], 70)
        self.assertEqual(get_total_score(30, 0, 0, 2000)["total_score"], 0)

    # read endpoints match the mock's shapes

    def test_home_shape(self):
        data = self.client.get("/api/home").get_json()
        self.assertEqual(set(data), {"user", "score", "stations"})
        self.assertEqual(set(data["score"]), {"current", "previous"})
        self.assertEqual(set(data["stations"]), {"pushUps", "sitUps", "runSeconds"})

    def test_stats_shape(self):
        data = self.client.get("/api/stats").get_json()
        self.assertEqual(set(data), {"username", "highest", "lowest", "monthly", "daily", "stations"})
        self.assertEqual(len(data["monthly"]), 12)
        self.assertEqual(set(data["stations"]), {"runSeconds", "pushUps", "sitUps"})
        self.assertLessEqual(data["lowest"]["score"], data["highest"]["score"])

    def test_plan_shape(self):
        data = self.client.get("/api/plan").get_json()
        self.assertEqual(set(data), {"username", "focus", "week", "explanation"})
        self.assertEqual(set(data["focus"]), {"station", "reason", "goal", "current"})
        self.assertEqual([d["day"] for d in data["week"]], ["Mon", "Tue", "Wed", "Thu", "Fri"])
        for day in data["week"]:
            self.assertEqual(set(day), {"day", "title", "detail", "done"})
            self.assertTrue(day["detail"])

    # writes

    def test_stations_save_updates_home_and_reuses_todays_row(self):
        before = len(self.client.get("/api/stats").get_json()["daily"])
        for pushups in (37, 38, 39):  # three taps on the stepper
            r = self.client.put("/api/stations", json={"pushUps": pushups, "sitUps": 42, "runSeconds": 725})
            self.assertEqual(r.status_code, 200)
        home = self.client.get("/api/home").get_json()
        self.assertEqual(home["stations"], {"pushUps": 39, "sitUps": 42, "runSeconds": 725})
        self.assertEqual(home["score"]["previous"], 66)  # still yesterday's reading, not the last tap
        self.assertEqual(len(self.client.get("/api/stats").get_json()["daily"]), before)

    def test_stations_validation(self):
        bad = [
            {"pushUps": "many", "sitUps": 40, "runSeconds": 700},
            {"pushUps": 40, "sitUps": 40},
            {"pushUps": 40, "sitUps": 40, "runSeconds": 10},
            {"pushUps": 40.5, "sitUps": 40, "runSeconds": 700},
            {"pushUps": True, "sitUps": 40, "runSeconds": 700},
        ]
        for body in bad:
            self.assertEqual(self.client.put("/api/stations", json=body).status_code, 400, body)

    def test_tick_and_untick_day(self):
        r = self.client.patch("/api/plan/days/Wed", json={"done": True})
        self.assertEqual((r.status_code, r.get_json()["done"]), (200, True))
        week = self.client.get("/api/plan").get_json()["week"]
        self.assertTrue(next(d for d in week if d["day"] == "Wed")["done"])
        self.client.patch("/api/plan/days/Wed", json={"done": False})
        week = self.client.get("/api/plan").get_json()["week"]
        self.assertFalse(next(d for d in week if d["day"] == "Wed")["done"])
        self.assertEqual(self.client.patch("/api/plan/days/Sun", json={"done": True}).status_code, 404)
        self.assertEqual(self.client.patch("/api/plan/days/Mon", json={"done": "yes"}).status_code, 400)

    # plan change (Claude mocked)

    def test_plan_change_flow(self):
        calls = []

        def fake_create(**kwargs):
            calls.append(kwargs)
            block = SimpleNamespace(type="tool_use", name="create_training_plan", input=FAKE_PLAN)
            return SimpleNamespace(stop_reason="tool_use", content=[block])

        with patch("claude_client.client.messages.create", side_effect=fake_create):
            self.assertEqual(self.client.post("/api/plan/change", json={"reasons": [], "other": ""}).status_code, 400)
            r = self.client.post("/api/plan/change", json={"reasons": ["I don't have enough time"], "other": "only 3 days"})
        self.assertEqual(r.status_code, 200, r.get_json())
        plan = r.get_json()
        self.assertEqual([d["day"] for d in plan["week"]], ["Mon", "Wed"])  # rest day hidden
        self.assertEqual(plan["week"][0]["detail"], "3 km · HR 135-150 bpm")
        self.assertEqual(plan["week"][1]["detail"], "4 × 20 push-ups")
        self.assertFalse(any(d["done"] for d in plan["week"]))  # ticks reset
        self.assertEqual(self.client.get("/api/plan").get_json()["explanation"], FAKE_PLAN["explanation"])

        prompt = calls[0]["messages"][0]["content"]
        self.assertIn("don't have enough time", prompt)
        self.assertIn("Total 70/100", prompt)  # the derived summary is sent
        self.assertNotIn("<22", prompt)  # never the raw scoring tables

    def test_plan_change_failure_keeps_old_plan(self):
        before = self.client.get("/api/plan").get_json()
        with patch("claude_client.client.messages.create", side_effect=RuntimeError("boom")):
            r = self.client.post("/api/plan/change", json={"reasons": ["Too easy"], "other": ""})
        self.assertEqual(r.status_code, 502)
        self.assertEqual(self.client.get("/api/plan").get_json(), before)

    def test_truncated_plan_is_rejected(self):
        cut = SimpleNamespace(stop_reason="max_tokens", content=[])
        with patch("claude_client.client.messages.create", return_value=cut):
            r = self.client.post("/api/plan/change", json={"reasons": ["Too easy"], "other": ""})
        self.assertEqual(r.status_code, 502)

    # limits, CORS, legacy routes

    def test_rate_limit_is_json_and_only_on_claude_routes(self):
        with patch("claude_client.client.messages.create", side_effect=RuntimeError("boom")):
            codes = [self.client.post("/api/plan/change", json={"reasons": ["Too easy"]}).status_code for _ in range(6)]
        self.assertIn(429, codes)
        limited = self.client.post("/api/plan/change", json={"reasons": ["Too easy"]})
        self.assertEqual(limited.status_code, 429)
        self.assertIn("error", limited.get_json())
        self.assertEqual(self.client.get("/api/home").status_code, 200)

    def test_cors_only_allows_listed_origins(self):
        ok = self.client.get("/api/health", headers={"Origin": "https://notsting.github.io"})
        self.assertEqual(ok.headers.get("Access-Control-Allow-Origin"), "https://notsting.github.io")
        other = self.client.get("/api/health", headers={"Origin": "https://evil.example"})
        self.assertIsNone(other.headers.get("Access-Control-Allow-Origin"))
        pre = self.client.options("/api/plan/days/Mon", headers={
            "Origin": "https://notsting.github.io", "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "content-type"})
        self.assertEqual(pre.status_code, 200)
        self.assertIn("PATCH", pre.headers.get("Access-Control-Allow-Methods", ""))

    def test_old_routes_still_work(self):
        r = self.client.post("/api/users", json={
            "username": "Ali", "age": 24, "height_cm": 170, "weight_kg": 65,
            "pushups_baseline": 30, "situps_baseline": 35, "run_2_4km_baseline_sec": 800})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.get("/api/home").get_json()["user"]["username"], "Zane")  # demo user unchanged
        p = self.client.post("/api/predict", json={
            "age": 20, "current_pushups": 36, "current_situps": 42, "current_runtime": 730,
            "training_frequency": 4, "training_duration": 6, "adherence_pct": 80})
        self.assertEqual(p.status_code, 200)
        self.assertIn("predicted_run_time", p.get_json())


if __name__ == "__main__":
    unittest.main()
