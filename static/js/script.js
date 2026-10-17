/* Skill Path AI — Frontend interactivity */

(function () {
  "use strict";

  const form = document.getElementById("ask-form");
  const input = document.getElementById("question-input");
  const askButton = document.getElementById("ask-button");
  const charHint = document.getElementById("char-hint");
  const loader = document.getElementById("loader");
  const errorMessage = document.getElementById("error-message");
  const resultCard = document.getElementById("result");
  const noMatchCard = document.getElementById("no-match");

  const scorePill = document.getElementById("score-pill");
  const sourcePill = document.getElementById("source-pill");
  const resultTopic = document.getElementById("result-topic");
  const resultAnswer = document.getElementById("result-answer");
  const resultWarning = document.getElementById("result-warning");
  const noMatchMessage = document.getElementById("no-match-message");

  const MAX_LENGTH = 1000;

  // Character counter
  input.addEventListener("input", function () {
    const remaining = MAX_LENGTH - input.value.length;
    charHint.textContent = input.value.length + " / " + MAX_LENGTH + " characters";
    charHint.style.color = remaining < 50 ? "#fb7185" : "var(--text-muted)";
    clearError();
  });

  // Chip buttons fill the input
  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      const question = chip.getAttribute("data-q") || "";
      input.value = question;
      input.dispatchEvent(new Event("input"));
      input.focus();
    });
  });

  function showLoader(show) {
    loader.style.display = show ? "flex" : "none";
    askButton.disabled = show;
    askButton.textContent = show ? "Searching..." : "Ask";
  }

  function clearError() {
    errorMessage.style.display = "none";
    errorMessage.textContent = "";
  }

  function setError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = "block";
  }

  function hideResults() {
    resultCard.classList.add("hidden");
    noMatchCard.classList.add("hidden");
  }

  function renderResult(data) {
    hideResults();

    if (data.error) {
      setError(data.error || "Unable to process your question.");
      showLoader(false);
      return;
    }

    if (!data.match_found) {
      noMatchMessage.textContent =
        data.answer || "No relevant note was found for your question.";
      noMatchCard.classList.remove("hidden");
      showLoader(false);
      return;
    }

    const note = data.note || {};
    scorePill.textContent = "Score: " + (data.score_percent !== undefined ? data.score_percent + "%" : "—");
    sourcePill.textContent = "Source: " + (note.topic || "—");
    resultTopic.textContent = note.topic || "Unknown topic";
    resultAnswer.textContent = data.answer || "";

    const warning = data.warning || "";
    if (warning) {
      resultWarning.textContent = warning;
      resultWarning.style.display = "block";
    } else {
      resultWarning.style.display = "none";
    }

    resultCard.classList.remove("hidden");
    showLoader(false);
    input.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const question = (input.value || "").trim();
    if (!question) {
      setError("Please type a question before asking.");
      input.focus();
      return;
    }

    if (question.length > MAX_LENGTH) {
      setError("Question is too long. Please shorten it.");
      input.focus();
      return;
    }

    clearError();
    hideResults();
    showLoader(true);

    console.log("[Skill Path AI] Submitting question:", question);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question }),
      });

      console.log("[Skill Path AI] Response status:", response.status);

      let data;
      try {
        data = await response.json();
      } catch (parseErr) {
        setError("Server returned an invalid response. Please try again.");
        console.error("[Skill Path AI] Failed to parse JSON response:", parseErr);
        showLoader(false);
        return;
      }

      if (!response.ok) {
        if (data && data.error) {
          setError(data.error);
        } else {
          setError("Server error (status " + response.status + ").");
        }
        console.error("[Skill Path AI] API error:", response.status, data);
        showLoader(false);
        return;
      }

      console.log("[Skill Path AI] API response:", data);
      renderResult(data);
    } catch (err) {
      setError("Unable to reach the server. Make sure Flask is running.");
      console.error("[Skill Path AI] Network error:", err);
      showLoader(false);
    }
  }

  form.addEventListener("submit", handleSubmit);

  // Allow Enter to submit when the input is focused (single-line input).
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event("submit"));
    }
  });
})();
