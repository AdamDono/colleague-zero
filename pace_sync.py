"""
Two-Way Live Bridge between Colleague Zero (`/Users/dam1mac89/Desktop/colleague-zero`)
and Pace Academy (`/Users/dam1mac89/Desktop/pace/instance/pace_local.db`):
1. Detects any learner assignment submitted inside Pace Academy (`assignment_submissions`),
   grades & moderates it with the 4 Autonomous Agent Workers (`PL -> MK -> RV -> MS`),
   writes the final mark (`grade`), `reviewed = 1`, and `feedback` back to Pace Academy's DB
   (plus Pace Academy Student & Teacher `notifications`), and imports it into Colleague Zero.
2. When a learner submits inside Colleague Zero, also writes the graded submission & mark
   into Pace Academy's `assignment_submissions` table so both platforms stay 100% in sync.
"""

import os
import re
import sqlite3
from datetime import datetime

from agents import run_autonomous_worker_pipeline
from db import commit_worker_pipeline_run, fetch_batch_dict

PACE_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pace", "instance", "pace_local.db")
)

_SYNCED_PACE_SUBMISSION_IDS = set()


def _format_pace_feedback(evaluated_dict, rubric):
    init_score = evaluated_dict["initial_mark"]["score"]
    final_score = evaluated_dict["moderation"]["corrected_score"]
    flagged = evaluated_dict["moderation"]["flagged"]
    lines = []

    if flagged:
        lines.append(
            f"⚡ COLLEAGUE ZERO MODERATION AUDIT: Assessor [MK] Pass-1: {init_score}% → Moderator [RV] Adjusted: {final_score}%"
        )
        lines.append(f"• Audit Finding: {evaluated_dict['moderation']['flag_reason']}")
    else:
        lines.append(
            f"✅ COLLEAGUE ZERO VERIFIED GRADE: {final_score}% ({rubric.get('version', 'Official Rubric')})"
        )

    lines.append("")
    lines.append(f"💬 FEEDBACK: {evaluated_dict['recovery']['feedback']}")
    lines.append("")
    lines.append("📊 RUBRIC CRITERION BREAKDOWN:")
    for c in rubric.get("criteria", []):
        cid = c["id"]
        w = c["weight"]
        iv = evaluated_dict["initial_mark"]["criteria_scores"].get(cid, 0)
        fv = evaluated_dict["moderation"]["corrected_criteria_scores"].get(cid, iv)
        delta_str = f" (Moderated from {iv}/{w})" if fv != iv else ""
        lines.append(f"  • {cid} · {c['name']}: {fv} / {w} marks{delta_str}")

    if evaluated_dict["recovery"].get("catchup_plan"):
        lines.append("")
        lines.append("🛟 3-STEP REMEDIAL / MASTERY PLAN:")
        for step in evaluated_dict["recovery"]["catchup_plan"]:
            lines.append(f"  ✓ {step}")

    return "\n".join(lines)


def poll_and_grade_pace_academy_submissions(active_batch_id="caps_life_sciences"):
    """
    Watches Pace Academy's `assignment_submissions` table for unreviewed or newly submitted work,
    runs the 4 Agent Workers (`PL -> MK -> RV -> MS`), writes the grade & feedback back into Pace Academy,
    and records the submission in Colleague Zero.
    """
    if not os.path.exists(PACE_DB_PATH):
        return 0

    graded_count = 0
    try:
        conn = sqlite3.connect(PACE_DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT
                s.id AS sub_id,
                s.assignment_id,
                s.student_id,
                s.attempt_number,
                s.submission_text,
                s.code_submission,
                s.submission_type,
                s.reviewed,
                s.grade,
                a.title AS assignment_title,
                a.description AS assignment_desc,
                a.section_id,
                sec.course_id,
                c.title AS course_title,
                c.teacher_id,
                u.first_name,
                u.last_name,
                u.username,
                u.email
            FROM assignment_submissions s
            JOIN assignments a ON s.assignment_id = a.id
            LEFT JOIN sections sec ON a.section_id = sec.id
            LEFT JOIN courses c ON sec.course_id = c.id
            LEFT JOIN users u ON s.student_id = u.id
            WHERE s.reviewed = 0 OR s.grade IS NULL
            ORDER BY s.id ASC
        """)
        rows = cur.fetchall()

        if not rows:
            conn.close()
            return 0

        batch_data = fetch_batch_dict(active_batch_id)
        rubric = batch_data["rubric"]

        for r in rows:
            sub_id = r["sub_id"]
            if sub_id in _SYNCED_PACE_SUBMISSION_IDS:
                continue

            fname = (r["first_name"] or "").strip()
            lname = (r["last_name"] or "").strip()
            learner_name = f"{fname} {lname}".strip() or r["username"] or (r["email"] or "Pace Learner").split("@")[0]
            learner_email = r["email"] or ""
            course_title = r["course_title"] or "Pace Academy Course"
            raw_text = (
                r["code_submission"]
                if (r["submission_type"] == "code" and r["code_submission"])
                else (r["submission_text"] or "")
            )
            if not raw_text.strip():
                continue

            evaluated_dict, worker_events = run_autonomous_worker_pipeline(
                batch_id=batch_data["id"],
                learner_name=learner_name,
                school_or_cohort=f"Pace Academy · {course_title}",
                essay_text=raw_text,
                rubric=rubric,
                number=r["attempt_number"] or 1,
            )

            final_score = float(evaluated_dict["moderation"]["corrected_score"])
            feedback_text = _format_pace_feedback(evaluated_dict, rubric)
            now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Write grade & feedback directly into Pace Academy's `assignment_submissions` table
            cur.execute(
                """
                UPDATE assignment_submissions
                SET grade = ?, reviewed = 1, feedback = ?
                WHERE id = ?
                """,
                (final_score, feedback_text, sub_id),
            )

            # 2. Insert Student & Teacher notifications in Pace Academy's `notifications` table
            if r["student_id"]:
                cur.execute(
                    """
                    INSERT INTO notifications (
                        user_id, notification_type, title, message, link_url,
                        read, emailed, created_at, priority, related_course_id, related_assignment_id
                    ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
                    """,
                    (
                        r["student_id"],
                        "assignment_feedback",
                        f"⚡ Colleague Zero Graded: {r['assignment_title']} ({int(final_score)}%)",
                        evaluated_dict["recovery"]["feedback"],
                        f"/student/section/{r['section_id']}/assignment/{r['assignment_id']}/submit",
                        now_iso,
                        "high" if evaluated_dict["recovery"]["needs_recovery"] else "normal",
                        r["course_id"],
                        r["assignment_id"],
                    ),
                )

            if r["teacher_id"]:
                cur.execute(
                    """
                    INSERT INTO notifications (
                        user_id, notification_type, title, message, link_url,
                        read, emailed, created_at, priority, related_course_id, related_assignment_id
                    ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, 'normal', ?, ?)
                    """,
                    (
                        r["teacher_id"],
                        "assignment_feedback",
                        f"🤖 Colleague Zero Auto-Graded {learner_name} ({int(final_score)}%)",
                        f"{r['assignment_title']}: {evaluated_dict['moderation']['correction_log']}",
                        f"/teacher/course/{r['course_id']}/section/{r['section_id']}/submissions",
                        now_iso,
                        r["course_id"],
                        r["assignment_id"],
                    ),
                )

            conn.commit()
            _SYNCED_PACE_SUBMISSION_IDS.add(sub_id)
            graded_count += 1

            # 3. Also commit into Colleague Zero's own DB & live dashboard
            commit_worker_pipeline_run(
                batch_id=batch_data["id"],
                learner_name=learner_name,
                learner_email=learner_email,
                school_or_cohort=f"Pace Academy · {course_title}",
                evaluated_dict=evaluated_dict,
                worker_events=worker_events,
            )

        conn.close()
    except Exception as e:
        print("Pace DB poll note:", e)

    return graded_count


def push_colleague_zero_grade_to_pace_db(learner_name, learner_email, school_or_cohort, batch_data, evaluated_dict):
    """
    When a learner submits on Colleague Zero (`/learner`), also writes the graded submission
    and mark into Pace Academy's `assignment_submissions` table so both platforms show it!
    """
    if not os.path.exists(PACE_DB_PATH):
        return
    try:
        conn = sqlite3.connect(PACE_DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Find or create student in Pace Academy
        email_clean = (learner_email or f"{re.sub(r'[^a-z0-9]', '.', learner_name.lower())}@pace-academy.co.za").strip().lower()
        cur.execute("SELECT id FROM users WHERE lower(email) = ? OR lower(username) = ?", (email_clean, learner_name.lower()))
        user_row = cur.fetchone()
        if user_row:
            student_id = user_row["id"]
        else:
            parts = learner_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
            uname = re.sub(r"[^a-z0-9_]", "_", learner_name.lower())[:30] + "_cz"
            cur.execute(
                """
                INSERT INTO users (email, username, password_hash, role, first_name, last_name, created_at, login_count, is_suspended, is_banned)
                VALUES (?, ?, 'pbkdf2:sha256:600000$cz$0000', 'student', ?, ?, ?, 1, 0, 0)
                """,
                (email_clean, uname, first_name, last_name, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
            )
            student_id = cur.lastrowid

        # Find latest assignment in Pace Academy
        cur.execute("SELECT id, section_id, title FROM assignments ORDER BY id DESC LIMIT 1")
        assign_row = cur.fetchone()
        if assign_row:
            assignment_id = assign_row["id"]
            section_id = assign_row["section_id"]
            assign_title = assign_row["title"]
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM assignment_submissions WHERE assignment_id = ? AND student_id = ?",
                (assignment_id, student_id),
            )
            attempt_num = (cur.fetchone()["cnt"] or 0) + 1
            final_score = float(evaluated_dict["moderation"]["corrected_score"])
            feedback_text = _format_pace_feedback(evaluated_dict, batch_data["rubric"])
            now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            cur.execute(
                """
                INSERT INTO assignment_submissions (
                    assignment_id, student_id, attempt_number, submission_text,
                    submitted_at, reviewed, feedback, submission_type, grade
                ) VALUES (?, ?, ?, ?, ?, 1, ?, 'text', ?)
                """,
                (
                    assignment_id,
                    student_id,
                    attempt_num,
                    evaluated_dict["essay_text"],
                    now_iso,
                    feedback_text,
                    final_score,
                ),
            )
            new_pace_sub_id = cur.lastrowid
            _SYNCED_PACE_SUBMISSION_IDS.add(new_pace_sub_id)

            cur.execute(
                """
                INSERT INTO notifications (
                    user_id, notification_type, title, message, link_url,
                    read, emailed, created_at, priority, related_assignment_id
                ) VALUES (?, 'assignment_feedback', ?, ?, ?, 0, 0, ?, 'normal', ?)
                """,
                (
                    student_id,
                    f"⚡ Colleague Zero Graded: {assign_title} ({int(final_score)}%)",
                    evaluated_dict["recovery"]["feedback"],
                    f"/student/section/{section_id}/assignment/{assignment_id}/submit",
                    now_iso,
                    assignment_id,
                ),
            )
            conn.commit()
        conn.close()
    except Exception as e:
        print("Push to Pace DB note:", e)

