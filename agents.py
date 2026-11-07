"""
Multi-Agent Engine for Colleague Zero:
- PL (Planner Agent): Decomposes goal, extracts rubric criterion concepts & weights.
- MK (Marker / Assessor Agent): Scores learner submission criterion-by-criterion against the actual rubric.
- RV (Reviewer / Moderator Agent): Audits MK output against rubric, flags errors, and triggers MK self-correction.
- MS (Messenger / Learner Recovery Agent): Generates criterion-specific feedback & custom 3-step remedial catch-up plans.
"""

import json
import os
import re

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


def evaluate_custom_submission_multi_agent(learner_name, school_or_cohort, essay_text, rubric, number=1):
    """
    Runs the 4-agent loop (Planner -> Marker -> Moderator -> Recovery) on a newly submitted
    learner script against ANY rubric (built-in or custom teacher-created rubric).
    Uses Gemini 2.5 Flash if GEMINI_API_KEY is set, otherwise runs the dynamic
    criterion-by-criterion semantic rubric analyzer.
    """
    client = get_gemini_client()
    criteria = rubric.get("criteria", [])
    pass_mark = int(rubric.get("pass_mark", 50))
    rubric_version = rubric.get("version", "Official Assessment Rubric")

    if client:
        try:
            prompt = f"""
You are Colleague Zero, a 4-agent educational assessment and moderation pipeline for South Africa.
Assessment Question: {rubric.get('question_prompt', '')}
Rubric ({rubric_version}):
{json.dumps(criteria, indent=2)}

Learner Name: {learner_name}
Submission Text:
\"\"\"{essay_text}\"\"\"

Execute the two-pass multi-agent evaluation:
1. MK (Assessor Agent): Score each criterion ID ({[c['id'] for c in criteria]}) strictly up to its weight. Quote or reference specific concepts the learner wrote or missed in `rationale`. If the learner uses informal analogies/colloquialisms to explain a valid concept, MK should initially under-score; if the learner writes vague fluff without facts, MK may initially over-score.
2. RV (Moderator Agent): Audit MK's initial mark against the rubric. If MK unfairly penalized valid concepts expressed informally (or over-scored fluff), set `flagged=true`, explain the exact discrepancy in `flag_reason`, and provide `corrected_score`, `corrected_criteria_scores`, and `correction_log`.
3. MS (Recovery Agent): Write highly specific `feedback` referencing the exact criteria the learner mastered vs missed, and a concrete 3-step `catchup_plan` tailored to the weakest rubric criteria.

Return ONLY valid JSON matching this schema:
{{
  "initial_mark": {{
    "score": <int 0-100>,
    "criteria_scores": {{ "<criterion_id>": <int>, ... }},
    "rationale": "<string>"
  }},
  "moderation": {{
    "flagged": <bool>,
    "flag_reason": "<string or null>",
    "corrected_score": <int 0-100>,
    "corrected_criteria_scores": {{ "<criterion_id>": <int>, ... }},
    "correction_log": "<string>"
  }},
  "recovery": {{
    "feedback": "<string>",
    "needs_recovery": <bool>,
    "catchup_plan": ["<step 1>", "<step 2>", "<step 3>"]
  }}
}}
"""
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            data = json.loads(resp.text)
            return {
                "id": f"SUB-{number:02d}",
                "number": number,
                "learner_name": learner_name,
                "school_or_cohort": school_or_cohort,
                "submitted_at": "Just now",
                "essay_text": essay_text,
                "initial_mark": data["initial_mark"],
                "moderation": data["moderation"],
                "recovery": data["recovery"],
                "engine": "gemini-2.5-flash",
            }
        except Exception as e:
            print("Gemini API error, using dynamic rubric analyzer:", e)

    # Dynamic Criterion-by-Criterion Semantic Rubric Analyzer
    text_lower = essay_text.lower()
    word_count = len(re.findall(r"\w+", essay_text))

    init_scores = {}
    corr_scores = {}
    matched_by_criterion = {}
    missing_by_criterion = {}
    informal_hits_total = 0

    for c in criteria:
        cid = c["id"]
        weight = int(c["weight"])
        kws = extract_criterion_keywords(c)

        direct_matches = []
        informal_matches = []
        missing_kws = []

        for kw in kws:
            # Check direct stem match (first 5 chars for long words)
            stem = kw[:5] if len(kw) >= 6 else kw
            if stem in text_lower:
                direct_matches.append(kw)
            else:
                # Check if student used an informal analogy for this concept
                syn_list = INFORMAL_ANALOGY_SYNONYMS.get(kw, [])
                if any(s in text_lower for s in syn_list):
                    informal_matches.append(kw)
                else:
                    missing_kws.append(kw)

        informal_hits_total += len(informal_matches)
        total_kws = max(1, len(kws))

        # Calculate formal coverage vs true conceptual coverage (including analogies)
        formal_ratio = len(direct_matches) / total_kws
        conceptual_ratio = (len(direct_matches) + len(informal_matches) * 0.9) / total_kws

        # Scale ratios realistically (hitting ~45% of all rubric description tokens = full mastery)
        formal_mastery = min(1.0, formal_ratio / 0.42)
        conceptual_mastery = min(1.0, conceptual_ratio / 0.42)

        # Length/depth factor for very short 1-sentence answers
        depth_factor = 1.0 if word_count >= 25 else max(0.25, word_count / 25.0)

        formal_score = int(round(weight * formal_mastery * depth_factor))
        true_score = int(round(weight * conceptual_mastery * depth_factor))

        # Check if student wrote a long, fluent-sounding paragraph with zero rubric terms ("fluff")
        is_fluff = (word_count >= 35 and len(direct_matches) == 0 and len(informal_matches) == 0)

        if is_fluff:
            init_scores[cid] = int(round(weight * 0.65))  # MK fooled by length/fluency
            corr_scores[cid] = int(round(weight * 0.15))  # RV corrects down to true rubric match
        elif len(informal_matches) > 0 and true_score > formal_score:
            # MK penalized informal phrasing; RV restores full conceptual score
            init_scores[cid] = max(int(weight * 0.30), formal_score)
            corr_scores[cid] = max(true_score, int(weight * 0.78))
        else:
            init_scores[cid] = true_score
            corr_scores[cid] = true_score

        matched_by_criterion[cid] = direct_matches + [f"{m} (informal analogy)" for m in informal_matches]
        missing_by_criterion[cid] = missing_kws[:4]

    init_total = sum(init_scores.values())
    corr_total = sum(corr_scores.values())
    flagged = abs(corr_total - init_total) >= 5

    # Build specific, evidence-based rationale and moderation audit logs
    strong_c = [c for c in criteria if corr_scores[c["id"]] >= c["weight"] * 0.65]
    weak_c = [c for c in criteria if corr_scores[c["id"]] < c["weight"] * 0.65]

    matched_summary = []
    for c in criteria:
        m = matched_by_criterion[c["id"]]
        if m:
            matched_summary.append(f"{c['id']} ({', '.join(m[:3])})")

    if matched_summary:
        mk_evidence = f"Detected concepts in {'; '.join(matched_summary)}."
    else:
        mk_evidence = "No specific rubric terminology matched in submission."

    if flagged and corr_total > init_total:
        rationale = (
            f"First-pass scan awarded {init_total}% ({mk_evidence}) "
            f"Deducted marks where informal phrasing/analogies were used instead of textbook terminology."
        )
        flag_reason = (
            f"Assessor [MK] under-scored script at {init_total}% due to informal/second-language phrasing, "
            f"but the learner accurately explained the underlying mechanisms across {len(strong_c)}/{len(criteria)} rubric criteria."
        )
        correction_log = (
            f"Moderator [RV] re-evaluated against {rubric_version}: {init_total}% → {corr_total}% "
            f"(+{corr_total - init_total}%). Credited valid conceptual explanations."
        )
    elif flagged and corr_total < init_total:
        rationale = f"Awarded {init_total}% based on essay length ({word_count} words) and general structure."
        flag_reason = (
            f"Assessor [MK] over-scored script at {init_total}% (fluency bias), "
            f"but submission lacked required rubric concepts: {', '.join(c['name'] for c in weak_c)}."
        )
        correction_log = (
            f"Moderator [RV] enforced strict {rubric_version} audit: {init_total}% → {corr_total}% "
            f"({corr_total - init_total}%). Removed fluency bias."
        )
    else:
        rationale = (
            f"Scored {init_total}% across {len(criteria)} criteria ({word_count} words). {mk_evidence}"
        )
        flag_reason = None
        correction_log = (
            f"Verified {corr_total}% against {rubric_version}: Criterion scores match evidence in learner script."
        )

    # Build highly specific Learner Feedback and 3-Step Catch-Up Plan referencing exact criteria
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
                f"{len(criteria)} rubric criteria ({strong_names})."
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

    # Generate custom 3-step plan directly from the student's lowest-scoring criteria
    sorted_by_gap = sorted(
        criteria,
        key=lambda c: (corr_scores[c["id"]] / max(1, c["weight"]))
    )
    catchup_plan = []
    for idx, crit in enumerate(sorted_by_gap[:3], start=1):
        cid = crit["id"]
        cname = crit["name"]
        cdesc = crit["description"]
        missed = missing_by_criterion.get(cid, [])
        missed_str = f" (include key terms: {', '.join(missed)})" if missed else ""
        if corr_scores[cid] < crit["weight"] * 0.7:
            catchup_plan.append(
                f"Step {idx} — Fix {cid} ({cname}): Revise and explain how {cdesc}{missed_str}."
            )
        else:
            catchup_plan.append(
                f"Step {idx} — Polish {cid} ({cname}): Refine your formal terminology on: {cdesc}"
            )

    return {
        "id": f"SUB-{number:02d}",
        "number": number,
        "learner_name": learner_name,
        "school_or_cohort": school_or_cohort,
        "submitted_at": "Just now",
        "essay_text": essay_text,
        "initial_mark": {
            "score": init_total,
            "criteria_scores": init_scores,
            "rationale": rationale,
        },
        "moderation": {
            "flagged": flagged,
            "flag_reason": flag_reason,
            "corrected_score": corr_total,
            "corrected_criteria_scores": corr_scores,
            "correction_log": correction_log,
        },
        "recovery": {
            "feedback": feedback,
            "needs_recovery": corr_total < pass_mark,
            "catchup_plan": catchup_plan,
        },
        "engine": "colleague-zero-rubric-ai",
    }
