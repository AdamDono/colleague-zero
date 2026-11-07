"""
Colleague Zero — Autonomous Multi-Agent Education Colleague
Two-Portal Architecture (Learner Account + Educator/Colleague Zero Account)
Backed by Neon PostgreSQL (via DATABASE_URL) with automatic SQLite fallback.
"""

import csv
import io
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, Response

from agents import evaluate_custom_submission_multi_agent, get_gemini_client
from db import (
    fetch_batch_dict,
    get_db_status,
    mark_notifications_read,
    save_live_submission,
    seed_if_empty,
    get_db_session,
)

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "colleague-zero-standalone-key")

# Ensure DB is initialized and seeded on startup
get_db_session().close()


@app.route("/")
@app.route("/login")
def login_page():
    has_gemini = get_gemini_client() is not None
    db_status = get_db_status()
    return render_template("login.html", has_gemini=has_gemini, db_status=db_status)


@app.route("/learner")
def learner_portal():
    has_gemini = get_gemini_client() is not None
    db_status = get_db_status()
    return render_template("learner.html", has_gemini=has_gemini, db_status=db_status)


@app.route("/teacher")
def teacher_portal():
    has_gemini = get_gemini_client() is not None
    db_status = get_db_status()
    return render_template("index.html", has_gemini=has_gemini, db_status=db_status)


@app.route("/api/batches", methods=["GET"])
def get_batches():
    batch_id = request.args.get("batch_id", "caps_life_sciences")
    batch_data = fetch_batch_dict(batch_id)
    return jsonify({
        "ok": True,
        "batch": batch_data,
        "available_batches": batch_data["available_batches"],
        "notifications": batch_data["notifications"],
        "has_gemini": get_gemini_client() is not None,
        "db_status": get_db_status(),
    })


@app.route("/api/submissions/add", methods=["POST"])
def add_custom_submission():
    """
    Triggered when a learner submits an assignment from the Learner Portal (/learner)
    or when a judge injects a live test script from the Teacher Portal (/teacher).
    Automatically runs the 4-agent Planner -> Assessor -> Moderator -> Recovery loop,
    persists to the DB (Neon Postgres / SQLite), and dispatches notifications to both tabs.
    """
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id", "caps_life_sciences")
    batch_data = fetch_batch_dict(batch_id)

    learner_name = (data.get("learner_name") or "Sibusiso Tshabalala").strip()
    learner_email = (data.get("learner_email") or "").strip()
    school_or_cohort = (data.get("school_or_cohort") or "Orlando West Secondary · Gr 12A").strip()
    essay_text = (data.get("essay_text") or "").strip()

    if not essay_text:
        return jsonify({"ok": False, "error": "Please provide your assignment submission text."}), 400

    next_num = len(batch_data["submissions"]) + 1
    evaluated = evaluate_custom_submission_multi_agent(
        learner_name=learner_name,
        school_or_cohort=school_or_cohort,
        essay_text=essay_text,
        rubric=batch_data["rubric"],
        number=next_num,
    )

    saved_sub = save_live_submission(
        batch_id=batch_data["id"],
        evaluated_dict=evaluated,
        learner_email=learner_email,
    )
    updated_batch = fetch_batch_dict(batch_data["id"])

    return jsonify({
        "ok": True,
        "submission": saved_sub,
        "batch": updated_batch,
        "notifications": updated_batch["notifications"],
    })


@app.route("/api/notifications/read", methods=["POST"])
def read_notifications():
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id", "caps_life_sciences")
    role = data.get("role", "teacher")
    mark_notifications_read(batch_id, role)
    return jsonify({"ok": True})


@app.route("/api/batches/reset", methods=["POST"])
def reset_batches():
    get_db_session().close()
    seed_if_empty(force_reset=True)
    return jsonify({"ok": True})


@app.route("/api/export/<batch_id>.csv", methods=["GET"])
def export_batch_csv(batch_id):
    batch = fetch_batch_dict(batch_id)

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
        "Personalised Learner Feedback",
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
            s["recovery"]["feedback"],
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=colleague_zero_{batch['id']}_moderated.csv"},
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
