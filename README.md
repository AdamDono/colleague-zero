# Colleague Zero — Autonomous Assessor, Moderator & Learner Recovery Team

**Built for the Melsoft Academy Colleague Zero Hackathon (13–14 November 2026)**  
*“Don’t build a chatbot. Build a colleague.”*

---

## Overview

**Colleague Zero** is an autonomous multi-agent digital employee designed for South African **CAPS (Grades 10–12)** and **SETA / QCTO** education programmes.

Instead of waiting for chat prompts, you give Colleague Zero a **single high-level outcome goal** (e.g., *"Mark all Grade 12 Life Sciences submissions against Rubric v2, audit for grading fairness, self-correct any rubric discrepancies, and dispatch personalised remedial recovery plans to every learner"*).

Four specialized AI agents collaborate autonomously from start to finish with **zero human intervention**:

1. **`PL` — Planner Agent (`Reasons`):**
   - Parses the high-level goal, loads the curriculum rubric and weighting rules, scans the submission queue, splits learners into optimal batches, and sets moderation tolerances.
2. **`MK` — Assessor / Marker Agent (`Executes`):**
   - Evaluates each learner submission criterion-by-criterion against the official CAPS/SETA rubric and assigns initial scores and rationales.
3. **`RV` — Internal Moderator Agent (`Self-Corrects`):**
   - Audits every graded submission against the rubric before any mark is finalized.
   - Detects **grading inconsistencies, rubric mismatches, arithmetic errors, or unfair penalties against ESL / informal phrasing** when the learner demonstrated true conceptual mastery.
   - Issues a `[RV·FLAG]` rejection back to the Marker Agent (`MK`), forcing an autonomous `[MK·FIX]` re-evaluation until `[RV·PASS]` is achieved.
4. **`MS` — Learner Recovery & Delivery Agent (`Serves Education`):**
   - Generates criterion-specific feedback for every learner.
   - Automatically builds a **Personalised 3-Step Remedial Catch-Up Plan & Diagnostic Check** for any learner who scored below mastery on specific criteria, and dispatches the results.

---

## How It Meets the 5 Colleague Zero Judging Criteria

| Criterion | How Colleague Zero Delivers It |
| :--- | :--- |
| **01 · Reasons** | `PL` dynamically decomposes the goal, inspects rubric weights, identifies high-risk criteria, and orchestrates batch execution. |
| **02 · Self-Corrects** | `RV` independently audits `MK`'s marks, flags rubric discrepancies (`[RV·FLAG]`), sends scripts back to `MK` for re-marking (`[MK·FIX]`), and verifies compliance (`[RV·PASS]`). |
| **03 · Executes** | Delivers a complete graded mark sheet, full moderation audit log, individual feedback letters, and custom catch-up plans with `Human interventions: 0`. |
| **04 · Collaborates** | Four distinct agents (`PL`, `MK`, `RV`, `MS`) pass structured state payloads and rejection loops across an observable event bus. |
| **05 · Serves Education** | Solves South Africa's biggest educator & SETA bottleneck: teacher marking overload, internal moderation compliance, and immediate remedial support for struggling learners. |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Add your Gemini API key for live LLM reasoning
export GEMINI_API_KEY="your-gemini-api-key"

# 3. Run the standalone server (runs on port 5050 so it never conflicts with port 5000)
python app.py
```

Then open **`http://127.0.0.1:5050`** in your browser.
