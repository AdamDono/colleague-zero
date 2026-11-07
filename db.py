"""
Database layer for Colleague Zero (Neon Serverless PostgreSQL + SQLite fallback).
100% Real Data Mode:
- No pre-populated dummy student submissions.
- Real users table (`users`), real assignments & rubrics (`batches`),
  real learner submissions (`submissions`), and real notifications (`notifications`).
"""

import copy
import json
import os
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class UserRecord(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False)  # 'learner' or 'teacher'
    school_or_cohort = Column(String(255), nullable=False)
    created_at = Column(Float, default=lambda: time.time())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "school_or_cohort": self.school_or_cohort,
        }


class BatchRecord(Base):
    __tablename__ = "batches"

    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    programme_type = Column(String(255), nullable=False)
    default_goal = Column(Text, nullable=False)
    rubric_json = Column(Text, nullable=False)
    updated_at = Column(Float, default=lambda: time.time())


class SubmissionRecord(Base):
    __tablename__ = "submissions"

    id = Column(String(64), primary_key=True)
    batch_id = Column(String(64), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    learner_name = Column(String(255), nullable=False)
    learner_email = Column(String(255), nullable=True)
    school_or_cohort = Column(String(255), nullable=False)
    submitted_at = Column(String(128), nullable=False)
    essay_text = Column(Text, nullable=False)
    initial_mark_json = Column(Text, nullable=False)
    moderation_json = Column(Text, nullable=False)
    recovery_json = Column(Text, nullable=False)
    engine = Column(String(64), default="colleague-zero-ai")
    is_live = Column(Boolean, default=True)
    created_at = Column(Float, default=lambda: time.time())

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "number": self.number,
            "learner_name": self.learner_name,
            "learner_email": self.learner_email or "",
            "school_or_cohort": self.school_or_cohort,
            "submitted_at": self.submitted_at,
            "essay_text": self.essay_text,
            "initial_mark": json.loads(self.initial_mark_json),
            "moderation": json.loads(self.moderation_json),
            "recovery": json.loads(self.recovery_json),
            "engine": self.engine or "colleague-zero-ai",
            "is_live": bool(self.is_live),
            "created_at": self.created_at,
        }


class NotificationRecord(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), nullable=False, index=True)
    recipient_role = Column(String(32), nullable=False, index=True)  # 'teacher' or 'learner'
    learner_name = Column(String(255), nullable=True)
    submission_id = Column(String(64), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    badge_type = Column(String(32), default="info")
    is_read = Column(Boolean, default=False)
    created_at = Column(Float, default=lambda: time.time())
    time_label = Column(String(64), default="Just now")

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "recipient_role": self.recipient_role,
            "learner_name": self.learner_name,
            "submission_id": self.submission_id,
            "title": self.title,
            "message": self.message,
            "badge_type": self.badge_type,
            "is_read": bool(self.is_read),
            "created_at": self.created_at,
            "time_label": self.time_label,
        }


# Default real assignments with rubrics (0 dummy student submissions!)
DEFAULT_REAL_ASSIGNMENTS = [
    {
        "id": "caps_life_sciences",
        "title": "Grade 12 CAPS Life Sciences — Meiosis & Genetic Variation",
        "programme_type": "NSC CAPS · Grade 12 Paper 2 Assessment",
        "default_goal": (
            "Assess every incoming Grade 12 Life Sciences learner submission against CAPS Rubric v2.4, "
            "audit for grading fairness and second-language analogies, self-correct any rubric discrepancies, "
            "and dispatch personalised feedback with a 3-step remedial catch-up plan."
        ),
        "rubric": {
            "version": "DBE CAPS Rubric v2.4 (Paper 2)",
            "question_prompt": (
                "Explain how Meiosis contributes to genetic variation through Crossing-Over (Prophase I) "
                "and Random Arrangement of chromosomes (Metaphase I & II), and explain the biological "
                "importance of halving the chromosome number from diploid (2n=46) to haploid (n=23)."
            ),
            "total_marks": 100,
            "pass_mark": 50,
            "criteria": [
                {
                    "id": "C1",
                    "name": "Crossing-Over in Prophase I",
                    "weight": 30,
                    "description": "Homologous chromosomes pair up as bivalents, non-sister chromatids overlap at chiasmata, and exchange genetic material / DNA segments to create new allele combinations."
                },
                {
                    "id": "C2",
                    "name": "Random Arrangement in Metaphase I & II",
                    "weight": 30,
                    "description": "Homologous chromosome pairs arrange randomly along the equator in Metaphase I (and single chromosomes in Metaphase II), leading to independent assortment in gametes."
                },
                {
                    "id": "C3",
                    "name": "Halving Chromosome Number (Diploid to Haploid)",
                    "weight": 25,
                    "description": "Reduces diploid (2n / 46 chromosomes) parent cells to haploid (n / 23 chromosomes) gametes so fertilisation restores the correct diploid chromosome number."
                },
                {
                    "id": "C4",
                    "name": "Scientific Synthesis & Conceptual Clarity",
                    "weight": 15,
                    "description": "Clear distinction between Meiosis I and Meiosis II phases, logical cause-and-effect explanation of genetic variation, and accurate biological reasoning."
                }
            ]
        }
    },
    {
        "id": "seta_software_eng",
        "title": "SETA NQF Level 5 Software Engineering — API Security & Database Design",
        "programme_type": "MICT SETA · NQF Level 5 Workplace PoE",
        "default_goal": (
            "Evaluate all incoming MICT SETA NQF Level 5 learner PoE submissions against the API & Database Rubric, "
            "moderate for practical workplace understanding vs jargon, self-correct unfair scoring, and issue 3-step recovery plans."
        ),
        "rubric": {
            "version": "MICT SETA NQF5 Rubric v1.2",
            "question_prompt": (
                "Design a secure authentication and database architecture for a web application. "
                "Explain: (1) Password hashing & JWT/session authentication, (2) SQL Injection prevention & parameterised queries, "
                "(3) Relational database normalisation & indexing, and (4) Error handling & rate limiting."
            ),
            "total_marks": 100,
            "pass_mark": 50,
            "criteria": [
                {
                    "id": "C1",
                    "name": "Authentication & Password Security",
                    "weight": 30,
                    "description": "Explains password hashing (bcrypt/Argon2 with salt), token or session management (JWT/HTTP-only cookies), and HTTPS transport security."
                },
                {
                    "id": "C2",
                    "name": "SQL Injection Prevention & Data Validation",
                    "weight": 30,
                    "description": "Explains parameterised queries / prepared statements or ORM binding, input sanitisation, and least-privilege database user roles."
                },
                {
                    "id": "C3",
                    "name": "Database Schema, Keys & Indexing",
                    "weight": 25,
                    "description": "Explains primary and foreign keys, normalisation to prevent data redundancy, and indexing columns used in frequent WHERE/JOIN queries."
                },
                {
                    "id": "C4",
                    "name": "Resilience, Rate Limiting & Audit Logging",
                    "weight": 15,
                    "description": "Explains brute-force rate limiting, structured error responses without leaking stack traces, and audit logging."
                }
            ]
        }
    }
]

_engine = None
_SessionLocal = None
_active_db_url = None
_BATCH_CACHE = {}


def invalidate_batch_cache():
    global _BATCH_CACHE
    _BATCH_CACHE.clear()


def get_sqlite_fallback_url():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sqlite_path = os.path.join(base_dir, "colleague_zero.db")
    return f"sqlite:///{sqlite_path}"


def get_database_url():
    raw_url = (os.getenv("DATABASE_URL") or "").strip()
    if raw_url:
        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif raw_url.startswith("postgresql://") and "+psycopg2" not in raw_url:
            raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return raw_url
    return get_sqlite_fallback_url()


def get_db_session():
    global _engine, _SessionLocal, _active_db_url
    target_url = get_database_url()
    if _engine is None:
        urls_to_try = [target_url]
        if "channel_binding=require" in target_url:
            urls_to_try.append(target_url.replace("&channel_binding=require", "").replace("channel_binding=require&", ""))
        if not target_url.startswith("sqlite"):
            urls_to_try.append(get_sqlite_fallback_url())

        for candidate_url in urls_to_try:
            try:
                connect_args = {"check_same_thread": False} if candidate_url.startswith("sqlite") else {"connect_timeout": 8}
                eng = create_engine(candidate_url, connect_args=connect_args, pool_pre_ping=True)
                Base.metadata.create_all(bind=eng)
                _engine = eng
                _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
                _active_db_url = candidate_url
                ensure_real_assignments_exist()
                break
            except Exception as e:
                print(f"DB connection attempt failed for {candidate_url.split('@')[-1]}: {e}")
                continue
    return _SessionLocal()


def get_db_status():
    url = _active_db_url or get_database_url()
    is_neon = "neon.tech" in url or url.startswith("postgresql")
    return {
        "connected": True,
        "provider": "Neon Serverless Postgres (AWS us-east-2)" if is_neon else "SQLite Local DB",
        "is_postgres": is_neon,
    }


def ensure_real_assignments_exist():
    """
    Ensures the real assignment rubrics exist in Neon DB, WITHOUT any fake student submissions.
    Also removes any legacy dummy submissions (is_live == False) or old dummy batch IDs.
    """
    global _SessionLocal
    if _SessionLocal is None:
        return
    session = _SessionLocal()
    try:
        # Delete any old pre-seeded dummy submissions or legacy seta_project_mgmt rows
        deleted_dummy = session.query(SubmissionRecord).filter_by(is_live=False).delete()
        deleted_old_batch = session.query(BatchRecord).filter_by(id="seta_project_mgmt").delete()
        if deleted_dummy or deleted_old_batch:
            session.query(NotificationRecord).delete()
            session.query(SubmissionRecord).delete()
            session.commit()

        now_ts = time.time()
        for item in DEFAULT_REAL_ASSIGNMENTS:
            existing = session.query(BatchRecord).filter_by(id=item["id"]).first()
            if not existing:
                session.add(
                    BatchRecord(
                        id=item["id"],
                        title=item["title"],
                        programme_type=item["programme_type"],
                        default_goal=item["default_goal"],
                        rubric_json=json.dumps(item["rubric"]),
                        updated_at=now_ts,
                    )
                )
            else:
                existing.title = item["title"]
                existing.programme_type = item["programme_type"]
                existing.default_goal = item["default_goal"]
                existing.rubric_json = json.dumps(item["rubric"])
        session.commit()
        invalidate_batch_cache()
    except Exception as e:
        session.rollback()
        print("DB Init Error:", e)
    finally:
        session.close()


def wipe_all_submissions_and_users(reset_assignments=False):
    """
    Completely clears all submissions and notifications (and optionally users/custom assignments)
    so the database is 100% clean.
    """
    session = get_db_session()
    try:
        session.query(NotificationRecord).delete()
        session.query(SubmissionRecord).delete()
        if reset_assignments:
            session.query(BatchRecord).delete()
            session.query(UserRecord).delete()
        session.commit()
        invalidate_batch_cache()
        ensure_real_assignments_exist()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def register_or_login_user(name, email, password, role, school_or_cohort):
    session = get_db_session()
    try:
        email_clean = email.strip().lower()
        user = session.query(UserRecord).filter_by(email=email_clean).first()
        if user:
            if name.strip():
                user.name = name.strip()
            if school_or_cohort.strip():
                user.school_or_cohort = school_or_cohort.strip()
            user.role = role
            session.commit()
            return user.to_dict()
        else:
            new_user = UserRecord(
                name=name.strip(),
                email=email_clean,
                password=password,
                role=role,
                school_or_cohort=school_or_cohort.strip() or ("Grade 12 Cohort" if role == "learner" else "Lead Educator"),
                created_at=time.time(),
            )
            session.add(new_user)
            session.commit()
            return new_user.to_dict()
    finally:
        session.close()


def create_custom_assignment(title, programme_type, default_goal, rubric_dict):
    session = get_db_session()
    try:
        slug = "assign_" + str(int(time.time()))
        rec = BatchRecord(
            id=slug,
            title=title.strip(),
            programme_type=programme_type.strip(),
            default_goal=default_goal.strip(),
            rubric_json=json.dumps(rubric_dict),
            updated_at=time.time(),
        )
        session.add(rec)
        session.commit()
        invalidate_batch_cache()
        return slug
    finally:
        session.close()


def fetch_batch_dict(batch_id="caps_life_sciences"):
    if batch_id in _BATCH_CACHE:
        return copy.deepcopy(_BATCH_CACHE[batch_id])

    session = get_db_session()
    try:
        batch_rec = session.query(BatchRecord).filter_by(id=batch_id).first()
        if not batch_rec:
            batch_rec = session.query(BatchRecord).first()
            if not batch_rec:
                ensure_real_assignments_exist()
                batch_rec = session.query(BatchRecord).first()
            batch_id = batch_rec.id

        subs = (
            session.query(SubmissionRecord)
            .filter_by(batch_id=batch_id)
            .order_by(SubmissionRecord.created_at.desc(), SubmissionRecord.number.desc())
            .all()
        )
        sub_dicts = []
        for idx, s in enumerate(subs, start=1):
            d = s.to_dict()
            d["display_number"] = idx
            sub_dicts.append(d)

        all_batches = session.query(BatchRecord).order_by(BatchRecord.updated_at.desc()).all()
        available = []
        for b in all_batches:
            cnt = len(sub_dicts) if b.id == batch_id else session.query(SubmissionRecord).filter_by(batch_id=b.id).count()
            available.append({
                "id": b.id,
                "title": b.title,
                "programme_type": b.programme_type,
                "count": cnt,
            })

        notifs = (
            session.query(NotificationRecord)
            .filter_by(batch_id=batch_id)
            .order_by(NotificationRecord.id.desc())
            .limit(25)
            .all()
        )

        result = {
            "id": batch_rec.id,
            "title": batch_rec.title,
            "programme_type": batch_rec.programme_type,
            "default_goal": batch_rec.default_goal,
            "rubric": json.loads(batch_rec.rubric_json),
            "submissions": sub_dicts,
            "available_batches": available,
            "notifications": [n.to_dict() for n in notifs],
        }
        _BATCH_CACHE[batch_id] = copy.deepcopy(result)
        return result
    finally:
        session.close()


def save_live_submission(batch_id, evaluated_dict, learner_email=""):
    session = get_db_session()
    try:
        now_ts = time.time()
        now_str = datetime.now().strftime("%H:%M:%S SAST")
        total_existing = session.query(SubmissionRecord).filter_by(batch_id=batch_id).count()
        new_number = total_existing + 1
        sub_id = f"{batch_id}__SUB-{int(now_ts * 1000)}"

        rec = SubmissionRecord(
            id=sub_id,
            batch_id=batch_id,
            number=new_number,
            learner_name=evaluated_dict["learner_name"],
            learner_email=learner_email or f"{evaluated_dict['learner_name'].lower().replace(' ', '.')}@learner.edu.za",
            school_or_cohort=evaluated_dict["school_or_cohort"],
            submitted_at=now_str,
            essay_text=evaluated_dict["essay_text"],
            initial_mark_json=json.dumps(evaluated_dict["initial_mark"]),
            moderation_json=json.dumps(evaluated_dict["moderation"]),
            recovery_json=json.dumps(evaluated_dict["recovery"]),
            engine=evaluated_dict.get("engine", "colleague-zero-ai"),
            is_live=True,
            created_at=now_ts,
        )
        session.add(rec)

        init_score = evaluated_dict["initial_mark"]["score"]
        final_score = evaluated_dict["moderation"]["corrected_score"]
        flagged = evaluated_dict["moderation"]["flagged"]
        needs_rec = evaluated_dict["recovery"]["needs_recovery"]
        lname = evaluated_dict["learner_name"]

        # 1. Create Teacher Notification
        if flagged:
            t_title = f"⚡ [RV→MK Self-Corrected] {lname} (#{new_number}): {init_score}% → {final_score}%"
            t_msg = (
                f"Submission from {lname} was scored by [MK] at {init_score}%, "
                f"flagged by Moderator [RV] ({evaluated_dict['moderation']['flag_reason']}), "
                f"and self-corrected to {final_score}%."
            )
            t_badge = "warning"
        else:
            t_title = f"✅ [RV Verified] {lname} (#{new_number}) Graded at {final_score}%"
            t_msg = (
                f"Colleague Zero marked and moderated {lname}'s submission at {final_score}%. "
                f"{'3-Step Recovery Plan dispatched.' if needs_rec else 'Mastery feedback dispatched.'}"
            )
            t_badge = "success"

        session.add(
            NotificationRecord(
                batch_id=batch_id,
                recipient_role="teacher",
                learner_name=lname,
                submission_id=sub_id,
                title=t_title,
                message=t_msg,
                badge_type=t_badge,
                is_read=False,
                created_at=now_ts,
                time_label=now_str,
            )
        )

        # 2. Create Learner Notification
        if flagged:
            l_title = f"🛡️ Moderator Adjusted Your Mark: {init_score}% → {final_score}%"
        elif needs_rec:
            l_title = f"🛟 Assignment Graded ({final_score}%) — 3-Step Recovery Plan Ready"
        else:
            l_title = f"🎉 Assignment Graded & Verified: {final_score}%"

        session.add(
            NotificationRecord(
                batch_id=batch_id,
                recipient_role="learner",
                learner_name=lname,
                submission_id=sub_id,
                title=l_title,
                message=evaluated_dict["recovery"]["feedback"],
                badge_type="recovery" if needs_rec else "success",
                is_read=False,
                created_at=now_ts,
                time_label=now_str,
            )
        )

        session.commit()
        invalidate_batch_cache()
        return rec.to_dict()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def mark_notifications_read(batch_id, recipient_role):
    session = get_db_session()
    try:
        session.query(NotificationRecord).filter_by(
            batch_id=batch_id, recipient_role=recipient_role, is_read=False
        ).update({"is_read": True})
        session.commit()
        invalidate_batch_cache()
    finally:
        session.close()
