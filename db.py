"""
Database layer for Colleague Zero.
Supports Neon PostgreSQL (via DATABASE_URL in .env) out of the box,
and automatically falls back to a local SQLite database (colleague_zero.db)
until DATABASE_URL is configured.
"""

import copy
import json
import os
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from sample_data import BATCHES

Base = declarative_base()


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
    engine = Column(String(64), default="colleague-zero-core")
    is_live = Column(Boolean, default=False)
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
            "engine": self.engine or "colleague-zero-core",
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
    badge_type = Column(String(32), default="info")  # 'info', 'success', 'warning', 'recovery'
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


_engine = None
_SessionLocal = None
_active_db_url = None


def get_sqlite_fallback_url():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sqlite_path = os.path.join(base_dir, "colleague_zero.db")
    return f"sqlite:///{sqlite_path}"


def get_database_url():
    """
    Returns Neon PostgreSQL URL if DATABASE_URL is set in environment/.env,
    otherwise falls back to local SQLite colleague_zero.db.
    """
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
                seed_if_empty()
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


def seed_if_empty(force_reset=False):
    global _SessionLocal
    if _SessionLocal is None:
        return
    session = _SessionLocal()
    try:
        if force_reset:
            session.query(NotificationRecord).delete()
            session.query(SubmissionRecord).delete()
            session.query(BatchRecord).delete()
            session.commit()

        existing_count = session.query(BatchRecord).count()
        if existing_count > 0 and not force_reset:
            return

        now_ts = time.time()
        for batch_id, bdata in BATCHES.items():
            batch_rec = BatchRecord(
                id=batch_id,
                title=bdata["title"],
                programme_type=bdata["programme_type"],
                default_goal=bdata["default_goal"],
                rubric_json=json.dumps(bdata["rubric"]),
                updated_at=now_ts,
            )
            session.add(batch_rec)

            for idx, sub in enumerate(bdata["submissions"]):
                email_slug = sub["learner_name"].lower().replace(" ", ".")
                sub_rec = SubmissionRecord(
                    id=f"{batch_id}__{sub['id']}",
                    batch_id=batch_id,
                    number=sub["number"],
                    learner_name=sub["learner_name"],
                    learner_email=f"{email_slug}@learner.edu.za",
                    school_or_cohort=sub["school_or_cohort"],
                    submitted_at=sub["submitted_at"],
                    essay_text=sub["essay_text"],
                    initial_mark_json=json.dumps(sub["initial_mark"]),
                    moderation_json=json.dumps(sub["moderation"]),
                    recovery_json=json.dumps(sub["recovery"]),
                    engine=sub.get("engine", "colleague-zero-core"),
                    is_live=False,
                    created_at=now_ts - (len(bdata["submissions"]) - idx) * 60,
                )
                session.add(sub_rec)

            # Seed initial notifications so both portals look alive immediately
            flagged_subs = [s for s in bdata["submissions"] if s["moderation"]["flagged"]]
            recovery_subs = [s for s in bdata["submissions"] if s["recovery"]["needs_recovery"]]

            session.add(
                NotificationRecord(
                    batch_id=batch_id,
                    recipient_role="teacher",
                    learner_name="Colleague Zero",
                    submission_id=None,
                    title=f"Batch Moderated: {len(flagged_subs)} Rubric Discrepancies Self-Corrected",
                    message=(
                        f"Colleague Zero audited {len(bdata['submissions'])} scripts against {bdata['rubric']['version']}. "
                        f"RV flagged & fixed {len(flagged_subs)} marks and MS sent {len(recovery_subs)} recovery plans."
                    ),
                    badge_type="warning",
                    is_read=False,
                    created_at=now_ts - 30,
                    time_label="Recently",
                )
            )

            if bdata["submissions"]:
                first_sub = bdata["submissions"][0]
                session.add(
                    NotificationRecord(
                        batch_id=batch_id,
                        recipient_role="learner",
                        learner_name=first_sub["learner_name"],
                        submission_id=f"{batch_id}__{first_sub['id']}",
                        title=f"Mark Moderated & Verified: {first_sub['moderation']['corrected_score']}%",
                        message=first_sub["recovery"]["feedback"],
                        badge_type="success",
                        is_read=False,
                        created_at=now_ts - 20,
                        time_label="Recently",
                    )
                )

        session.commit()
    except Exception as e:
        session.rollback()
        print("DB Seed Error:", e)
    finally:
        session.close()


def fetch_batch_dict(batch_id="caps_life_sciences"):
    session = get_db_session()
    try:
        batch_rec = session.query(BatchRecord).filter_by(id=batch_id).first()
        if not batch_rec:
            batch_id = "caps_life_sciences"
            batch_rec = session.query(BatchRecord).filter_by(id=batch_id).first()

        subs = (
            session.query(SubmissionRecord)
            .filter_by(batch_id=batch_id)
            .order_by(SubmissionRecord.is_live.desc(), SubmissionRecord.created_at.desc(), SubmissionRecord.number.asc())
            .all()
        )
        # Keep numbering clean: live submissions at top get #1, etc. or preserve script number
        sub_dicts = []
        for idx, s in enumerate(subs, start=1):
            d = s.to_dict()
            d["display_number"] = idx
            sub_dicts.append(d)

        all_batches = session.query(BatchRecord).all()
        available = []
        for b in all_batches:
            cnt = session.query(SubmissionRecord).filter_by(batch_id=b.id).count()
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

        return {
            "id": batch_rec.id,
            "title": batch_rec.title,
            "programme_type": batch_rec.programme_type,
            "default_goal": batch_rec.default_goal,
            "rubric": json.loads(batch_rec.rubric_json),
            "submissions": sub_dicts,
            "available_batches": available,
            "notifications": [n.to_dict() for n in notifs],
        }
    finally:
        session.close()


def save_live_submission(batch_id, evaluated_dict, learner_email=""):
    session = get_db_session()
    try:
        now_ts = time.time()
        now_str = datetime.now().strftime("%H:%M SAST · LIVE")
        total_existing = session.query(SubmissionRecord).filter_by(batch_id=batch_id).count()
        new_number = total_existing + 1
        sub_id = f"{batch_id}__LIVE-{int(now_ts * 1000)}"

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
            engine=evaluated_dict.get("engine", "colleague-zero-core"),
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
                f"New submission from {lname} was auto-assessed by [MK] at {init_score}%, "
                f"flagged by Moderator [RV] ({evaluated_dict['moderation']['flag_reason']}), "
                f"and self-corrected to {final_score}% with 0 human intervention."
            )
            t_badge = "warning"
        else:
            t_title = f"✅ [RV Verified] {lname} (#{new_number}) Graded at {final_score}%"
            t_msg = (
                f"Colleague Zero autonomously marked and moderated {lname}'s submission at {final_score}%. "
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
                time_label="Just now",
            )
        )

        # 2. Create Learner Notification
        if flagged:
            l_title = f"🛡️ Moderator Protected Your Mark! Final Score: {final_score}% (Up from {init_score}%)"
        elif needs_rec:
            l_title = f"🛟 Assignment Graded ({final_score}%) + 3-Step Catch-Up Plan Ready"
        else:
            l_title = f"🎉 Assignment Graded & Moderated: {final_score}%"

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
                time_label="Just now",
            )
        )

        session.commit()
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
    finally:
        session.close()

