"""
Database layer for Colleague Zero — Connected to Neon Serverless PostgreSQL.
Tables in Neon DB:
- `users`: Real Learner & Educator accounts
- `batches`: Real Assignments & Rubrics
- `submissions`: Real Learner Submissions with multi-agent worker outputs
- `agent_events`: Real step-by-step execution logs produced by PL, MK, RV, and MS workers
- `notifications`: Real notifications for Learner and Educator portals
"""

import copy
import json
import os
import threading
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
            "created_at": self.created_at,
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
    engine = Column(String(64), default="colleague-zero-4-workers")
    is_live = Column(Boolean, default=True)
    created_at = Column(Float, default=lambda: time.time())

    def to_dict(self):
        init_data = json.loads(self.initial_mark_json)
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "number": self.number,
            "learner_name": self.learner_name,
            "learner_email": self.learner_email or "",
            "school_or_cohort": self.school_or_cohort,
            "submitted_at": self.submitted_at,
            "essay_text": self.essay_text,
            "worker_status": init_data.get("worker_status", "completed"),
            "initial_mark": init_data,
            "moderation": json.loads(self.moderation_json),
            "recovery": json.loads(self.recovery_json),
            "engine": self.engine or "colleague-zero-4-workers",
            "is_live": bool(self.is_live),
            "created_at": self.created_at,
        }


class AgentEventRecord(Base):
    __tablename__ = "agent_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), nullable=False, index=True)
    submission_id = Column(String(64), nullable=True, index=True)
    agent_code = Column(String(16), nullable=False)  # 'PL', 'MK', 'RV', 'MS'
    tag = Column(String(32), nullable=False)
    message = Column(Text, nullable=False)
    time_label = Column(String(64), nullable=False)
    created_at = Column(Float, default=lambda: time.time())

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "submission_id": self.submission_id,
            "agent_code": self.agent_code,
            "tag": self.tag,
            "message": self.message,
            "time_label": self.time_label,
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
_USERS_CACHE = []


def invalidate_batch_cache():
    global _BATCH_CACHE
    _BATCH_CACHE.clear()


def get_database_url():
    raw_url = (os.getenv("DATABASE_URL") or "").strip()
    if raw_url:
        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif raw_url.startswith("postgresql://") and "+psycopg2" not in raw_url:
            raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return raw_url
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return f"sqlite:///{os.path.join(base_dir, 'colleague_zero.db')}"


def get_db_session():
    global _engine, _SessionLocal, _active_db_url
    target_url = get_database_url()
    if _engine is None:
        urls_to_try = [target_url]
        if "channel_binding=require" in target_url:
            urls_to_try.append(target_url.replace("&channel_binding=require", "").replace("channel_binding=require&", ""))

        for candidate_url in urls_to_try:
            try:
                connect_args = (
                    {"check_same_thread": False}
                    if candidate_url.startswith("sqlite")
                    else {"connect_timeout": 15, "keepalives": 1, "keepalives_idle": 20, "keepalives_interval": 10, "keepalives_count": 5}
                )
                eng = create_engine(
                    candidate_url,
                    connect_args=connect_args,
                    pool_pre_ping=True,
                    pool_recycle=120,
                    pool_size=5,
                    max_overflow=10,
                )
                Base.metadata.create_all(bind=eng)
                _engine = eng
                _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
                _active_db_url = candidate_url
                ensure_real_assignments_exist()
                break
            except Exception as e:
                print(f"Neon DB connection attempt error: {e}")
                continue
    if _SessionLocal is None:
        return None
    return _SessionLocal()


def get_db_status():
    url = _active_db_url or get_database_url()
    is_neon = "neon.tech" in url or url.startswith("postgresql")
    return {
        "connected": _engine is not None,
        "provider": "Neon Serverless Postgres" if is_neon else "Local DB",
        "is_postgres": is_neon,
    }


def ensure_real_assignments_exist():
    global _SessionLocal, _USERS_CACHE
    if _SessionLocal is None:
        return
    session = _SessionLocal()
    try:
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

        session.query(UserRecord).filter(
            UserRecord.email.in_(["sibusiso.tshabalala@student.edu.za", "sibusiso.tshabalala@learner.edu.za"])
        ).delete(synchronize_session=False)

        session.commit()
        users = session.query(UserRecord).order_by(UserRecord.id.desc()).all()
        _USERS_CACHE = [u.to_dict() for u in users]
        invalidate_batch_cache()
    except Exception as e:
        session.rollback()
        print("DB Init Error:", e)
    finally:
        session.close()


def register_or_login_user(name, email, password, role, school_or_cohort):
    global _USERS_CACHE
    email_clean = email.strip().lower()
    user_dict = {
        "id": len(_USERS_CACHE) + 1,
        "name": name.strip(),
        "email": email_clean,
        "role": role,
        "school_or_cohort": school_or_cohort.strip() or ("Grade 12 Cohort" if role == "learner" else "Lead Educator"),
        "created_at": time.time(),
    }

    session = get_db_session()
    if session is None:
        return user_dict
    try:
        user = session.query(UserRecord).filter_by(email=email_clean).first()
        if user:
            if name.strip():
                user.name = name.strip()
            if school_or_cohort.strip():
                user.school_or_cohort = school_or_cohort.strip()
            user.role = role
            session.commit()
            res = user.to_dict()
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
            res = new_user.to_dict()

        users = session.query(UserRecord).order_by(UserRecord.id.desc()).all()
        _USERS_CACHE = [u.to_dict() for u in users]
        return res
    except Exception as e:
        session.rollback()
        print("register_or_login_user DB warning:", e)
        return user_dict
    finally:
        session.close()


def list_all_users():
    global _USERS_CACHE
    session = get_db_session()
    if session is None:
        return _USERS_CACHE
    try:
        users = session.query(UserRecord).order_by(UserRecord.id.desc()).all()
        _USERS_CACHE = [u.to_dict() for u in users]
        return _USERS_CACHE
    except Exception:
        return _USERS_CACHE
    finally:
        session.close()


def commit_worker_pipeline_run(batch_id, learner_name, learner_email, school_or_cohort, evaluated_dict, worker_events):
    """
    Commits the entire 4-worker execution run (UserRecord, SubmissionRecord, all 4+ AgentEventRecords,
    and Learner + Educator NotificationRecords) to Neon PostgreSQL in a SINGLE fast transaction!
    Never hangs or fails partway through.
    """
    now_ts = time.time()
    now_str = datetime.now().strftime("%H:%M:%S SAST")
    sub_id = f"{batch_id}__SUB-{int(now_ts * 1000)}"

    # Update in-memory cache immediately so UI is instant even if network has latency
    cached_batch = _BATCH_CACHE.get(batch_id)
    new_number = (len(cached_batch["submissions"]) + 1) if cached_batch else evaluated_dict.get("number", 1)

    sub_payload = {
        "id": sub_id,
        "batch_id": batch_id,
        "number": new_number,
        "learner_name": learner_name,
        "learner_email": learner_email or "",
        "school_or_cohort": school_or_cohort,
        "submitted_at": now_str,
        "essay_text": evaluated_dict["essay_text"],
        "worker_status": "completed",
        "initial_mark": evaluated_dict["initial_mark"],
        "moderation": evaluated_dict["moderation"],
        "recovery": evaluated_dict["recovery"],
        "engine": evaluated_dict.get("engine", "colleague-zero-4-workers"),
        "is_live": True,
        "created_at": now_ts,
    }

    init_score = evaluated_dict["initial_mark"]["score"]
    final_score = evaluated_dict["moderation"]["corrected_score"]
    flagged = evaluated_dict["moderation"]["flagged"]
    needs_rec = evaluated_dict["recovery"]["needs_recovery"]

    if flagged:
        t_title = f"⚡ [RV→MK Self-Corrected] {learner_name} (#{new_number}): {init_score}% → {final_score}%"
        t_msg = (
            f"Assessor Worker [MK] scored {learner_name} at {init_score}%. "
            f"Moderator Worker [RV] flagged it ({evaluated_dict['moderation']['flag_reason']}) "
            f"and triggered [MK] Pass-2 re-evaluation to {final_score}%."
        )
        t_badge = "warning"
        l_title = f"🛡️ Moderator Adjusted Your Mark: {init_score}% → {final_score}%"
    else:
        t_title = f"✅ [RV Verified] {learner_name} (#{new_number}) Graded at {final_score}%"
        t_msg = (
            f"Workers [PL → MK → RV → MS] assessed and verified {learner_name}'s submission at {final_score}%. "
            f"{'3-Step Recovery Plan dispatched.' if needs_rec else 'Mastery feedback dispatched.'}"
        )
        t_badge = "success"
        l_title = (
            f"🛟 Assignment Graded ({final_score}%) — 3-Step Recovery Plan Ready"
            if needs_rec
            else f"🎉 Assignment Graded & Verified: {final_score}%"
        )

    session = get_db_session()
    if session is not None:
        try:
            total_existing = session.query(SubmissionRecord).filter_by(batch_id=batch_id).count()
            new_number = total_existing + 1
            sub_payload["number"] = new_number

            # 1. Upsert User if email provided
            if learner_email:
                email_clean = learner_email.strip().lower()
                existing_user = session.query(UserRecord).filter_by(email=email_clean).first()
                if not existing_user:
                    session.add(
                        UserRecord(
                            name=learner_name,
                            email=email_clean,
                            password="learner_verified",
                            role="learner",
                            school_or_cohort=school_or_cohort,
                            created_at=now_ts,
                        )
                    )

            # 2. Insert SubmissionRecord
            rec = SubmissionRecord(
                id=sub_id,
                batch_id=batch_id,
                number=new_number,
                learner_name=learner_name,
                learner_email=learner_email or "",
                school_or_cohort=school_or_cohort,
                submitted_at=now_str,
                essay_text=evaluated_dict["essay_text"],
                initial_mark_json=json.dumps(evaluated_dict["initial_mark"]),
                moderation_json=json.dumps(evaluated_dict["moderation"]),
                recovery_json=json.dumps(evaluated_dict["recovery"]),
                engine=evaluated_dict.get("engine", "colleague-zero-4-workers"),
                is_live=True,
                created_at=now_ts,
            )
            session.add(rec)

            # 3. Insert all 4 Worker AgentEventRecords
            for ev in worker_events:
                session.add(
                    AgentEventRecord(
                        batch_id=batch_id,
                        submission_id=sub_id,
                        agent_code=ev["agent_code"],
                        tag=ev["tag"],
                        message=ev["message"].replace("#1", f"#{new_number}"),
                        time_label=ev["time_label"],
                        created_at=now_ts,
                    )
                )

            # 4. Insert Educator & Learner NotificationRecords
            session.add(
                NotificationRecord(
                    batch_id=batch_id,
                    recipient_role="teacher",
                    learner_name=learner_name,
                    submission_id=sub_id,
                    title=t_title,
                    message=t_msg,
                    badge_type=t_badge,
                    is_read=False,
                    created_at=now_ts,
                    time_label=now_str,
                )
            )
            session.add(
                NotificationRecord(
                    batch_id=batch_id,
                    recipient_role="learner",
                    learner_name=learner_name,
                    submission_id=sub_id,
                    title=l_title,
                    message=evaluated_dict["recovery"]["feedback"],
                    badge_type="recovery" if needs_rec else "success",
                    is_read=False,
                    created_at=now_ts,
                    time_label=now_str,
                )
            )

            # Commit everything in ONE single round-trip to Neon PostgreSQL!
            session.commit()
            invalidate_batch_cache()
            return rec.to_dict()
        except Exception as e:
            session.rollback()
            print("Neon DB single-transaction commit warning:", e)
        finally:
            session.close()

    # Fallback cache update if network momentarily dropped
    if batch_id in _BATCH_CACHE:
        _BATCH_CACHE[batch_id]["submissions"].insert(0, sub_payload)
        for ev in worker_events:
            _BATCH_CACHE[batch_id]["agent_events"].append(ev)
    return sub_payload


def create_custom_assignment(title, programme_type, default_goal, rubric_dict):
    slug = "assign_" + str(int(time.time()))
    session = get_db_session()
    if session is not None:
        try:
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
        except Exception as e:
            session.rollback()
            print("create_custom_assignment error:", e)
        finally:
            session.close()
    return slug


def _build_fallback_batch_dict(batch_id="caps_life_sciences"):
    item = next((a for a in DEFAULT_REAL_ASSIGNMENTS if a["id"] == batch_id), DEFAULT_REAL_ASSIGNMENTS[0])
    return {
        "id": item["id"],
        "title": item["title"],
        "programme_type": item["programme_type"],
        "default_goal": item["default_goal"],
        "rubric": copy.deepcopy(item["rubric"]),
        "submissions": [],
        "available_batches": [
            {"id": a["id"], "title": a["title"], "programme_type": a["programme_type"], "count": 0}
            for a in DEFAULT_REAL_ASSIGNMENTS
        ],
        "notifications": [],
        "agent_events": [],
        "users_count": len(_USERS_CACHE),
    }


def fetch_batch_dict(batch_id="caps_life_sciences"):
    if batch_id in _BATCH_CACHE:
        return copy.deepcopy(_BATCH_CACHE[batch_id])

    session = get_db_session()
    if session is None:
        return _build_fallback_batch_dict(batch_id)

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

        events = (
            session.query(AgentEventRecord)
            .filter_by(batch_id=batch_id)
            .order_by(AgentEventRecord.id.desc())
            .limit(30)
            .all()
        )

        users_count = session.query(UserRecord).count()

        result = {
            "id": batch_rec.id,
            "title": batch_rec.title,
            "programme_type": batch_rec.programme_type,
            "default_goal": batch_rec.default_goal,
            "rubric": json.loads(batch_rec.rubric_json),
            "submissions": sub_dicts,
            "available_batches": available,
            "notifications": [n.to_dict() for n in notifs],
            "agent_events": [e.to_dict() for e in reversed(events)],
            "users_count": users_count,
        }
        _BATCH_CACHE[batch_id] = copy.deepcopy(result)
        return result
    except Exception as e:
        print("fetch_batch_dict resilient fallback:", e)
        if batch_id in _BATCH_CACHE:
            return copy.deepcopy(_BATCH_CACHE[batch_id])
        return _build_fallback_batch_dict(batch_id)
    finally:
        session.close()


def wipe_all_submissions_and_users(reset_assignments=False):
    invalidate_batch_cache()
    session = get_db_session()
    if session is None:
        return
    try:
        session.query(AgentEventRecord).delete()
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
        print("wipe error:", e)
    finally:
        session.close()


def mark_notifications_read(batch_id, recipient_role):
    if batch_id in _BATCH_CACHE:
        for n in _BATCH_CACHE[batch_id].get("notifications", []):
            if n.get("recipient_role") == recipient_role:
                n["is_read"] = True
    session = get_db_session()
    if session is None:
        return
    try:
        session.query(NotificationRecord).filter_by(
            batch_id=batch_id, recipient_role=recipient_role, is_read=False
        ).update({"is_read": True})
        session.commit()
        invalidate_batch_cache()
    except Exception:
        session.rollback()
    finally:
        session.close()
