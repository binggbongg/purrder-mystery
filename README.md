# 🐾 Purrder Mystery

**Purrder Mystery** is a cozy, cat-themed deductive logic game inspired by *Murdle*, built with Python and Streamlit. Each playthrough procedurally generates a unique 4x4x4 murder mystery puzzle and lets players interrogate feline suspects powered by an LLM—requiring sharp questioning to extract clues without the AI ever giving away the final answer.

---

## 🎯 Project Overview

* **Target Audience:** Murder mystery lovers, gamers, and logic puzzle enthusiasts.
* **Industry:** Gaming & Gamified EdTech (critical thinking and deductive reasoning).
* **Core Loop:** 
  1. Generate a randomized 4x4x4 logic matrix (4 Suspects, 4 Weapons, 4 Locations).
  2. Read the introductory crime scene narrative.
  3. Interrogate individual feline suspects 1-on-1 to uncover their alibis and hidden clues.
  4. Track eliminations and confirmations on the interactive deduction grid.
  5. Submit a final accusation (Who, What, Where) for a detailed deduction score.

---

## ✨ Key Features

* **Deterministic 4x4x4 Logic Engine:** Guarantees every generated puzzle is mathematically solvable with zero contradicting alibis.
* **Dynamic Narrative Generation:** Crafts a unique, PG-13 cozy mystery hook for every round based on the selected database entities.
* **Persona-Driven Interrogation:** Switches seamlessly between 4 distinct cat suspects, complete with breed quirks, feline body language, and strict knowledge boundaries.
* **Prompt-Injection Guardrails:** Enforces strict system rules so suspects remain evasive, stay in character, and never leak the final triplet.
* **Interactive Deduction Workspace:** Built-in Streamlit cross-reference grid alongside the interrogation terminal.
* **Accusation & Post-Game Evaluator:** Reports the case outcome, detective rank, and a 100-point breakdown of accusation accuracy, clue discovery, question quality, reasoning, efficiency, and independence.

## Investigation scoring

The accusation closes the case. Purrder reviews the recorded investigation in batches and shows the report when review completes. The optional accusation explanation can contribute deductive reasoning. If the evaluator is unavailable, the accusation outcome is still recorded and the performance review can be retried. Offline mock mode can complete a score when there are no interactions that require qualitative review.

Tune category allocations, clue weights, meaningful-question thresholds, difficulty budgets, hint deductions, ranks, and evaluator limits in `ScoringConfig` in `scoring.py`. The current cases use the medium budget by default. To use a smaller model for the evaluator, set `SCORING_LLM_MODEL` to a model served by the existing provider. Local Ollama at port 11434 reviews one turn at a time using structured output, with a longer timeout for local inference.

Streamlit saves cases and reports in `.purrder/sessions.sqlite3` by default. Set `PURRDER_SESSION_DB` to choose another writable location. Keep the database on persistent storage to retain cases across server restarts. The browser URL contains a private case resume token. Anyone with that URL can reopen the case. The CLI keeps its existing process-local sessions.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Frontend / UI:** Streamlit
* **Data Validation:** Pydantic
* **LLM Integration:** OpenAI / Google GenAI / Anthropic SDK (configurable via `.env`)

---

## 🚀 Setup & Installation (Windows 11 / VS Code)

1. **Clone the repository and open in VS Code:**
   ```bash
   git clone [https://github.com/yourusername/purrder-mystery.git]
   cd purrder-mystery
   code .
