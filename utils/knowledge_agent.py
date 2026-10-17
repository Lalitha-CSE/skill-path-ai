"""Knowledge retrieval agent for Skill Path AI.

The agent loads notes from a JSON knowledge base, compares a student's
question against each note using TF-IDF vectorization and cosine
similarity, and returns the best match together with a similarity score.

Retrieval logic is intentionally separate from Flask route logic so it can
be tested and reused independently of the web layer.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeAgentError(Exception):
    """Raised when the knowledge agent cannot operate correctly."""


class KnowledgeAgent:
    """Search a local JSON knowledge base using TF-IDF and cosine similarity."""

    def __init__(
        self,
        knowledge_path: str,
        similarity_threshold: float = 0.25,
    ) -> None:
        """Initialize the agent.

        Args:
            knowledge_path: Filesystem path to the knowledge JSON file.
            similarity_threshold: Minimum cosine similarity required to
                treat a note as relevant. Scores range from 0 to 1.
        """
        self.knowledge_path = knowledge_path
        self.similarity_threshold = similarity_threshold
        self.notes: List[Dict[str, Any]] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._note_matrix = None
        self._loaded = False

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #
    def load(self) -> List[Dict[str, Any]]:
        """Load and validate notes from the knowledge JSON file.

        Returns:
            The list of note dictionaries.

        Raises:
            KnowledgeAgentError: If the file is missing, contains malformed
                JSON, or does not hold a list of usable note objects.
        """
        if not os.path.exists(self.knowledge_path):
            raise KnowledgeAgentError(
                f"Knowledge file not found: {self.knowledge_path}"
            )

        try:
            with open(self.knowledge_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise KnowledgeAgentError(
                f"Malformed JSON in knowledge file: {exc}"
            ) from exc
        except OSError as exc:
            raise KnowledgeAgentError(
                f"Unable to read knowledge file: {exc}"
            ) from exc

        if not isinstance(data, list):
            raise KnowledgeAgentError(
                "Knowledge base must contain a JSON array of notes"
            )

        cleaned: List[Dict[str, Any]] = []
        for index, entry in enumerate(data):
            if not isinstance(entry, dict):
                continue
            topic = str(entry.get("topic", "")).strip()
            text = str(entry.get("text", "")).strip()
            if not topic or not text:
                continue
            cleaned.append(
                {
                    "id": str(entry.get("id", f"note-{index}")),
                    "topic": topic,
                    "keywords": str(entry.get("keywords", "")),
                    "text": text,
                    "status": str(entry.get("status", "unreviewed")).strip() or "unreviewed",
                }
            )

        if not cleaned:
            raise KnowledgeAgentError("Knowledge base contains no usable notes")

        self.notes = cleaned
        self._build_index()
        self._loaded = True
        return self.notes

    def _build_index(self) -> None:
        """Build the TF-IDF index over note topic + content text."""
        documents = [
            f"{note['topic']} {note['keywords']} {note['text']}"
            for note in self.notes
        ]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._note_matrix = self._vectorizer.fit_transform(documents)

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #
    def _similarity(self, question: str) -> List[float]:
        """Return cosine similarities between the question and all notes."""
        if self._vectorizer is None or self._note_matrix is None:
            raise KnowledgeAgentError("Knowledge index has not been built")
        query_vector = self._vectorizer.transform([question])
        similarities = cosine_similarity(query_vector, self._note_matrix)
        return similarities[0].tolist()

    def find_best_match(self, question: str) -> Dict[str, Any]:
        """Find the most relevant note for a question.

        Args:
            question: The student's question.

        Returns:
            A dictionary with keys:
                - match_found: bool
                - note: the best matching note (or None)
                - score: float similarity score (0 to 1)
                - score_percent: score expressed as a percentage
                - answer: the note text or a fallback message
                - warning: draft-status warning (or None)
                - error: error message (or None)

        Raises:
            KnowledgeAgentError: If the agent has not been loaded.
        """
        if not self._loaded or not self.notes:
            raise KnowledgeAgentError("Knowledge agent has not been loaded")

        question = question.strip()
        if not question:
            return {
                "match_found": False,
                "note": None,
                "score": 0.0,
                "score_percent": 0,
                "answer": "Please enter a question before asking.",
                "warning": None,
                "error": None,
            }

        try:
            similarities = self._similarity(question)
        except ValueError as exc:
            # Occurs when the vocabulary is empty or the query contains no
            # known terms after stop-word removal.
            return {
                "match_found": False,
                "note": None,
                "score": 0.0,
                "score_percent": 0,
                "answer": (
                    "I could not find a relevant note for that question. "
                    "Try rephrasing it or browse the learning paths."
                ),
                "warning": None,
                "error": None,
            }

        best_index = int(max(range(len(similarities)), key=lambda i: similarities[i]))
        best_score = float(similarities[best_index])
        best_note = self.notes[best_index]

        result: Dict[str, Any] = {
            "match_found": best_score >= self.similarity_threshold,
            "note": best_note,
            "score": best_score,
            "score_percent": round(best_score * 100, 1),
            "answer": "",
            "warning": None,
            "error": None,
        }

        if result["match_found"]:
            result["answer"] = best_note["text"]
            if best_note["status"].lower() == "draft":
                result["warning"] = (
                    f"Note: the source '{best_note['topic']}' is marked as a "
                    "draft. Review it before relying on it for coursework."
                )
        else:
            result["answer"] = (
                "I could not find a relevant note in the knowledge base for "
                "that question. Try rephrasing it or ask about Python, AI, "
                "machine learning, data science, or careers."
            )

        return result

    def answer(self, question: str) -> Dict[str, Any]:
        """Convenience wrapper around :meth:`find_best_match`.

        Catches unexpected errors so callers always receive a result dict
        instead of an exception.
        """
        try:
            return self.find_best_match(question)
        except KnowledgeAgentError as exc:
            return {
                "match_found": False,
                "note": None,
                "score": 0.0,
                "score_percent": 0,
                "answer": "The knowledge agent is currently unavailable.",
                "warning": None,
                "error": str(exc),
            }
        except Exception as exc:  # pragma: no cover - defensive safeguard
            return {
                "match_found": False,
                "note": None,
                "score": 0.0,
                "score_percent": 0,
                "answer": "An unexpected error occurred while processing your question.",
                "warning": None,
                "error": str(exc),
            }
