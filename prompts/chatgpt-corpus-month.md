# IRONMAN Corpus Generator — MONTH (Tier 2)

You previously generated 20 messages for "Day 1" at Nexus Dynamics. Now generate **180 additional messages** covering the rest of the first month (days 2-30). Same person, same company.

## Format

Same JSON array format:
```json
[
  {"timestamp": "2025-03-16T09:05:00", "message": "..."},
  ...
]
```

## Rules

1. **180 messages, ~25,000 words total.** Spread across 29 days (~6 messages/day).
2. **Continue the same world.** Reference people, projects, and facts from Day 1. Build on them.
3. **Introduce 30-40 NEW people** over the month (team members, customers, vendors, candidates).
4. **3-5 facts per message minimum.**
5. **Natural conversation tone.** Some days are busy (10+ messages), some quiet (2-3).

## Must include across the month:
- **10+ new hires or team members** with full details (role, background, allergies, hobbies, pets, emergency contacts, desk numbers)
- **5+ customer accounts** with ARR, champion, industry, contract dates, use case
- **3+ incidents** with timestamps, root cause, resolution, duration, who was on-call
- **8+ meetings** with attendees, decisions, action items
- **10+ credentials/config** (API keys, server IPs, ports, database passwords, SSH keys, service accounts)
- **5+ project updates** showing progress/changes from Day 1 status
- **3+ policy/benefits changes** (PTO policy updated, new insurance provider, etc.)
- **2+ contradictions**: facts that CHANGE from earlier (someone moves teams, a credential rotates, a policy updates). Make the OLD value and NEW value both clearly stated.
- **5+ financial figures** (revenue, burn rate, runway, deal sizes)

## Difficulty escalators:
- **Same-name people**: Include at least 3 pairs of people who share first names but are different people (e.g., "Stefan Lang the ML engineer" and "Stefan Park the sales rep")
- **Similar credentials**: Multiple API keys for different services that look alike
- **Cross-references**: "The customer whose champion is [person] just renewed for [amount]"
- **Temporal precision**: "As of Tuesday the deploy is on staging. By Thursday it should be in prod."

## Output
Return ONLY the JSON array (180 messages). No commentary. Timestamps should span 2025-03-16 to 2025-04-13.
