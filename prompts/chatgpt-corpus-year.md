# IRONMAN Corpus Generator — YEAR (Tier 3)

You previously generated 200 messages for Month 1 at Nexus Dynamics. Now generate **1,800 additional messages** covering months 2-12. Same person, same company.

**This is a large generation. Break it into 6 batches of 300 messages each if needed. I'll prompt you for each batch.**

## Format

Same JSON array:
```json
[
  {"timestamp": "2025-04-14T08:30:00", "message": "..."},
  ...
]
```

## Rules

1. **1,800 messages, ~200,000 words total.** Spread across 11 months (~5-6 messages/day on workdays).
2. **Continue the existing world.** All people, projects, customers from Month 1 persist.
3. **5+ facts per message minimum.**
4. **Natural tone.** Real conversations, not reports.

## Must include across the year:
- **60+ total people** (some from Month 1 persist, 30+ new across the year)
- **People leaving**: At least 5 people quit or are let go. Their info should still be findable.
- **15+ customers** total with varying status (active, churned, renewed, expanded)
- **20+ incidents** with full details
- **50+ meetings** across the year
- **30+ credential rotations** (keys change, old values explicitly stated)
- **15+ projects** (some launch, some get cancelled, some pivot)
- **Company milestones**: funding round, office move, reorg, acquisitions, layoffs
- **Seasonal events**: holidays, company retreat, annual reviews, budget planning

## Difficulty escalators (critical):
- **20+ contradictions**: Facts that change over time. Old values must be findable. "We moved from AWS us-east-1 to us-west-2 in July." "401k match went from 4% to 6% in September."
- **10+ same-name pairs**: Different people sharing names across departments
- **Long-range dependencies**: "The project that started in April finally shipped in November"
- **Buried facts**: Important details mentioned casually in passing, not as the main topic
- **Dense days**: Some days have 15+ messages (incident days, launch days, board meeting days)
- **Quiet weeks**: Some weeks have almost nothing (holidays, vacation)
- **Evolving roles**: People get promoted, switch teams, take on new responsibilities
- **Implicit facts**: "Grabbed lunch with Stefan and his daughter" (implies Stefan has a daughter — never explicitly stated)

## Word count targets per batch:
- Batch 1 (months 2-3): 300 messages, ~33,000 words
- Batch 2 (months 4-5): 300 messages, ~33,000 words
- Batch 3 (months 6-7): 300 messages, ~33,000 words
- Batch 4 (months 8-9): 300 messages, ~33,000 words
- Batch 5 (months 10-11): 300 messages, ~33,000 words
- Batch 6 (month 12): 300 messages, ~33,000 words

## Output
Return ONLY the JSON array for each batch. No commentary. Timestamps should span 2025-04-14 to 2026-03-14.

**Start with Batch 1 (months 2-3, April 14 - June 13, 2025). I'll ask for each subsequent batch.**
