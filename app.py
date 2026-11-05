"""
Colleague Zero — Standalone Multi-Agent Education Colleague
Autonomous Assessor, Internal Moderator & Learner Recovery Team for CAPS & SETA.
Completely independent Flask application (runs on port 5050 by default).
"""

import copy
import csv
import io
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, Response

from sample_data import BATCHES
from agents import evaluate_custom_submission_multi_agent, get_gemini_client

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "colleague-zero-standalone-key")

# In-memory working store so live custom judge submissions persist during the session
RUNTIME_BATCHES = copy.deepcopy(BATCHES)


@app.route("/")
def index():
    has_gemini = get_gemini_client() is not None
    return render_template("index.html", has_gemini=has_gemini)


@app.route("/api/batches", methods=["GET"])
def get_batches():
    batch_id = request.args.get("batch_id", "caps_life_sciences")
    if batch_id not in RUNTIME_BATCHES:
        batch_id = "caps_life_sciences"
    return jsonify({
        "ok": True,
        "batch": RUNTIME_BATCHES[batch_id],
        "available_batches": [
            {"id": k, "title": v["title"], "programme_type": v["programme_type"], "count": len(v["submissions"])}
            for k, v in RUNTIME_BATCHES.items()
        ],
        "has_gemini": get_gemini_client() is not None
    })


@app.route("/api/submissions/add", methods=["POST"])
def add_custom_submission():
    """
    Allows a user or hackathon judge to inject a live learner essay into the batch
    and immediately runs the 4-agent Planner -> Assessor -> Moderator -> Recovery loop.
    """
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id", "caps_life_sciences")
    if batch_id not in RUNTIME_BATCHES:
        batch_id = "caps_life_sciences"

    batch = RUNTIME_BATCHES[batch_id]
    learner_name = (data.get("learner_name") or "Judge Test Learner").strip()
    school_or_cohort = (data.get("school_or_cohort") or "Live Hackathon Evaluation").strip()
    essay_text = (data.get("essay_text") or "").strip()

    if not essay_text:
        return jsonify({"ok": False, "error": "Please provide learner submission text."}), 400

    next_num = len(batch["submissions"]) + 1
    evaluated = evaluate_custom_submission_multi_agent(
        learner_name=learner_name,
        school_or_cohort=school_or_cohort,
        essay_text=essay_text,
        rubric=batch["rubric"],
        number=next_num,
    )
    batch["submissions"].insert(0, evaluated)
    for idx, sub in enumerate(batch["submissions"], start=1):
        sub["number"] = idx

    return jsonify({
        "ok": True,
        "submission": evaluated,
        "batch": batch
    })


@app.route("/api/batches/reset", methods=["POST"])
def reset_batches():
    global RUNTIME_BATCHES
    RUNTIME_BATCHES = copy.deepcopy(BATCHES)
    return jsonify({"ok": True})


@app.route("/api/export/<batch_id>.csv", methods=["GET"])
def export_batch_csv(batch_id):
    if batch_id not in RUNTIME_BATCHES:
        batch_id = "caps_life_sciences"
    batch = RUNTIME_BATCHES[batch_id]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Script #",
        "Learner Name",
        "School / Cohort",
        "Initial Assessor Mark (%)",
        "Moderator Flagged?",
        "Final Moderated Mark (%)",
        "Score Delta",
        "Moderator Audit Note",
        "Recovery Plan Triggered?",
        "Personalised Learner Feedback"
    ])
    for s in batch["submissions"]:
        init_score = s["initial_mark"]["score"]
        final_score = s["moderation"]["corrected_score"]
        delta = final_score - init_score
        writer.writerow([
            f"#{s['number']}",
            s["learner_name"],
            s["school_or_cohort"],
            f"{init_score}%",
            "YES (Self-Corrected)" if s["moderation"]["flagged"] else "NO (Verified)",
            f"{final_score}%",
            f"{'+' if delta > 0 else ''}{delta}%" if delta != 0 else "0%",
            s["moderation"]["flag_reason"] or s["moderation"]["correction_log"],
            "YES" if s["recovery"]["needs_recovery"] else "NO",
            s["recovery"]["feedback"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=colleague_zero_{batch_id}_moderated.csv"}
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
