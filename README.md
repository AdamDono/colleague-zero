# Colleague Zero — Autonomous Assessor, Internal Moderator & Learner Recovery Team

**Built for the Melsoft Academy Colleague Zero Hackathon**  
*“Don’t build a chatbot. Build a colleague.”*

---

## Overview

**Colleague Zero** is an autonomous 4-agent digital colleague built for South African **CAPS (Grades 10–12)** and **SETA / QCTO** education programmes, backed by **Neon Serverless PostgreSQL**.

Instead of acting as a prompt-driven chatbot, Colleague Zero operates across a **Two-Portal Live Architecture**:
- **Tab 1 — Learner Portal (`/learner`):** Learners sign in, inspect the active assignment prompt and official rubric criteria (`C1–C4`), submit their response (or upload a file), and receive real-time notifications with their moderated mark, fairness audit explanation, criterion breakdown, and interactive **3-Step Remedial Catch-Up Plan**.
- **Tab 2 — Educator & Colleague Zero Hub (`/teacher`):** Educators sign in, create custom assignments & rubrics, set a single standing **Outcome Goal**, and watch Colleague Zero autonomously detect incoming learner submissions, evaluate them across 4 collaborating agents (`PL → MK → RV → MS`), self-correct grading discrepancies with **0 human interventions**, and export audit-ready CSV marksheets.

---

## The 4-Agent Autonomous Pipeline

1. **`PL` — Planner Agent (`01 · Reasons`):**
   - Monitors the database queue for incoming learner submissions, parses the standing outcome goal, and extracts the active rubric criteria, weights, and required domain concepts.
2. **`MK` — Assessor / Marker Agent (`02 · Executes`):**
   - Evaluates each learner submission criterion-by-criterion (`C1–C4`) against the official CAPS/SETA rubric and logs initial scores and evidence rationales.
3. **`RV` — Internal Moderator Agent (`03 · Self-Corrects`):**
   - Audits every graded submission against the rubric *before* any mark is finalized.
   - Detects **unfair penalties against second-language (ESL) / informal analogies** when the learner demonstrated true conceptual mastery, issues a `[RV·FLAG]`, and forces an autonomous `[MK·FIX]` re-evaluation until `[RV·PASS]` is verified.
4. **`MS` — Learner Recovery & Delivery Agent (`05 · Serves Education`):**
   - Generates criterion-specific feedback naming the exact criteria mastered vs missed.
   - Automatically builds a **Custom 3-Step Remedial Catch-Up Plan** targeting the learner's lowest-scoring criteria and dispatches real-time notifications to both the Learner and Educator portals.

---

## How It Meets the 5 Colleague Zero Judging Criteria

| Criterion | How Colleague Zero Delivers It |
| :--- | :--- |
| **01 · Reasons** | `PL` dynamically decomposes the standing outcome goal, extracts rubric weights and concepts, and routes incoming learner submissions. |
| **02 · Self-Corrects** | `RV` independently audits `MK`'s initial marks, flags unfair ESL/analogy penalties (`[RV·FLAG]`), forces `MK` to re-mark (`[MK·FIX]`), and verifies compliance (`[RV·PASS]`). |
| **03 · Executes** | Runs end-to-end from learner submission to moderated grade, database persistence, and recovery plan dispatch with `Human interventions: 0`. |
| **04 · Collaborates** | Four distinct agents (`PL`, `MK`, `RV`, `MS`) hand off structured state payloads and moderation loops across an observable live event bus. |
| **05 · Serves Education** | Eliminates educator marking & moderation overload while giving struggling learners immediate, criterion-specific 3-step recovery plans. |

---

## Architecture & Tech Stack

- **Backend:** Python, Flask (`app.py`), Multi-Agent Rubric & Gemini Engine (`agents.py`)
- **Database:** **Neon Serverless PostgreSQL** via SQLAlchemy & `psycopg2` (`db.py`) with automatic local SQLite fallback (`colleague_zero.db`)
- **Frontend:** Two-Portal Reactive UI (`templates/login.html`, `templates/learner.html`, `templates/index.html`) with cross-tab live polling and toast notifications

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env (Neon PostgreSQL URL + optional Gemini API Key)
# DATABASE_URL=postgresql://...
# GEMINI_API_KEY=...

# 3. Start the server (runs on port 5050)
python3 app.py
```

Open **`http://127.0.0.1:5050/login`** in your browser:
- Sign in to **Tab 1 (`/learner`)** as a Learner.
- Sign in to **Tab 2 (`/teacher`)** as an Educator & Moderator.
