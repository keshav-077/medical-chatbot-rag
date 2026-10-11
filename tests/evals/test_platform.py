"""Rule tests that do not call external APIs."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("FLASK_ENV", "development")
os.environ["BLOOM_INLINE_MISSIONS"] = "0"
os.environ["BLOOM_FORCE_DIGEST"] = "0"

from orchestration.graphs.common import verify_node
from orchestration.intent import classify_intent
from orchestration.safety import is_emergency, safety_node
from tools.drugs import find_monograph, interaction_notes


class _Row:
    def __init__(self, generic_name, brand_names=""):
        self.generic_name = generic_name
        self.brand_names = brand_names


class SafetyTests(unittest.TestCase):
    def test_chest_pain_is_emergency(self):
        result = safety_node({"message": "I have chest pain and I can't breathe"})
        self.assertTrue(result["skip_rag"])
        self.assertEqual(result["risk_level"], "emergency")
        self.assertIn("112", result["answer"])
        self.assertIn("will not give casual", result["answer"])

    def test_ordinary_question_is_not_emergency(self):
        self.assertFalse(is_emergency("What is paracetamol used for?"))


class IntentTests(unittest.TestCase):
    def test_drug_name_routes_to_medication(self):
        self.assertEqual(
            classify_intent("what is in crocin", ["paracetamol", "crocin"]),
            "medication",
        )

    def test_hospital_routes_to_care(self):
        self.assertEqual(classify_intent("hospital near me", []), "care")


class DrugTests(unittest.TestCase):
    def test_brand_match(self):
        rows = [_Row("paracetamol", "Crocin, Dolo")]
        found = find_monograph("Is Crocin the same as paracetamol?", rows)
        self.assertEqual(found.generic_name, "paracetamol")

    def test_interaction_with_profile(self):
        notes = interaction_notes("metformin", ["alcohol at night"])
        self.assertTrue(notes)

    def test_verify_strips_invented_dose(self):
        result = verify_node(
            {
                "intent": "medication",
                "answer": "You should take 500 mg tonight.",
                "context": "paracetamol 500 mg tablets",
                "citations": [{"source": "label"}],
                "disclaimer": "Confirm with a pharmacist.",
            }
        )
        self.assertNotIn("take 500 mg", result["answer"].lower())


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path(__file__).resolve().parents[2] / "instance" / "pytest_bloom.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        os.environ["DATABASE_URL"] = "sqlite:///" + db_path.as_posix()
        from app import app

        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        cls.client = app.test_client()
        cls.app = app

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["version"], "2.1.0")
        self.assertIn("embedding_provider", body)

    def test_emergency_turn_skips_casual_answer(self):
        from orchestration.graphs.main import run_turn

        with self.app.app_context():
            result = run_turn("sudden chest pain")
        self.assertEqual(result["risk_level"], "emergency")
        self.assertNotIn("three sentences", result["answer"].lower())

    def test_known_drug_has_composition_and_date(self):
        from orchestration.graphs.main import run_turn

        with self.app.app_context():
            result = run_turn("what is in paracetamol")
        self.assertIn("Composition", result["answer"])
        self.assertIn("2026-01-15", result["answer"])
        self.assertTrue(result.get("freshness"))

    def test_unknown_drug_asks_for_a_name(self):
        from orchestration.graphs.main import run_turn

        with self.app.app_context():
            result = run_turn("tell me about the medicine zzyxnotadrug")
        self.assertIn("which medicine", result["answer"].lower())

    def test_worker_ingests_in_development(self):
        response = self.client.post("/api/worker/run")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertIn("ingest", body)
        self.assertIn("missions", body)


class MissionTriggerTests(unittest.TestCase):
    def test_appointment_intent_queues_visit_pack(self):
        from missions.triggers import missions_for_turn, wants_visit_pack

        self.assertTrue(wants_visit_pack("book a doctor tomorrow", "appointment"))
        specs = missions_for_turn("book a doctor tomorrow", "appointment", 7)
        kinds = [item["kind"] for item in specs]
        self.assertIn("visit_pack", kinds)
        self.assertTrue(specs[0]["dedupe_key"].startswith("visit:7:"))

    def test_i_take_metformin_queues_med_card(self):
        from missions.triggers import missions_for_turn, wants_med_card

        self.assertTrue(wants_med_card("I take metformin at night", "medication"))
        specs = missions_for_turn("I take metformin at night", "medication", 3)
        self.assertTrue(any(item["kind"] == "med_card" for item in specs))

    def test_interaction_question_queues_huddle(self):
        from missions.triggers import wants_interaction_huddle

        self.assertTrue(
            wants_interaction_huddle("can I take ibuprofen with my metformin", "medication")
        )

    def test_emergency_queues_nothing(self):
        from missions.triggers import missions_for_turn

        self.assertEqual(missions_for_turn("chest pain", "emergency", 1), [])

    def test_no_user_queues_nothing(self):
        from missions.triggers import missions_for_turn

        self.assertEqual(missions_for_turn("book a doctor", "appointment", None), [])


class NotifyAndAqiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["BLOOM_INLINE_MISSIONS"] = "0"
        db_path = Path(__file__).resolve().parents[2] / "instance" / "pytest_bloom.db"
        os.environ["DATABASE_URL"] = "sqlite:///" + db_path.as_posix()
        from app import app
        from models import User, db

        cls.app = app
        with app.app_context():
            user = User.query.filter_by(email="notify-test@bloom.local").first()
            if user is None:
                user = User(name="Notify", email="notify-test@bloom.local")
                user.set_password("secret12")
                db.session.add(user)
                db.session.commit()
            cls.user_id = user.id

    def test_notify_writes_row_without_telegram(self):
        from models import Notification
        from services.notify import notify

        with self.app.app_context():
            before = Notification.query.filter_by(user_id=self.user_id).count()
            notify(self.user_id, "Visit pack is ready.", kind="visit_pack", push_telegram=True)
            after = Notification.query.filter_by(user_id=self.user_id).count()
            self.assertGreater(after, before)

    def test_enqueue_dedupes_same_key(self):
        from missions.enqueue import enqueue_mission
        from models import Mission

        with self.app.app_context():
            key = "visit:test-dedupe-key"
            first = enqueue_mission("visit_pack", self.user_id, payload={"message": "a"}, dedupe_key=key)
            second = enqueue_mission("visit_pack", self.user_id, payload={"message": "b"}, dedupe_key=key)
            self.assertEqual(first.id, second.id)
            self.assertEqual(Mission.query.filter_by(dedupe_key=key).count(), 1)

    def test_failed_mission_can_requeue(self):
        from missions.enqueue import enqueue_mission
        from models import Mission, db

        with self.app.app_context():
            key = "visit:test-failed-requeue"
            first = enqueue_mission("visit_pack", self.user_id, payload={"message": "a"}, dedupe_key=key)
            first.status = "failed"
            db.session.commit()
            second = enqueue_mission("visit_pack", self.user_id, payload={"message": "b"}, dedupe_key=key)
            self.assertEqual(first.id, second.id)
            self.assertEqual(second.status, "queued")
            self.assertEqual(Mission.query.filter_by(dedupe_key=key).count(), 1)

    def test_old_appointments_do_not_queue_visit_packs(self):
        from datetime import datetime, timedelta, timezone

        from missions.runner import queued_upcoming_visits
        from models import AppointmentRequest, Mission, db

        with self.app.app_context():
            old = AppointmentRequest(
                user_id=self.user_id,
                specialty="cardiology",
                reason="old checkup",
                created_at=datetime.now(timezone.utc) - timedelta(days=10),
            )
            db.session.add(old)
            db.session.commit()
            before = Mission.query.filter_by(user_id=self.user_id, kind="visit_pack").count()
            queued_upcoming_visits()
            after = Mission.query.filter_by(user_id=self.user_id, kind="visit_pack").count()
            self.assertEqual(before, after)

    def test_safety_notices_file_loads(self):
        from mcp_bloom.sources.notices import list_safety_notices

        notices = list_safety_notices()
        self.assertTrue(notices)
        self.assertTrue(any(row.get("drug") == "paracetamol" for row in notices))

    def test_aqi_skipped_without_coords(self):
        from services.location import get_user_location

        with self.app.app_context():
            self.assertIsNone(get_user_location(None))
            self.assertIsNone(get_user_location(999999))

    def test_safety_screen_still_wins(self):
        from mcp_bloom.registry import safety_screen

        result = safety_screen("I have chest pain")
        self.assertTrue(result["emergency"])
        self.assertIn("112", result["answer"])


class HuddleSafetyTests(unittest.TestCase):
    def test_reviewer_rejects_diagnosis(self):
        from missions.huddles.safety_review import review_lab_text

        ok, reason = review_lab_text("You have diabetes based on this report.")
        self.assertFalse(ok)
        self.assertIn("Diagnosis", reason)

    def test_reviewer_rejects_dose(self):
        from missions.huddles.safety_review import review_lab_text

        ok, _reason = review_lab_text("Take 500 mg tonight after food.")
        self.assertFalse(ok)

    def test_reviewer_allows_plain_explanation(self):
        from missions.huddles.safety_review import review_lab_text

        ok, reason = review_lab_text(
            "Hemoglobin is a number on the report. Ask your doctor what it means for you."
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")


if __name__ == "__main__":
    unittest.main()
