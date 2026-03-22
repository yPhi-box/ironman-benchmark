# IRONMAN Scoring Rules

**This document governs ALL benchmark scoring. No exceptions. No adjustments. No "recalculations."**

If the scoring rules need to change, update THIS document FIRST, then re-run ALL tests. Never change scoring after seeing results.

---

## Core Rule

**What the test returns is what gets reported.** Raw output only. No manual adjustments, no post-hoc exclusions, no "corrected" scores.

---

## How a Query is Scored

1. System receives a query
2. System returns up to 5 results (chunks of text)
3. All 5 results are concatenated into one string
4. The expected answer text is checked against that string
5. **Pass** = expected text found (case-insensitive substring match)
6. **Fail** = expected text not found
7. No partial credit. Binary pass/fail.

---

## How Categories are Scored

- Each query belongs to one category
- Category score = (passed / total) × 100
- **Every category is shown in the report, every time, for every system**
- If a category has 0 queries for a tier, show "n/a"
- If a system scores 0%, show 0%
- If a system scores 100%, show 100%
- **Never exclude, zero, or adjust a category score after the fact**

---

## How Overall Score is Calculated

- Overall = (total passed across ALL categories) / (total queries) × 100
- All categories count equally toward the overall score
- No weighting, no exclusions

---

## How Grades are Assigned

| Grade | Range | Meaning |
|-------|-------|---------|
| S | 70%+ | Exceptional |
| A | 55–69% | Outstanding |
| B | 40–54% | Strong |
| C | 30–39% | Competitive |
| D | 20–29% | Below average |
| F | <20% | Failing |

---

## Latency

- Measured per query (wall clock, milliseconds)
- Report: average, P50 (median), P95
- Latency does NOT affect the score or grade

---

## Known Scoring Limitations

These are documented, not "fixed" by adjusting scores:

1. **Negative/adversarial inflation**: A system that returns nothing passes all "question has no answer" queries by default. This is a flaw in the test design, NOT something to correct in the score. Document it with a ⚠️ flag.

2. **Adversarial penalty for active systems**: A system that always returns results scores 0% on adversarial because returning anything = fail. Same flaw, opposite direction. Document with ⚠️.

3. **Exact text matching misses**: The scorer uses substring matching. If the system retrieves the correct information but the expected answer is phrased differently, it scores as a fail. This is a known limitation of binary scoring vs LLM-judge scoring.

4. **Evidence-based scoring (LoCoMo/Workspace)**: When using evidence mapping instead of answer text, the same rules apply — check if evidence text appears in results. Still binary pass/fail.

---

## Rules for Report Publishing

1. Show raw scores for every system, every tier, every category
2. Flag known issues with ⚠️ — never hide them
3. If scoring rules change, re-run ALL tests and publish new results
4. Never mix results from different scoring versions in one report
5. Every report states which scoring version was used
6. Previous reports are archived, not overwritten

---

## Scoring Version

**v1.0** — March 21, 2026

Changes from this point forward require a version bump and full re-test.
