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
* **Accusation & Post-Game Evaluator:** Grades the player's final guess and highlights which clues were successfully uncovered versus missed.

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