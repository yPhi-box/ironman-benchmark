# IRONMAN Corpus Generator — Full Year

Generate a JSON array of **2,000 messages** simulating one year of a person talking to their AI assistant at a tech startup called **Nexus Dynamics** (supply chain AI company, ~100 employees, Boulder CO, founded 2020).

The benchmark will slice this into 3 tiers:
- **Day 1** = messages 1-20
- **Month 1** = messages 1-200
- **Full Year** = all 2,000 messages

So **Day 1 must be packed with facts** (it's tested alone). Month 1 must work standalone. The full year builds on everything.

## Format

```json
[
  {"timestamp": "2025-03-15T08:12:00", "message": "Hey, just got out of standup. Aurora project is behind by 2 weeks — Kai Richter says the data pipeline refactor is blocking. Sprint ends Friday."},
  ...
]
```

## Rules

1. **Natural conversation tone.** Casual messages from a person to their AI assistant. Not reports, not documents.
2. **5+ queryable facts per message.** Names, numbers, dates, emails, phone numbers, dollar amounts, API keys, IPs, deadlines.
3. **Timestamps span 2025-03-15 to 2026-03-14.** Workdays mostly, occasional weekends for incidents.
4. **Pacing:**
   - Day 1 (messages 1-20): Dense. ~3,000 words. Establish key people, projects, infra.
   - Month 1 (messages 1-200): ~25,000 words. ~6-7 messages/day. Build the world.
   - Months 2-12 (messages 201-2000): ~200,000 words. ~5-6 messages/workday. Evolve everything.

## Content requirements across the full year:

**People (60+ total):**
- Day 1: Introduce 8-10 key people with roles, backgrounds, personal details
- Month 1: 30+ people total (hires, team members, customers)
- Full year: 60+ people. At least 5 leave the company. At least 5 get promoted.
- Each person needs: full name, role, team, start date, and at least 3 personal facts (hometown, hobbies, allergies, pets, kids, emergency contact, desk number, employee ID)
- **10+ same-name pairs**: Different people sharing first names across departments (e.g., "Stefan Lang in ML" vs "Stefan Park in Sales")

**Projects (15+):**
- Day 1: 2-3 active projects with status
- Full year: 15+ projects. Some launch, some get cancelled, some pivot.
- Include tech stacks, deadlines, team assignments, blockers

**Customers (15+):**
- Each with: company name, industry, ARR, contract dates, champion (name + title + email), use case
- Some churn, some renew, some expand

**Infrastructure (30+ credentials):**
- API keys, server IPs, database connection strings, SSH keys, service accounts, ports
- **30+ credential rotations over the year** — old value AND new value explicitly stated each time
- Format varies: "new Datadog key is dd-api-xxx, replacing dd-api-yyy" or "rotated the PagerDuty key to pd-xxx"

**Incidents (20+):**
- Timestamp, duration, root cause, resolution, who was on-call, impact, postmortem actions

**Meetings (50+):**
- Attendees, decisions, action items, follow-ups

**Company events:**
- Funding round with details (amount, lead investor, valuation)
- Office move (old address, new address, date)
- Reorg (who moved where)
- Benefits changes (old value → new value)
- Annual reviews, holiday party, company retreat
- At least 1 acquisition or partnership

**Financial (20+ figures):**
- ARR, burn rate, runway, deal sizes, salary info, budget allocations

## Difficulty requirements (critical for the benchmark):

1. **20+ contradictions**: Facts that explicitly change. "We used to be on us-east-1 but migrated to us-west-2 in July." "401k match went from 4% to 6% effective September 1." Both old and new values must be clearly stated.

2. **Implicit facts (20+)**: Never directly stated but inferable. "Grabbed lunch with Stefan and his daughter at that Italian place on Pearl Street" (implies Stefan has a daughter, implies Italian restaurant on Pearl Street). "Maya had to leave the meeting early for her son's soccer game" (implies Maya has a son).

3. **Buried facts (20+)**: Important details mentioned in passing, not as the main topic. Allergy info dropped casually in a lunch story. A credential mentioned in the middle of an incident narrative.

4. **Cross-references (15+)**: "The customer whose champion shares a name with our ML engineer just renewed." Facts that require connecting info across multiple messages.

5. **Long-range dependencies (10+)**: "That project from April finally shipped in November." Facts that span months.

6. **Dense days vs quiet weeks**: Incident days should have 10-15 messages. Holiday weeks should have 1-2. Realistic cadence.

7. **Evolving roles**: People change teams, get promoted, take on different projects. Their current status should differ from their initial introduction.

## What NOT to do
- No real companies, people, or credentials
- No generic filler ("had a good day", "thanks!", "ok")
- No messages without queryable facts
- Don't reuse the example names/facts from this prompt — create original ones
- Don't make it feel generated — these should read like real messages from a real person

## Generation instructions
This is too large for one response. Generate in batches:
- **Batch 1**: Messages 1-200 (Day 1 + rest of Month 1). ~25,000 words.
- **Batch 2**: Messages 201-500 (Months 2-3). ~33,000 words.
- **Batch 3**: Messages 501-800 (Months 4-5). ~33,000 words.
- **Batch 4**: Messages 801-1100 (Months 6-7). ~33,000 words.
- **Batch 5**: Messages 1101-1500 (Months 8-9). ~33,000 words.
- **Batch 6**: Messages 1501-2000 (Months 10-12). ~40,000 words.

Start with Batch 1. I'll say "next batch" for each subsequent one. Maintain consistency across batches — same people, same projects, same world.

## Output
Return ONLY the JSON array for each batch. No commentary, no explanations.
