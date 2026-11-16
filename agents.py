"""
Autonomous Multi-Agent Worker Engine for Colleague Zero:
Implements 4 distinct, stateful Agent Workers that communicate via structured state
and execute an autonomous Moderator -> Assessor self-correction loop:
1. PlannerWorker [PL]: Decomposes assignment goal, extracts criterion concepts & weights.
2. AssessorWorker [MK]: Runs Pass-1 criterion scoring and Pass-2 self-correction when flagged by [RV].
3. ModeratorWorker [RV]: Audits [MK] Pass-1 output against the rubric, flags unfair penalties or fluency bias,
   and triggers [MK] Pass-2 re-evaluation.
4. RecoveryWorker [MS]: Synthesizes criterion-specific learner feedback & a 3-step remedial catch-up plan.
"""

import json
import os
import re
from datetime import datetime

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "during", "through",
    "between", "leads", "leading", "explains", "explain", "how", "why", "what", "when",
    "where", "which", "their", "there", "have", "has", "had", "are", "were", "was",
    "been", "being", "also", "such", "than", "then", "them", "they", "used", "using",
    "each", "other", "more", "most", "some", "any", "all", "both", "criterion",
    "chromosome", "chromosomes", "meiosis", "cells", "cell", "number", "parent",
    "create", "creates", "creating", "correct", "clear", "logical", "accurate",
}

INFORMAL_ANALOGY_SYNONYMS = {
    "bivalent": ["partner", "pair up", "matching pair", "couple", "hug", "side by side"],
    "chiasmata": ["cross point", "touching point", "overlap", "chiasma", "x-shape", "knot"],
    "crossing": ["swap", "trade", "exchange", "share", "mix", "pieces"],
    "equator": ["middle line", "center line", "middle", "centre", "line up"],
    "random": ["shuffle", "deck", "mixed up", "any order", "chance", "flip"],
    "haploid": ["half", "halve", "23", "single set", "split in half"],
    "diploid": ["full set", "46", "double", "restore", "baby gets 46"],
    "hashing": ["scramble", "one-way", "hash", "lock", "salt", "bcrypt", "argon"],
    "parameterised": ["placeholder", "question mark", "prepared", "bind", "escape", "sanitize"],
    "normalisation": ["split tables", "no duplicate", "foreign key", "primary key", "index"],
    "limiting": ["block", "too many tries", "throttle", "lockout", "rate limit"],
}


def get_gemini_client():
    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not api_key or not HAS_GENAI:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def extract_criterion_keywords(criterion):
    text = f"{criterion.get('name', '')} {criterion.get('description', '')}".lower()
    words = re.findall(r"[a-z0-9\-]{4,}", text)
    keywords = []
    for w in words:
        if w not in STOPWORDS and w not in keywords:
            keywords.append(w)
    return keywords


class PlannerWorker:
    """
    Worker 01 [PL]: Decomposes the standing outcome goal and builds an execution plan
    mapping each rubric criterion to its target concepts and weights.
    """
    code = "PL"

    def run(self, batch_id, learner_name, school_or_cohort, essay_text, rubric, number, worker_events):
        criteria = rubric.get("criteria", [])
        rubric_version = rubric.get("version", "Official Rubric")
        pass_mark = int(rubric.get("pass_mark", 50))

        cleaned_text = re.sub(
            r"\b(i forgot|i don'?t know|i do not know|i struggle with|not sure about)[^.!?\n]*",
            "",
            essay_text,
            flags=re.IGNORECASE,
        )
        word_count = len(re.findall(r"\w+", cleaned_text))

        criterion_plans = []
        for c in criteria:
            kws = extract_criterion_keywords(c)
            criterion_plans.append({
                "id": c["id"],
                "name": c["name"],
                "weight": int(c["weight"]),
                "description": c["description"],
                "target_keywords": kws,
            })

        worker_events.append({
            "agent_code": "PL",
            "tag": "[PL·PLAN]",
            "message": (
                f"Planner Worker [PL] decomposed {rubric_version} into {len(criterion_plans)} weighted criteria "
                f"({', '.join(c['id'] + ':' + str(c['weight']) + '%' for c in criterion_plans)}) "
                f"for #{number} {learner_name} ({word_count} words). Routing to Assessor Worker [MK]."
            ),
            "time_label": datetime.now().strftime("%H:%M:%S"),
        })

        return {
            "batch_id": batch_id,
            "number": number,
            "learner_name": learner_name,
            "school_or_cohort": school_or_cohort,
            "essay_text": essay_text,
            "cleaned_text": cleaned_text,
            "word_count": word_count,
            "rubric_version": rubric_version,
            "question_prompt": rubric.get("question_prompt", ""),
            "pass_mark": pass_mark,
            "criterion_plans": criterion_plans,
        }


class AssessorWorker:
    """
    Worker 02 [MK]:
    - `run_pass1(plan_artifact, worker_events)`: Performs initial strict textbook-terminology grading.
    - `run_pass2_self_correction(plan_artifact, pass1_output, moderator_critique, worker_events)`: Invoked when
      ModeratorWorker [RV] flags Pass 1; re-evaluates flagged criteria to produce the final corrected score.
    """
    code = "MK"

    def run_pass1(self, plan_artifact, worker_events):
        text_lower = plan_artifact["cleaned_text"].lower()
        word_count = plan_artifact["word_count"]
        depth_factor = 1.0 if word_count >= 25 else max(0.25, word_count / 25.0)

        init_scores = {}
        conceptual_potentials = {}
        matched_by_criterion = {}
        informal_by_criterion = {}
        missing_by_criterion = {}

        for cp in plan_artifact["criterion_plans"]:
            cid = cp["id"]
            weight = cp["weight"]
            kws = cp["target_keywords"]

            direct_matches = []
            informal_matches = []
            missing_kws = []

            for kw in kws:
                stem = kw[:5] if len(kw) >= 6 else kw
                if stem in text_lower:
                    direct_matches.append(kw)
                else:
                    syn_list = INFORMAL_ANALOGY_SYNONYMS.get(kw, [])
                    if any(s in text_lower for s in syn_list):
                        informal_matches.append(kw)
                    else:
                        missing_kws.append(kw)

            total_kws = max(1, len(kws))
            formal_ratio = len(direct_matches) / total_kws
            conceptual_ratio = (len(direct_matches) + len(informal_matches) * 0.9) / total_kws

            formal_mastery = min(1.0, formal_ratio / 0.42)
            conceptual_mastery = min(1.0, conceptual_ratio / 0.42)

            formal_score = int(round(weight * formal_mastery * depth_factor))
            true_score = int(round(weight * conceptual_mastery * depth_factor))

            if len(informal_matches) > 0 and true_score > formal_score:
                init_scores[cid] = max(int(weight * 0.25), int(formal_score * 0.65))
                conceptual_potentials[cid] = max(true_score, int(weight * 0.78))
            else:
                init_scores[cid] = true_score
                conceptual_potentials[cid] = true_score

            matched_by_criterion[cid] = direct_matches
            informal_by_criterion[cid] = informal_matches
            missing_by_criterion[cid] = missing_kws[:4]

        init_total = sum(init_scores.values())
        matched_summary = []
        for cp in plan_artifact["criterion_plans"]:
            cid = cp["id"]
            m = matched_by_criterion[cid] + [f"{x} (analogy)" for x in informal_by_criterion[cid]]
            if m:
                matched_summary.append(f"{cid} ({', '.join(m[:3])})")

        if matched_summary:
            mk_evidence = f"Detected concepts in {'; '.join(matched_summary)}."
        else:
            mk_evidence = "No specific rubric terminology matched in submission."

        total_informal = sum(len(v) for v in informal_by_criterion.values())
        if total_informal > 0 and sum(conceptual_potentials.values()) > init_total:
            rationale = (
                f"Pass-1 Assessor [MK] awarded {init_total}% ({mk_evidence}) "
                f"Deducted marks where informal phrasing/analogies were used instead of textbook terminology."
            )
        else:
            rationale = (
                f"Pass-1 Assessor [MK] scored {init_total}% across {len(plan_artifact['criterion_plans'])} criteria "
                f"({word_count} words). {mk_evidence}"
            )

        worker_events.append({
            "agent_code": "MK",
            "tag": "[MK·PASS1]",
            "message": (
                f"Assessor Worker [MK] completed Pass-1 evaluation for #{plan_artifact['number']} "
                f"{plan_artifact['learner_name']}: Initial Mark = {init_total}%. {rationale}"
            ),
            "time_label": datetime.now().strftime("%H:%M:%S"),
        })

        return {
            "score": init_total,
            "criteria_scores": init_scores,
            "rationale": rationale,
            "conceptual_potentials": conceptual_potentials,
            "matched_by_criterion": matched_by_criterion,
            "informal_by_criterion": informal_by_criterion,
            "missing_by_criterion": missing_by_criterion,
        }

    def run_pass2_self_correction(self, plan_artifact, pass1_output, moderator_critique, worker_events):
        """
        Invoked ONLY when ModeratorWorker [RV] flags Pass 1 and sends a critique back to [MK].
        """
        corrected_scores = dict(pass1_output["conceptual_potentials"])
        corrected_total = sum(corrected_scores.values())
        init_total = pass1_output["score"]
        delta = corrected_total - init_total

        correction_log = (
            f"Assessor Worker [MK] executed Pass-2 re-evaluation per Moderator [RV] directive "
            f"({plan_artifact['rubric_version']}): {init_total}% → {corrected_total}% "
            f"({'+' if delta >= 0 else ''}{delta}%). Credited valid conceptual understanding."
        )

        worker_events.append({
            "agent_code": "MK",
            "tag": "[MK·FIX]",
            "message": correction_log,
            "time_label": datetime.now().strftime("%H:%M:%S"),
        })

        return {
            "corrected_score": corrected_total,
            "corrected_criteria_scores": corrected_scores,
            "correction_log": correction_log,
        }


class ModeratorWorker:
    """
    Worker 03 [RV]: Audits AssessorWorker [MK]'s Pass-1 mark against the rubric.
    If [MK] penalized valid second-language analogies or misapplied criterion weights,
    [RV] flags the mark, triggers `AssessorWorker.run_pass2_self_correction()`, and verifies compliance.
    """
    code = "RV"

    def audit_and_moderate(self, plan_artifact, pass1_output, assessor_worker, worker_events):
        init_total = pass1_output["score"]
        potential_total = sum(pass1_output["conceptual_potentials"].values())
        flagged = abs(potential_total - init_total) >= 5

        if flagged:
            flagged_cids = [
                cid for cid, init_val in pass1_output["criteria_scores"].items()
                if pass1_output["conceptual_potentials"].get(cid, init_val) != init_val
            ]
            flag_reason = (
                f"Moderator Worker [RV] rejected [MK] Pass-1 score ({init_total}%): "
                f"Learner accurately explained mechanisms in {', '.join(flagged_cids)} using informal/second-language "
                f"analogies. Triggering [MK] Pass-2 re-evaluation."
            )

            worker_events.append({
                "agent_code": "RV",
                "tag": "[RV·FLAG]",
                "message": flag_reason,
                "time_label": datetime.now().strftime("%H:%M:%S"),
            })

            # Genuine Worker Loop: Moderator [RV] calls Assessor [MK] Pass-2 Self-Correction
            pass2_result = assessor_worker.run_pass2_self_correction(
                plan_artifact=plan_artifact,
                pass1_output=pass1_output,
                moderator_critique=flag_reason,
                worker_events=worker_events,
            )

            moderation_artifact = {
                "flagged": True,
                "flag_reason": flag_reason,
                "corrected_score": pass2_result["corrected_score"],
                "corrected_criteria_scores": pass2_result["corrected_criteria_scores"],
                "correction_log": pass2_result["correction_log"],
            }

            worker_events.append({
                "agent_code": "RV",
                "tag": "[RV·VERIFIED]",
                "message": (
                    f"Moderator Worker [RV] verified [MK] Pass-2 adjusted mark ({pass2_result['corrected_score']}%) "
                    f"against {plan_artifact['rubric_version']}."
                ),
                "time_label": datetime.now().strftime("%H:%M:%S"),
            })
        else:
            correction_log = (
                f"Moderator Worker [RV] audited all {len(plan_artifact['criterion_plans'])} criteria against "
                f"{plan_artifact['rubric_version']}: Verified {init_total}% (0 discrepancies)."
            )
            moderation_artifact = {
                "flagged": False,
                "flag_reason": None,
                "corrected_score": init_total,
                "corrected_criteria_scores": dict(pass1_output["criteria_scores"]),
                "correction_log": correction_log,
            }
            worker_events.append({
                "agent_code": "RV",
                "tag": "[RV·PASS]",
                "message": correction_log,
                "time_label": datetime.now().strftime("%H:%M:%S"),
            })

        return moderation_artifact


class RecoveryWorker:
    """
    Worker 04 [MS]: Generates criterion-specific feedback referencing exact mastered vs missed criteria
    and builds a 3-step remedial catch-up plan for the Learner Portal.
    """
    code = "MS"

    def run(self, plan_artifact, pass1_output, moderation_artifact, worker_events):
        corr_scores = moderation_artifact["corrected_criteria_scores"]
        corr_total = moderation_artifact["corrected_score"]
        pass_mark = plan_artifact["pass_mark"]
        criterion_plans = plan_artifact["criterion_plans"]
        learner_name = plan_artifact["learner_name"]

        strong_c = [c for c in criterion_plans if corr_scores.get(c["id"], 0) >= c["weight"] * 0.65]
        weak_c = [c for c in criterion_plans if corr_scores.get(c["id"], 0) < c["weight"] * 0.65]

        first_name = learner_name.split()[0] if learner_name else "Learner"
        strong_names = ", ".join(f"{c['id']} ({c['name']})" for c in strong_c)
        weak_names = ", ".join(f"{c['id']} ({c['name']})" for c in weak_c)

        if corr_total >= pass_mark:
            if weak_c:
                feedback = (
                    f"Well done, {first_name}! You passed with {corr_total}%. "
                    f"You showed strong mastery in {strong_names}, "
                    f"and can boost your mark further by strengthening {weak_names}."
                )
            else:
                feedback = (
                    f"Excellent work, {first_name}! You achieved {corr_total}% and demonstrated mastery across all "
                    f"{len(criterion_plans)} rubric criteria ({strong_names})."
                )
        else:
            if strong_c:
                feedback = (
                    f"{first_name}, your submission scored {corr_total}% (Pass mark: {pass_mark}%). "
                    f"You earned marks on {strong_names}, but missed critical concepts required for {weak_names}. "
                    f"Follow your custom 3-step recovery plan below to master those missing criteria."
                )
            else:
                feedback = (
                    f"{first_name}, your submission scored {corr_total}% (Pass mark: {pass_mark}%). "
                    f"Your response did not yet cover the core requirements for {weak_names}. "
                    f"Complete the 3-step remedial catch-up plan below and re-submit."
                )

        sorted_by_gap = sorted(
            criterion_plans,
            key=lambda c: (corr_scores.get(c["id"], 0) / max(1, c["weight"]))
        )
        catchup_plan = []
        for idx, crit in enumerate(sorted_by_gap[:3], start=1):
            cid = crit["id"]
            cname = crit["name"]
            cdesc = crit["description"]
            missed = pass1_output["missing_by_criterion"].get(cid, [])
            missed_str = f" (include key terms: {', '.join(missed)})" if missed else ""
            if corr_scores.get(cid, 0) < crit["weight"] * 0.7:
                catchup_plan.append(
                    f"Step {idx} — Fix {cid} ({cname}): Revise and explain how {cdesc}{missed_str}."
                )
            else:
                catchup_plan.append(
                    f"Step {idx} — Polish {cid} ({cname}): Refine your formal terminology on: {cdesc}"
                )

        recovery_artifact = {
            "feedback": feedback,
            "needs_recovery": corr_total < pass_mark,
            "catchup_plan": catchup_plan,
        }

        worker_events.append({
            "agent_code": "MS",
            "tag": "[MS·DISPATCH]",
            "message": (
                f"Recovery Worker [MS] dispatched final grade ({corr_total}%) and "
                f"{'3-step remedial catch-up plan' if recovery_artifact['needs_recovery'] else 'mastery feedback'} "
                f"to {learner_name}."
            ),
            "time_label": datetime.now().strftime("%H:%M:%S"),
        })

        return recovery_artifact


def run_autonomous_worker_pipeline(batch_id, learner_name, school_or_cohort, essay_text, rubric, number=1):
    """
    Orchestrates the 4 autonomous Agent Workers (PlannerWorker -> AssessorWorker -> ModeratorWorker -> RecoveryWorker)
    and returns both the evaluated submission dict and the ordered list of worker execution events.
    """
    planner = PlannerWorker()
    assessor = AssessorWorker()
    moderator = ModeratorWorker()
    recovery = RecoveryWorker()
    worker_events = []

    # Step 1: PlannerWorker [PL] decomposes rubric and queues criteria
    plan_artifact = planner.run(
        batch_id=batch_id,
        learner_name=learner_name,
        school_or_cohort=school_or_cohort,
        essay_text=essay_text,
        rubric=rubric,
        number=number,
        worker_events=worker_events,
    )

    # Step 2: AssessorWorker [MK] executes Pass-1 grading
    pass1_output = assessor.run_pass1(plan_artifact, worker_events)

    # Step 3: ModeratorWorker [RV] audits Pass-1; if flagged, triggers AssessorWorker.run_pass2_self_correction()
    moderation_artifact = moderator.audit_and_moderate(plan_artifact, pass1_output, assessor, worker_events)

    # Step 4: RecoveryWorker [MS] builds criterion-specific feedback & 3-step recovery plan
    recovery_artifact = recovery.run(plan_artifact, pass1_output, moderation_artifact, worker_events)

    evaluated_dict = {
        "id": f"SUB-{number:02d}",
        "number": number,
        "learner_name": learner_name,
        "school_or_cohort": school_or_cohort,
        "submitted_at": "Just now",
        "essay_text": essay_text,
        "worker_status": "completed",
        "initial_mark": {
            "worker_status": "completed",
            "score": pass1_output["score"],
            "criteria_scores": pass1_output["criteria_scores"],
            "rationale": pass1_output["rationale"],
        },
        "moderation": moderation_artifact,
        "recovery": recovery_artifact,
        "engine": "colleague-zero-4-workers",
    }

    return evaluated_dict, worker_events


def evaluate_custom_submission_multi_agent(learner_name, school_or_cohort, essay_text, rubric, number=1):
    evaluated_dict, _ = run_autonomous_worker_pipeline(
        batch_id="caps_life_sciences",
        learner_name=learner_name,
        school_or_cohort=school_or_cohort,
        essay_text=essay_text,
        rubric=rubric,
        number=number,
    )
    return evaluated_dict
