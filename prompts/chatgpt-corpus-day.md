# IRONMAN Corpus Generator — DAY (Tier 1)

Generate a JSON array of **20 messages** that simulate one day of a person talking to their AI assistant at a tech startup called **Nexus Dynamics** (supply chain AI company, ~100 employees, based in Boulder CO).

## Format

```json
[
  {
    "timestamp": "2025-03-15T08:12:00",
    "message": "Hey, just got out of standup. The Aurora project is behind by 2 weeks — Kai Richter says the data pipeline refactor is blocking everything. Sprint ends Friday."
  },
  ...
]
```

## Rules

1. **Natural language only.** These are messages from a person to their AI. Casual, sometimes messy. Not structured documents.
2. **Pack specific facts into every message.** Names, numbers, dates, emails, phone numbers, dollar amounts, deadlines, credentials, locations. The benchmark will query these facts later.
3. **20 messages, ~3,000 words total.**
4. **Cover these topics across the day:**
   - 3-4 messages about **people** (new hire, team member details, someone's birthday, allergies, hobbies, pets, kids)
   - 3-4 messages about **projects** (status, deadlines, blockers, tech stack)
   - 2-3 messages about **meetings** (what was discussed, decisions made, action items)
   - 2-3 messages about **infrastructure** (server IPs, API keys, credentials, deployments)
   - 2-3 messages about **customers** (account details, contracts, champions, ARR)
   - 2-3 messages about **company** (policies, benefits, org changes, financials)
   - 1-2 messages about **incidents** (something broke, root cause, resolution)

## Fact Density Requirements

Each message should contain **at least 3 queryable facts.** Examples:
- "Stefan Lang started today as ML engineer. He's from Munich, did his PhD at TU Munich on reinforcement learning. Allergic to shellfish. His desk is 4B-12. Employee ID is NX-2847."
- "Switched our Datadog API key to dd-api-7x9k2m4p8q. Old one was dd-api-OLD-3x7k9m2p. PagerDuty service key is pd-svc-3f8k9m2x."
- "Acme Manufacturing contract renewed — $340K ARR, 2-year term. Champion is Anders Lang, their VP of Ops. Email: anders.lang@acmemfg.com"

## What NOT to do
- No real company names, real people, or real credentials
- No generic filler messages ("had a good day!")
- No messages without queryable facts
- Don't use the exact examples above — create fresh ones

## Output
Return ONLY the JSON array. No commentary.
