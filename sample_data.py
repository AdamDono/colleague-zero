"""
Realistic South African CAPS & SETA assessment batches for Colleague Zero.
Includes rubrics, learner submissions, and edge-case scripts designed to test
autonomous Assessor -> Moderator self-correction loops and Learner Recovery plans.
"""

BATCHES = {
    "caps_life_sciences": {
        "id": "caps_life_sciences",
        "title": "Grade 12 CAPS Life Sciences — Meiosis & Genetic Variation",
        "programme_type": "NSC CAPS · Grade 12 Term 1 Essay",
        "default_goal": (
            "Mark all 12 Grade 12 Life Sciences essays against CAPS Rubric v2, "
            "moderate for grading consistency and ESL fairness, self-correct any "
            "rubric discrepancies, and send personalised feedback with remedial "
            "catch-up plans to every learner."
        ),
        "rubric": {
            "version": "CAPS Rubric v2.4 (DBE Paper 2)",
            "total_marks": 100,
            "pass_mark": 50,
            "criteria": [
                {
                    "id": "C1",
                    "name": "Criterion 1: Crossing-Over in Prophase I",
                    "weight": 30,
                    "description": "Explains homologous chromosome pairing (bivalents), chiasmata formation, and exchange of genetic material between non-sister chromatids."
                },
                {
                    "id": "C2",
                    "name": "Criterion 2: Random Arrangement in Metaphase I & II",
                    "weight": 30,
                    "description": "Explains independent assortment of homologous chromosomes at the equator during Metaphase I and chromatids in Metaphase II."
                },
                {
                    "id": "C3",
                    "name": "Criterion 3: Biological Significance & Halving Chromosome Number",
                    "weight": 25,
                    "description": "Explains how diploid (2n) becomes haploid (n) gametes and prevents chromosome doubling across generations."
                },
                {
                    "id": "C4",
                    "name": "Criterion 4: Logical Synthesis & Scientific Accuracy",
                    "weight": 15,
                    "description": "Coherent structure, correct distinction between meiosis I and II, and absence of factual contradictions."
                }
            ]
        },
        "submissions": [
            {
                "id": "SUB-01",
                "number": 1,
                "learner_name": "Thabo Mokoena",
                "school_or_cohort": "Orlando West Secondary · Gr 12A",
                "submitted_at": "08:14 SAST",
                "essay_text": (
                    "During Prophase I of meiosis, homologous chromosomes pair up to form bivalents. "
                    "Non-sister chromatids overlap at points called chiasmata and swap segments of DNA in a process called crossing-over, "
                    "creating new allele combinations. In Metaphase I, homologous chromosome pairs line up randomly along the equator, "
                    "so maternal and paternal chromosomes separate independently into daughter cells. "
                    "Meiosis also reduces the chromosome number from diploid (2n=46) to haploid (n=23) in gametes so that when fertilisation occurs, "
                    "the normal diploid number is restored in the zygote."
                ),
                "initial_mark": {
                    "score": 88,
                    "criteria_scores": {"C1": 28, "C2": 26, "C3": 22, "C4": 12},
                    "rationale": "Strong coverage of crossing-over, chiasmata, independent assortment, and diploid-to-haploid reduction."
                },
                "moderation": {
                    "flagged": False,
                    "flag_reason": None,
                    "corrected_score": 88,
                    "corrected_criteria_scores": {"C1": 28, "C2": 26, "C3": 22, "C4": 12},
                    "correction_log": "Verified against CAPS Rubric v2.4: All 4 criteria accurately scored."
                },
                "recovery": {
                    "feedback": "Excellent essay, Thabo! You clearly explained chiasmata in Prophase I and random arrangement in Metaphase I. To reach 95%+, explicitly mention random arrangement of single chromosomes in Metaphase II as well.",
                    "needs_recovery": False,
                    "catchup_plan": [
                        "Stretch Task: Compare Metaphase I (bivalents at equator) vs Metaphase II (individual chromosomes at equator) in a 2-column table."
                    ]
                }
            },
            {
                "id": "SUB-02",
                "number": 2,
                "learner_name": "Amahle Dlamini",
                "school_or_cohort": "Umlazi ComTech · Gr 12B",
                "submitted_at": "08:16 SAST",
                "essay_text": (
                    "Meiosis makes sex cells. In Prophase I chromosomes cross over and share genes. "
                    "However, I struggle to remember the difference between Metaphase I and Anaphase I. "
                    "At the end of meiosis there are 4 cells that are different from each other."
                ),
                "initial_mark": {
                    "score": 38,
                    "criteria_scores": {"C1": 14, "C2": 6, "C3": 10, "C4": 8},
                    "rationale": "Mentions crossing-over briefly without naming bivalents or chiasmata; misses random arrangement at the equator and haploid/diploid halving."
                },
                "moderation": {
                    "flagged": False,
                    "flag_reason": None,
                    "corrected_score": 38,
                    "corrected_criteria_scores": {"C1": 14, "C2": 6, "C3": 10, "C4": 8},
                    "correction_log": "Confirmed 38%. Criterion 2 and Criterion 3 omissions require targeted learner recovery."
                },
                "recovery": {
                    "feedback": "Amahle, you correctly identified that crossing-over happens in Prophase I and produces 4 genetically distinct cells! However, you missed key marks on chiasmata, random arrangement in Metaphase I/II, and halving the chromosome number from diploid (2n) to haploid (n).",
                    "needs_recovery": True,
                    "catchup_plan": [
                        "Step 1 (Concept Drill): Review the 3 keywords for Prophase I: Homologous pair (bivalent) → Chiasma → Non-sister chromatid exchange.",
                        "Step 2 (Visual Comparison): Draw Metaphase I showing pairs lined up randomly on either side of the equator line.",
                        "Step 3 (Quick Recovery Check): Explain in 2 sentences why gametes must have 23 chromosomes (n) instead of 46 (2n)."
                    ]
                }
            },
            {
                "id": "SUB-03",
                "number": 3,
                "learner_name": "Sipho Ndlovu",
                "school_or_cohort": "Khayelitsha STEM High · Gr 12A",
                "submitted_at": "08:19 SAST",
                "essay_text": (
                    "In Prophase 1 the matching chromosome partners from mom and dad hug each other tightly as a bivalent and touch at the chiasma point, "
                    "swapping pieces of their chromatid legs so the DNA mixes up. Then in Metaphase 1 and 2, the chromosome pairs don't follow a fixed queue "
                    "at the middle equator line—they line up in any random left-or-right order, which shuffles the deck of genes even more. "
                    "Also, meiosis cuts the full 46 chromosome set in half to 23 (haploid) in sperm and egg cells so the baby still gets 46 when they fuse."
                ),
                "initial_mark": {
                    "score": 44,
                    "criteria_scores": {"C1": 14, "C2": 12, "C3": 12, "C4": 6},
                    "rationale": "Informal phrasing ('hug each other', 'shuffles the deck') penalized heavily for lack of textbook register."
                },
                "moderation": {
                    "flagged": True,
                    "flag_reason": "Essay #3 scored 44% due to informal analogy penalty, but accurately satisfies Criteria 1, 2, and 3 (names bivalent, chiasma, chromatid exchange, random equator arrangement in Metaphase I & II, and 46→23 haploid reduction).",
                    "corrected_score": 76,
                    "corrected_criteria_scores": {"C1": 24, "C2": 23, "C3": 20, "C4": 9},
                    "correction_log": "Re-marked #3 against CAPS Rubric v2.4: 44% → 76% (+32%). CAPS marking guidelines award full conceptual credit when scientific terms (bivalent, chiasma, equator, haploid) are present alongside analogies."
                },
                "recovery": {
                    "feedback": "Great conceptual understanding, Sipho! Your explanation of bivalents, chiasmata, random arrangement at the equator, and cutting chromosomes from 46 to 23 is spot on. To score 85%+ in the final NSC exam, pair your analogies with formal phrases like 'independent assortment of homologous chromosomes'.",
                    "needs_recovery": False,
                    "catchup_plan": [
                        "Exam Polish Tip: Replace 'hug each other' with 'synapsis of homologous chromosomes' while keeping your clear explanation of chiasmata."
                    ]
                }
            },
            {
                "id": "SUB-04",
                "number": 4,
                "learner_name": "Kagiso Molefe",
                "school_or_cohort": "Mamelodi Senior Secondary · Gr 12C",
                "submitted_at": "08:21 SAST",
                "essay_text": (
                    "Genetic variation is introduced in two main ways during meiosis. First, crossing-over occurs in Prophase I when homologous chromosomes "
                    "form bivalents and exchange genetic segments at the chiasmata. Second, random arrangement of chromosomes at the equator during Metaphase I "
                    "and Metaphase II leads to independent assortment of alleles into gametes. Finally, meiosis halves the chromosome number from diploid to haploid "
                    "so chromosome numbers stay constant from generation to generation."
                ),
                "initial_mark": {
                    "score": 92,
                    "criteria_scores": {"C1": 28, "C2": 28, "C3": 23, "C4": 13},
                    "rationale": "Comprehensive, well-structured CAPS essay covering all four rubric dimensions accurately."
                },
                "moderation": {
                    "flagged": False,
                    "flag_reason": None,
                    "corrected_score": 92,
                    "corrected_criteria_scores": {"C1": 28, "C2": 28, "C3": 23, "C4": 13},
                    "correction_log": "Verified against CAPS Rubric v2.4: High distinction confirmed."
                },
                "recovery": {
                    "feedback": "Outstanding distinction (92%), Kagiso! Your breakdown of Prophase I chiasmata, Metaphase I & II random arrangement, and diploid-to-haploid reduction is exam-ready.",
                    "needs_recovery": False,
                    "catchup_plan": [
                        "Extension Challenge: Practice a past-paper question on non-disjunction during Anaphase I leading to Trisomy 21."
                    ]
                }
            },
            {
                "id": "SUB-05",
                "number": 5,
                "learner_name": "Zanele Khumalo",
                "school_or_cohort": "Soshanguve High · Gr 12A",
                "submitted_at": "08:25 SAST",
                "essay_text": (
                    "In Prophase I homologous chromosomes pair as bivalents and non-sister chromatids exchange DNA segments at chiasmata. "
                    "During Metaphase I bivalents position themselves randomly on the equator, and in Metaphase II single chromosomes also arrange randomly "
                    "(which is why gametes end up haploid n=23 instead of diploid 2n=46, keeping species chromosome count stable across generations after fertilisation)."
                ),
                "initial_mark": {
                    "score": 56,
                    "criteria_scores": {"C1": 26, "C2": 22, "C3": 0, "C4": 8},
                    "rationale": "Good C1 and C2, but awarded 0/25 for Criterion 3 because paragraph 2 was only parsed as Metaphase mechanics."
                },
                "moderation": {
                    "flagged": True,
                    "flag_reason": "Essay #5 scored 56% (0/25 on Criterion 3), but the parenthetical clause explicitly states haploid (n=23) vs diploid (2n=46) and species chromosome stability after fertilisation.",
                    "corrected_score": 81,
                    "corrected_criteria_scores": {"C1": 26, "C2": 22, "C3": 21, "C4": 12},
                    "correction_log": "Re-marked #5 against CAPS Rubric v2.4: 56% → 81% (+25%). Criterion 3 points were embedded in the final clause and missed on initial pass."
                },
                "recovery": {
                    "feedback": "Well done, Zanele! All your scientific facts on chiasmata, random arrangement, and haploid (n=23) gamete formation are accurate. Tip: Put your diploid-to-haploid explanation in its own short paragraph so human exam markers never miss it!",
                    "needs_recovery": False,
                    "catchup_plan": [
                        "Formatting Tip: Separate Variation Mechanisms (Prophase I / Metaphase I & II) and Chromosome Number Halving into two distinct paragraphs."
                    ]
                }
            },
            {
                "id": "SUB-06",
                "number": 6,
                "learner_name": "Lerato Sithole",
                "school_or_cohort": "Boksburg High · Gr 12B",
                "submitted_at": "08:28 SAST",
                "essay_text": (
                    "Crossing-over happens in Prophase I when homologous chromosomes exchange genetic material at the chiasmata. "
                    "This makes the chromatids genetically different. However, I did not finish the rest of the essay on Metaphase and chromosome numbers."
                ),
                "initial_mark": {
                    "score": 35,
                    "criteria_scores": {"C1": 25, "C2": 0, "C3": 4, "C4": 6},
                    "rationale": "Strong Criterion 1 (Prophase I crossing-over), but Criterion 2 and Criterion 3 are incomplete."
                },
                "moderation": {
                    "flagged": False,
                    "flag_reason": None,
                    "corrected_score": 35,
                    "corrected_criteria_scores": {"C1": 25, "C2": 0, "C3": 4, "C4": 6},
                    "correction_log": "Verified 35%. Incomplete submission on C2 and C3 flagged for Learner Recovery plan."
                },
                "recovery": {
                    "feedback": "Lerato, your Prophase I explanation earned 25/30! You only lost marks because you ran out of time before covering Metaphase I/II random arrangement and diploid-to-haploid halving.",
                    "needs_recovery": True,
                    "catchup_plan": [
                        "Step 1 (Metaphase I & II): Write 3 bullet points explaining how bivalents arrange randomly on the equator in Metaphase I.",
                        "Step 2 (Haploid Reduction): Write 2 sentences explaining how meiosis I reduces chromosome number from 2n to n.",
                        "Step 3 (5-Min Timed Drill): Practice writing all 3 paragraphs in under 12 minutes."
                    ]
                }
            },
            {
                "id": "SUB-07",
                "number": 7,
                "learner_name": "Liam van Wyk",
                "school_or_cohort": "Bellville High · Gr 12A",
                "submitted_at": "08:30 SAST",
                "essay_text": (
                    "Meiosis is a vital process of cell division in the human body that produces four daughter cells. "
                    "During Prophase I, homologous chromosomes pair up into bivalents and undergo crossing-over at the chiasmata, "
                    "exchanging DNA between non-sister chromatids to create genetic diversity. "
                    "Furthermore, the cells divide twice to create four genetically unique cells with high biological importance for evolution and survival."
                ),
                "initial_mark": {
                    "score": 74,
                    "criteria_scores": {"C1": 27, "C2": 20, "C3": 16, "C4": 11},
                    "rationale": "Well-written scientific prose; awarded partial marks across C2 and C3."
                },
                "moderation": {
                    "flagged": True,
                    "flag_reason": "Essay #7 scored 74% (halo effect from fluent prose), but completely omits Criterion 2 (random arrangement in Metaphase I/II) and does not mention haploid (n) vs diploid (2n) in Criterion 3.",
                    "corrected_score": 48,
                    "corrected_criteria_scores": {"C1": 27, "C2": 0, "C3": 11, "C4": 10},
                    "correction_log": "Re-marked #7 against CAPS Rubric v2.4: 74% → 48% (-26%). Removed unearned C2 marks; triggered Learner Recovery plan for Metaphase I/II."
                },
                "recovery": {
                    "feedback": "Liam, your Prophase I crossing-over paragraph is excellent (27/30). However, our moderator noticed you completely skipped Metaphase I & II random arrangement and didn't specify diploid (2n) to haploid (n) chromosome reduction.",
                    "needs_recovery": True,
                    "catchup_plan": [
                        "Step 1 (Missing Mechanism): Add a paragraph on Random Arrangement of homologous chromosomes at the equator in Metaphase I & II (worth 30%).",
                        "Step 2 (Precision Terms): Explicitly state 'diploid (2n) to haploid (n)' when discussing gamete formation.",
                        "Step 3 (Re-Submit Check): Complete the 2-question Metaphase checkpoint."
                    ]
                }
            },
            {
                "id": "SUB-08",
                "number": 8,
                "learner_name": "Naledi Mthembu",
                "school_or_cohort": "Soweto Science Academy · Gr 12A",
                "submitted_at": "08:33 SAST",
                "essay_text": (
                    "In Prophase I, homologous chromosomes pair up and exchange genetic material at chiasmata during crossing-over. "
                    "In Metaphase I, bivalents line up randomly at the equator, and in Metaphase II individual chromosomes arrange randomly, "
                    "leading to independent assortment. Meiosis reduces the chromosome number from diploid (2n) to haploid (n) so gametes have half "
                    "the chromosomes, preventing doubling at fertilisation."
                ),
                "initial_mark": {
                    "score": 86,
                    "criteria_scores": {"C1": 26, "C2": 27, "C3": 21, "C4": 12},
                    "rationale": "Clear, accurate coverage of all four CAPS rubric criteria."
                },
                "moderation": {
                    "flagged": False,
                    "flag_reason": None,
                    "corrected_score": 86,
                    "corrected_criteria_scores": {"C1": 26, "C2": 27, "C3": 21, "C4": 12},
                    "correction_log": "Verified 86% against CAPS Rubric v2.4."
                },
                "recovery": {
                    "feedback": "Fantastic work, Naledi (86%)! You nailed all three core mechanisms accurately and concisely.",
                    "needs_recovery": False,
                    "catchup_plan": [
                        "Enrichment: Specify 'non-sister chromatids' in Prophase I to lock in 100% on Criterion 1."
                    ]
                }
            }
        ]
    },
    "seta_project_mgmt": {
        "id": "seta_project_mgmt",
        "title": "SETA NQF Level 4 — Workplace Project Risk & Scope PoE",
        "programme_type": "Services SETA US-120372 · Formative PoE Batch",
        "default_goal": (
            "Assess all 6 NQF Level 4 Workplace PoE submissions against SETA Unit Standard 120372, "
            "perform internal moderation to catch assessor discrepancies, and issue NYC (Not Yet Competent) "
            "remedial recovery plans."
        ),
        "rubric": {
            "version": "SETA US-120372 Assessment Guide v3.1",
            "total_marks": 100,
            "pass_mark": 60,
            "criteria": [
                {
                    "id": "C1",
                    "name": "SO1: Identify & Classify Workplace Project Risks",
                    "weight": 35,
                    "description": "Identifies at least 3 concrete project risks and classifies probability and impact."
                },
                {
                    "id": "C2",
                    "name": "SO2: Formulate Preventative & Contingency Actions",
                    "weight": 35,
                    "description": "Provides actionable mitigation controls and named risk owners for each identified risk."
                },
                {
                    "id": "C3",
                    "name": "SO3: Stakeholder Escalation & Scope Governance",
                    "weight": 30,
                    "description": "Defines change-request procedure and communication protocol when scope creep occurs."
                }
            ]
        },
        "submissions": [
            {
                "id": "SETA-01",
                "number": 1,
                "learner_name": "Mandla Zulu",
                "school_or_cohort": "Gauteng Youth Learnership Cohort 4",
                "submitted_at": "09:02 SAST",
                "essay_text": (
                    "For our IT rollout project, the three main risks are: (1) Fibre link delay (High probability, High impact), "
                    "(2) Staff resistance to the new POS software (Medium probability, High impact), and (3) Power outages during migration (High probability, Medium impact). "
                    "To mitigate these, the Network Lead will pre-order LTE failover routers 14 days early, the Training Officer will run hands-on floor workshops, "
                    "and the Site Supervisor will schedule cutover on UPS-backed shifts. Any scope additions must go through a signed Change Control Form approved by the Project Sponsor."
                ),
                "initial_mark": {
                    "score": 91,
                    "criteria_scores": {"C1": 33, "C2": 32, "C3": 26},
                    "rationale": "Competent across SO1, SO2, and SO3 with concrete workplace evidence."
                },
                "moderation": {
                    "flagged": False,
                    "flag_reason": None,
                    "corrected_score": 91,
                    "corrected_criteria_scores": {"C1": 33, "C2": 32, "C3": 26},
                    "correction_log": "SETA Internal Moderation: Competent (C) judgement confirmed."
                },
                "recovery": {
                    "feedback": "Competent (91%)! Excellent practical risk register with clear risk owners and formal Change Control governance.",
                    "needs_recovery": False,
                    "catchup_plan": [
                        "PoE Sign-off: Ready for external SETA verifier audit."
                    ]
                }
            },
            {
                "id": "SETA-02",
                "number": 2,
                "learner_name": "Precious Mahlangu",
                "school_or_cohort": "Gauteng Youth Learnership Cohort 4",
                "submitted_at": "09:08 SAST",
                "essay_text": (
                    "In our warehouse stock-system project: Risk 1 is barcode scanner delivery delay (Med/High) -> Logistics Coordinator will use rental scanners as backup. "
                    "Risk 2 is wrong SKU data import (High/High) -> Data Clerk will run a 50-item sandbox test before go-live. "
                    "Risk 3 is load-shedding halting training (High/Med) -> Facilitator will use printed job-aids and offline tablets. "
                    "When a manager asks for extra dashboard features mid-sprint, we log a Scope Change Request and get Steering Committee sign-off before adding hours."
                ),
                "initial_mark": {
                    "score": 49,
                    "criteria_scores": {"C1": 18, "C2": 16, "C3": 15},
                    "rationale": "Marked NYC (49%) because submission used arrow shorthand ('->') instead of a formal table layout."
                },
                "moderation": {
                    "flagged": True,
                    "flag_reason": "Submission #2 scored 49% (NYC) due to formatting style, yet includes 3 classified risks (SO1), 3 named owners + contingencies (SO2), and Steering Committee Scope Change sign-off (SO3).",
                    "corrected_score": 84,
                    "corrected_criteria_scores": {"C1": 30, "C2": 29, "C3": 25},
                    "correction_log": "Re-marked #2 against SETA US-120372: 49% (NYC) → 84% (Competent). SETA assessment principles assess evidence against Specific Outcomes, not typography."
                },
                "recovery": {
                    "feedback": "Competent (84%), Precious! Your risk classifications, contingency owners, and Steering Committee change-control process meet all three Specific Outcomes.",
                    "needs_recovery": False,
                    "catchup_plan": [
                        "PoE Filing Note: Evidence satisfies SO1–SO3; attached to final Portfolio of Evidence."
                    ]
                }
            },
            {
                "id": "SETA-03",
                "number": 3,
                "learner_name": "Bongani Khoza",
                "school_or_cohort": "Gauteng Youth Learnership Cohort 4",
                "submitted_at": "09:15 SAST",
                "essay_text": (
                    "Projects have many risks like running out of budget, people being late, or computers breaking. "
                    "We must work hard and communicate well with the team so the project finishes on time."
                ),
                "initial_mark": {
                    "score": 32,
                    "criteria_scores": {"C1": 14, "C2": 10, "C3": 8},
                    "rationale": "Generic statements; lacks risk probability/impact classification, named owners, and scope change governance."
                },
                "moderation": {
                    "flagged": False,
                    "flag_reason": None,
                    "corrected_score": 32,
                    "corrected_criteria_scores": {"C1": 14, "C2": 10, "C3": 8},
                    "correction_log": "SETA Internal Moderation: Confirmed 32% (Not Yet Competent). Remedial evidence required."
                },
                "recovery": {
                    "feedback": "Not Yet Competent (32%), Bongani. You identified general risks (budget, schedule, equipment), but SETA Unit Standard 120372 requires rating Probability/Impact, naming who owns each mitigation action, and explaining how you handle Scope Creep.",
                    "needs_recovery": True,
                    "catchup_plan": [
                        "Step 1 (SO1 Remediation): Rate each of your 3 risks as High/Medium/Low Probability and Impact.",
                        "Step 2 (SO2 Remediation): Assign a specific workplace role (e.g., IT Technician, Project Admin) and a concrete backup action to each risk.",
                        "Step 3 (SO3 Remediation): Write 2 sentences explaining how a Change Request Form prevents unapproved scope changes."
                    ]
                }
            }
        ]
    }
}
