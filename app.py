"""
Colleague Zero — Autonomous Multi-Agent Education Colleague
"""

import csv
import io
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, Response

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

from agents import get_gemini_client, run_autonomous_worker_pipeline
from pace_sync import poll_and_grade_pace_academy_submissions, push_colleague_zero_grade_to_pace_db
from db import (
    commit_worker_pipeline_run,
    create_custom_assignment,
    ensure_real_assignments_exist,
    fetch_batch_dict,
    get_db_session,
    get_db_status,
    list_all_users,
    mark_notifications_read,
    register_or_login_user,
    wipe_all_submissions_and_users,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "colleague-zero-standalone-key")


@app.route("/")
@app.route("/login")
def login_page():
    has_gemini = get_gemini_client() is not None
    return render_template("login.html", has_gemini=has_gemini)


@app.route("/learner")
def learner_portal():
    has_gemini = get_gemini_client() is not None
    return render_template("learner.html", has_gemini=has_gemini)


@app.route("/teacher")
def teacher_portal():
    has_gemini = get_gemini_client() is not None
    return render_template("index.html", has_gemini=has_gemini)


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "learner").strip()
    school_or_cohort = (data.get("school_or_cohort") or "").strip()

    if not name or not email:
        return jsonify({"ok": False, "error": "Please enter your name and email."}), 400

    user_dict = register_or_login_user(
        name=name,
        email=email,
        password=password or "pass123",
        role=role,
        school_or_cohort=school_or_cohort,
    )
    return jsonify({"ok": True, "user": user_dict})


@app.route("/api/users", methods=["GET"])
def get_users():
    return jsonify({
        "ok": True,
        "users": list_all_users(),
    })


@app.route("/api/assignments/create", methods=["POST"])
def create_assignment_route():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    programme_type = (data.get("programme_type") or "CAPS / SETA Assessment").strip()
    question_prompt = (data.get("question_prompt") or "").strip()
    rubric_version = (data.get("rubric_version") or "Custom Rubric v1.0").strip()
    pass_mark = int(data.get("pass_mark") or 50)
    criteria = data.get("criteria") or []

    if not title or not criteria:
        return jsonify({"ok": False, "error": "Please provide an assignment title and rubric criteria."}), 400

    default_goal = (
        f"Autonomously assess all incoming learner submissions for '{title}' against {rubric_version}, "
        f"moderate for grading fairness, self-correct rubric discrepancies, and send 3-step recovery plans."
    )
    rubric_dict = {
        "version": rubric_version,
        "question_prompt": question_prompt,
        "total_marks": sum(int(c.get("weight", 25)) for c in criteria),
        "pass_mark": pass_mark,
        "criteria": criteria,
    }
    new_batch_id = create_custom_assignment(
        title=title,
        programme_type=programme_type,
        default_goal=default_goal,
        rubric_dict=rubric_dict,
    )
    batch_data = fetch_batch_dict(new_batch_id)
    return jsonify({
        "ok": True,
        "batch_id": new_batch_id,
        "batch": batch_data,
        "available_batches": batch_data["available_batches"],
    })


@app.route("/api/batches", methods=["GET"])
def get_batches():
    batch_id = request.args.get("batch_id") or "caps_life_sciences"
    poll_and_grade_pace_academy_submissions(batch_id)
    batch_data = fetch_batch_dict(batch_id)
    return jsonify({
        "ok": True,
        "batch": batch_data,
        "available_batches": batch_data["available_batches"],
        "notifications": batch_data["notifications"],
        "agent_events": batch_data.get("agent_events", []),
        "has_gemini": get_gemini_client() is not None,
    })


@app.route("/api/submissions/add", methods=["POST"])
def add_custom_submission():
    """
    Runs the 4 autonomous Agent Workers (`PlannerWorker` -> `AssessorWorker` -> `ModeratorWorker` -> `RecoveryWorker`)
    and commits the submission, worker execution trace (`agent_events`), and notifications in a single fast transaction.
    """
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id", "caps_life_sciences")
    batch_data = fetch_batch_dict(batch_id)

    learner_name = (data.get("learner_name") or "").strip()
    learner_email = (data.get("learner_email") or "").strip()
    school_or_cohort = (data.get("school_or_cohort") or "Grade 12 / SETA Cohort").strip()
    essay_text = (data.get("essay_text") or "").strip()

    if not learner_name:
        return jsonify({"ok": False, "error": "Please sign in with your name before submitting."}), 400
    if not essay_text:
        return jsonify({"ok": False, "error": "Please write or upload your assignment response."}), 400

    next_num = len(batch_data["submissions"]) + 1
    evaluated_dict, worker_events = run_autonomous_worker_pipeline(
        batch_id=batch_data["id"],
        learner_name=learner_name,
        school_or_cohort=school_or_cohort,
        essay_text=essay_text,
        rubric=batch_data["rubric"],
        number=next_num,
    )

    saved_sub = commit_worker_pipeline_run(
        batch_id=batch_data["id"],
        learner_name=learner_name,
        learner_email=learner_email,
        school_or_cohort=school_or_cohort,
        evaluated_dict=evaluated_dict,
        worker_events=worker_events,
    )
    push_colleague_zero_grade_to_pace_db(
        learner_name=learner_name,
        learner_email=learner_email,
        school_or_cohort=school_or_cohort,
        batch_data=batch_data,
        evaluated_dict=evaluated_dict,
    )
    updated_batch = fetch_batch_dict(batch_data["id"])

    return jsonify({
        "ok": True,
        "submission": saved_sub,
        "batch": updated_batch,
        "notifications": updated_batch["notifications"],
        "agent_events": updated_batch.get("agent_events", []),
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
    wipe_all_submissions_and_users(reset_assignments=False)
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
    s = get_db_session()
    if s is not None:
        s.close()
    port = int(os.getenv("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
