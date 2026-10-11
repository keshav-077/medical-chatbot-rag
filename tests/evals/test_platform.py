"""Rule tests that do not call external APIs."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("FLASK_ENV", "development")

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
        self.assertIn("ingest", response.get_json())


if __name__ == "__main__":
    unittest.main()
