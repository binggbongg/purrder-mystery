# 🐾 Purrder Mystery

A cozy, cat-themed deduction game inspired by *Murdle*, built with Python and Streamlit. Interrogate LLM-powered feline suspects, collect clues, and work out who did it, with what, and where.

**Live app:** https://purrder-mystery-meow.streamlit.app

## 🎯 Overview

- **Target users:** Murder mystery lovers, gamers, and logic puzzle enthusiasts
- **Industry:** Gaming and Gamified Education

## 🎮 How to Play

1. Read the crime scene report.
2. Interrogate each suspect one-on-one.
3. Track your deductions on the grid.
4. Submit your accusation (Who, What, Where) to receive your score and evaluation.

## ✨ Features

- **Randomized Cases:** 4 of 6 suspects, 4 of 8 weapons, and 4 of 8 locations per round
- **Python Logic Engine:** Python decides the solution and clues; the LLM phrases the dialogue
- **Dynamic Narrative:** A cozy AI-written crime scene report for each case
- **Persona-Driven Interrogation:** Distinct personalities, mannerisms, and limited knowledge for each cat
- **Deduction Grid:** Cross-reference suspects, weapons, and locations
- **Accusation and Scoring:** A final score with a detective rank
- **Prompt Defenses:** Input filtering, random sequence enclosure, instruction defense, post-prompting, and output checking

## 🛠️ Tech Stack

- Python 3.11+
- Streamlit
- Pydantic
- Ollama, ChatGPT Luna 6

## 🚀 Run Locally (Windows)

1. Clone the repository:
   ```powershell
   git clone https://github.com/yourusername/purrder-mystery.git
   cd purrder-mystery
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Install the dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Create your settings file:
   ```powershell
   copy .env.example .env
   ```
5. Start the app:
   ```powershell
   streamlit run ui/app.py
   ```