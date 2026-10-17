"""Skill Path AI — Flask backend.

Serves the knowledge-agent website and exposes a JSON question-answer
endpoint. Retrieval logic lives in utils/knowledge_agent.py.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request

from utils.knowledge_agent import KnowledgeAgent

# --------------------------------------------------------------------------- #
# Application setup
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "data", "knowledge.json")

app = Flask(__name__, template_folder="templates", static_folder="static")

# Reasonable request-size limit (1 MB is ample for a question payload).
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

# Maximum accepted question length.
MAX_QUESTION_LENGTH = 1000

# Single shared agent instance. Load the knowledge base at startup.
knowledge_agent = KnowledgeAgent(
    knowledge_path=KNOWLEDGE_PATH,
    similarity_threshold=0.25,
)

try:
    knowledge_agent.load()
except Exception:  # pragma: no cover - startup safeguard
    # Defer the error to the request handler so the app still starts and
    # can return a helpful message instead of crashing on import.
    knowledge_agent = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index() -> str:
    """Render the home page with the question-answer interface."""
    return render_template("index.html")


@app.route("/about")
def about() -> str:
    """Render the About page explaining how the agent works."""
    return render_template("about.html")


@app.route("/api/ask", methods=["POST"])
def ask() -> Any:
    """Handle question submissions.

    Expects JSON: {"question": "..."}
    Returns JSON with the agent result and an appropriate HTTP status code.
    """
    if knowledge_agent is None:
        return jsonify(
            {
                "error": "Knowledge base is not available.",
                "match_found": False,
                "answer": "The knowledge agent could not be initialized.",
            }
        ), 503

    if not request.is_json:
        return jsonify({"error": "Request must be JSON."}), 415

    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    question = payload.get("question", "")

    if not isinstance(question, str):
        return jsonify({"error": "Question must be a string."}), 400

    question = question.strip()
    if not question:
        return jsonify({"error": "Question cannot be empty."}), 400

    if len(question) > MAX_QUESTION_LENGTH:
        return jsonify(
            {
                "error": f"Question is too long (maximum {MAX_QUESTION_LENGTH} characters)."
            }
        ), 400

    result = knowledge_agent.answer(question)
    status = 200 if result.get("error") is None else 500
    return jsonify(result), status


@app.errorhandler(404)
def not_found(error: Any) -> Any:
    """Friendly 404 handler."""
    return jsonify({"error": "Page not found."}), 404


@app.errorhandler(413)
def request_too_large(error: Any) -> Any:
    """Handler for oversized request payloads."""
    return jsonify({"error": "Request payload is too large."}), 413


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Debug mode is only for local development, never production.
    app.run(host="127.0.0.1", port=5000, debug=False)
