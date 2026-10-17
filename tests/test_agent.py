"""Unit tests for the Skill Path AI knowledge agent and Flask routes."""

import json
import os
import sys
import unittest

# Ensure the project root is importable when tests run from the tests folder.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import app, knowledge_agent  # noqa: E402
from utils.knowledge_agent import KnowledgeAgent, KnowledgeAgentError  # noqa: E402


class KnowledgeAgentTests(unittest.TestCase):
    """Tests for the knowledge retrieval agent."""

    def setUp(self):
        self.agent = KnowledgeAgent(
            knowledge_path=os.path.join(PROJECT_ROOT, "data", "knowledge.json"),
            similarity_threshold=0.25,
        )
        self.agent.load()

    def test_question_matches_existing_note(self):
        """A question about a known topic should match its note."""
        result = self.agent.answer("What is overfitting?")
        self.assertTrue(result["match_found"])
        self.assertIsNotNone(result["note"])
        self.assertGreaterEqual(result["score"], self.agent.similarity_threshold)
        self.assertIn("overfit", (result["answer"] or "").lower())

    def test_unknown_question_triggers_fallback(self):
        """An unrelated question should not be presented as a match."""
        result = self.agent.answer("What is the boiling point of mercury?")
        self.assertFalse(result["match_found"])
        self.assertEqual(result["score"], 0.0)
        self.assertIn("could not find", (result["answer"] or "").lower())

    def test_empty_question(self):
        """An empty question should return a helpful message without a match."""
        result = self.agent.answer("")
        self.assertFalse(result["match_found"])
        self.assertIsNone(result["note"])
        self.assertIn("Please enter a question", result["answer"])

    def test_draft_note_warning(self):
        """A draft note should include a warning."""
        # The AI/ML learning roadmap note is marked as "draft".
        result = self.agent.answer("What is the AI ML learning roadmap?")
        self.assertTrue(result["match_found"])
        self.assertIsNotNone(result["note"])
        self.assertEqual(result["note"]["status"], "draft")
        self.assertIsNotNone(result["warning"])
        self.assertIn("draft", result["warning"].lower())

    def test_missing_knowledge_file(self):
        """A missing knowledge file should raise KnowledgeAgentError."""
        bad_agent = KnowledgeAgent(
            knowledge_path=os.path.join(PROJECT_ROOT, "data", "does_not_exist.json"),
            similarity_threshold=0.25,
        )
        with self.assertRaises(KnowledgeAgentError):
            bad_agent.load()

    def test_malformed_json(self):
        """Malformed JSON should raise KnowledgeAgentError."""
        bad_path = os.path.join(PROJECT_ROOT, "data", "bad.json")
        with open(bad_path, "w", encoding="utf-8") as fh:
            fh.write("{not valid json")
        bad_agent = KnowledgeAgent(
            knowledge_path=bad_path,
            similarity_threshold=0.25,
        )
        try:
            with self.assertRaises(KnowledgeAgentError):
                bad_agent.load()
        finally:
            if os.path.exists(bad_path):
                os.remove(bad_path)

    def test_score_is_percentage(self):
        """The score_percent field should be 0-100."""
        result = self.agent.answer("Explain supervised learning")
        self.assertTrue(result["match_found"])
        self.assertGreaterEqual(result["score_percent"], 0)
        self.assertLessEqual(result["score_percent"], 100)


class FlaskRouteTests(unittest.TestCase):
    """Tests for the Flask application routes."""

    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_home_page(self):
        """The home page should return HTML with status 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Skill Path AI", response.data)

    def test_about_page(self):
        """The about page should return HTML with status 200."""
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)

    def test_question_submission_route(self):
        """The /api/ask route should return JSON for a valid question."""
        response = self.client.post(
            "/api/ask",
            data=json.dumps({"question": "What is Pandas used for?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertIn("match_found", data)
        self.assertIn("answer", data)

    def test_api_ask_python_returns_match(self):
        """POST /api/ask with 'What is Python?' returns HTTP 200 and a match."""
        response = self.client.post(
            "/api/ask",
            data=json.dumps({"question": "What is Python?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertTrue(data["match_found"])
        self.assertIsNotNone(data["note"])
        self.assertGreaterEqual(data["score_percent"], 0)
        self.assertIsInstance(data["answer"], str)
        self.assertGreater(len(data["answer"]), 0)
        self.assertIsNone(data["error"])

    def test_api_ask_unknown_returns_no_match(self):
        """POST /api/ask with an unrelated question returns match_found: false."""
        response = self.client.post(
            "/api/ask",
            data=json.dumps({"question": "What is the boiling point of mercury?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data["match_found"])
        self.assertEqual(data["score_percent"], 0)
        self.assertIn("could not find", (data["answer"] or "").lower())
        self.assertIsNone(data["error"])

    def test_api_ask_machine_learning_returns_match(self):
        """POST /api/ask with 'Explain machine learning' returns HTTP 200 and a match."""
        response = self.client.post(
            "/api/ask",
            data=json.dumps({"question": "Explain machine learning"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["match_found"])
        self.assertIsInstance(data["answer"], str)
        self.assertGreater(len(data["answer"]), 0)
        self.assertIsNone(data["error"])
        self.assertIn("machine learning", (data["answer"] or "").lower())

    def test_api_ask_capital_of_france_returns_match(self):
        """POST /api/ask with 'What is the capital of France?' returns HTTP 200 and mentions Paris."""
        response = self.client.post(
            "/api/ask",
            data=json.dumps({"question": "What is the capital of France?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["match_found"])
        self.assertIsInstance(data["answer"], str)
        self.assertGreater(len(data["answer"]), 0)
        self.assertIsNone(data["error"])
        self.assertIn("Paris", data["answer"])

    def test_api_ask_pandas_missing_values_returns_match(self):
        """POST /api/ask with 'Pandas missing values' returns HTTP 200 and a match."""
        response = self.client.post(
            "/api/ask",
            data=json.dumps({"question": "Pandas missing values"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["match_found"])
        self.assertIsInstance(data["answer"], str)
        self.assertGreater(len(data["answer"]), 0)
        self.assertIsNone(data["error"])
        answer_lower = (data["answer"] or "").lower()
        self.assertIn("pandas", answer_lower)
        self.assertTrue(
            "dropna" in answer_lower or "fillna" in answer_lower or "isnull" in answer_lower or "isna" in answer_lower,
            "Answer should mention missing-value handling methods",
        )

    def test_api_ask_empty_question_returns_400(self):
        """POST /api/ask with an empty question returns HTTP 400."""
        response = self.client.post(
            "/api/ask",
            data=json.dumps({"question": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_api_ask_non_json_returns_415(self):
        """POST /api/ask with non-JSON content returns HTTP 415."""
        response = self.client.post(
            "/api/ask",
            data="not json",
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, 415)

    def test_404_page(self):
        """An unknown route should return a 404 JSON error."""
        response = self.client.get("/does-not-exist")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
