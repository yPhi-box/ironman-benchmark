#!/usr/bin/env python3
"""
Generate realistic OC workspace data for IRONMAN benchmark.

Based on real OC bot workspace structure — daily memory files, project trackers,
long-term memory, configs. All data is completely fictional.

Scenario: "Sentinel" — an OC bot managing web dev and marketing for a fictional
plumbing company "Apex Plumbing Solutions" (apexplumbingsolutions.com).
Owner: "Marcus Webb", timezone CST, based in Denver CO.

Generates 365 days of workspace data with:
- Daily memory files (2025-04-01 to 2026-03-31)
- Project tracker files (SEO, outreach, competitors, tech issues)
- MEMORY.md (long-term curated memory)
- TOOLS.md, HEARTBEAT.md, IDENTITY.md
- Config files, growth trackers

All content is synthetic — no real people, companies, or credentials.
"""
import json
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

# === FICTIONAL WORLD ===

COMPANY = "Apex Plumbing Solutions"
DOMAIN = "apexplumbingsolutions.com"
OWNER = "Marcus Webb"
BOT_NAME = "Sentinel"
CITY = "Denver"
STATE = "CO"
ADDRESS = "2917 Elkhorn Drive, Suite 110, Denver, CO 80205"
PHONE = "720-555-0147"
EIN = "47-8291053"

# Staff
STAFF = {
    "Marcus Webb": "owner",
    "Dana Torres": "office manager",
    "Jake Lindgren": "lead technician",
    "Riley Cho": "marketing coordinator",
    "Vic Okafor": "apprentice",
    "Logan Pratt": "dispatcher",
}

# Competitors
COMPETITORS = [
    {"name": "Mountain View Plumbing", "domain": "mtviewplumbing.com", "da": 28},
    {"name": "Front Range Drain Co", "domain": "frontrangedrain.com", "da": 35},
    {"name": "Pike's Peak Plumbing", "domain": "pikespeakplumbing.com", "da": 22},
    {"name": "Red Rocks Rooter", "domain": "redrooksrooter.com", "da": 19},
    {"name": "Mile High Plumbers", "domain": "milehighplumbers.com", "da": 41},
]

# Services
SERVICES = [
    "drain cleaning", "sewer line repair", "water heater installation",
    "emergency plumbing", "pipe repair", "toilet repair",
    "faucet installation", "garbage disposal repair", "sump pump installation",
    "hydro jetting", "trenchless sewer repair", "gas line repair",
    "water softener installation", "backflow prevention", "repiping",
    "leak detection", "bathroom remodel plumbing", "commercial plumbing",
]

# Service areas
SERVICE_AREAS = [
    "Denver", "Aurora", "Lakewood", "Arvada", "Westminster",
    "Thornton", "Centennial", "Boulder", "Broomfield", "Littleton",
    "Englewood", "Golden", "Parker", "Castle Rock", "Highlands Ranch",
]

# Keywords tracking
KEYWORDS = [
    {"kw": "plumber denver", "pos": 23, "vol": 2900},
    {"kw": "emergency plumber denver", "pos": 15, "vol": 880},
    {"kw": "drain cleaning denver", "pos": 18, "vol": 720},
    {"kw": "water heater installation denver", "pos": 31, "vol": 390},
    {"kw": "sewer line repair denver", "pos": 27, "vol": 260},
    {"kw": "plumber aurora co", "pos": 12, "vol": 480},
    {"kw": "24 hour plumber denver", "pos": 19, "vol": 590},
    {"kw": "hydro jetting denver", "pos": 8, "vol": 170},
    {"kw": "trenchless sewer repair denver", "pos": 14, "vol": 140},
    {"kw": "garbage disposal repair denver", "pos": 22, "vol": 210},
    {"kw": "plumber lakewood co", "pos": 9, "vol": 320},
    {"kw": "water softener installation denver", "pos": 35, "vol": 110},
    {"kw": "backflow testing denver", "pos": 11, "vol": 90},
    {"kw": "gas line repair denver", "pos": 29, "vol": 150},
    {"kw": "bathroom plumbing remodel denver", "pos": 42, "vol": 200},
]

# Fake credentials
CREDS = {
    "wp_admin": "sentinel-wp-2025",
    "google_analytics": "UA-482917-3",
    "ga4_property": "G-7X9K2M4P8Q",
    "gsc_property": "sc-domain:apexplumbingsolutions.com",
    "ahrefs_api": "ahrefs-api-k8m2n4p7q9",
    "moz_api": "mozscape-8x2k4m9p",
    "mailchimp_api": "mc-api-3f8k9m2x7p",
    "twilio_sid": "AC7x9k2m4p8q3f6h",
    "hosting_panel": "cpanel.apexhost.com",
    "ssh_key_path": "/home/sentinel/.ssh/id_rsa",
    "db_name": "apex_wp_db",
    "db_user": "apex_dbuser",
}

# Fake IPs
IPS = {
    "sentinel": "10.0.1.50",
    "webserver": "10.0.1.10",
    "staging": "10.0.1.11",
    "marcus_pc": "10.0.1.100",
}

# Email contacts
EMAILS = {
    "marcus": "marcus@apexplumbingsolutions.com",
    "info": "info@apexplumbingsolutions.com",
    "dana": "dana@apexplumbingsolutions.com",
    "support": "support@apexplumbingsolutions.com",
}

# Moz/SEO data evolving over time
def get_da_for_date(d):
    """Domain authority grows from 8 to ~22 over the year."""
    day_num = (d - datetime(2025, 4, 1)).days
    return min(8 + int(day_num * 0.04), 22)

def get_pages_crawled(d):
    day_num = (d - datetime(2025, 4, 1)).days
    return min(30 + int(day_num * 0.3), 145)


# === CONTENT GENERATORS ===

START_DATE = datetime(2025, 4, 1)
END_DATE = datetime(2026, 3, 31)


def gen_daily_file(d, day_num):
    """Generate a daily memory file for a given date."""
    dow = d.strftime("%A")
    is_weekend = dow in ("Saturday", "Sunday")
    
    sections = []
    sections.append(f"# {d.strftime('%Y-%m-%d')} Session Notes\n")
    
    # Pick 2-5 work items for the day
    num_items = random.randint(1, 3) if is_weekend else random.randint(2, 5)
    
    work_types = [
        gen_seo_work, gen_content_work, gen_technical_work,
        gen_outreach_work, gen_email_work, gen_analytics_work,
        gen_competitor_work, gen_site_issue, gen_wordpress_work,
        gen_meeting_notes, gen_marcus_interaction, gen_site_issue,
    ]
    
    # Weight towards SEO and content early, technical later
    if day_num < 90:
        weights = [3, 3, 1, 2, 2, 1, 2, 1, 2, 1, 2, 1]
    elif day_num < 200:
        weights = [2, 2, 2, 2, 1, 2, 1, 2, 2, 1, 2, 1]
    else:
        weights = [2, 2, 3, 1, 1, 2, 1, 2, 2, 2, 2, 2]
    
    chosen = random.choices(work_types, weights=weights, k=num_items)
    # Deduplicate
    seen = set()
    unique = []
    for fn in chosen:
        if fn.__name__ not in seen:
            seen.add(fn.__name__)
            unique.append(fn)
    
    hour = random.randint(6, 23)
    for fn in unique:
        sections.append(fn(d, day_num, hour))
        hour = min(hour + random.randint(1, 3), 23)
    
    # Occasional Marcus correction/feedback (15% chance)
    if random.random() < 0.15:
        sections.append(gen_marcus_correction(d, day_num))
    
    # Occasional mistake log (10% chance)
    if random.random() < 0.10:
        sections.append(gen_mistake_entry(d, day_num))
    
    return "\n".join(sections)


def gen_seo_work(d, day_num, hour):
    """Generate SEO work entry."""
    kw = random.choice(KEYWORDS)
    area = random.choice(SERVICE_AREAS)
    
    templates = [
        f"""## SEO Work ({hour}:00 CST)

### Keyword Position Check
- **"{kw['kw']}"**: Position #{kw['pos'] - random.randint(0, 3)} (was #{kw['pos']})
- Search volume: {kw['vol']}/mo
- Target: top 10 by end of quarter
- Page ranking: /{kw['kw'].replace(' ', '-').replace('denver', area.lower())}/

### On-Page Optimization
- Updated title tag for /{random.choice(SERVICES).replace(' ', '-')}/
- Added FAQ schema with 4 questions
- Internal linked from 3 related service pages
- Meta description rewritten — was generic, now includes "{area}" and pricing hook
- **Status:** ✅ Published""",

        f"""## Moz Crawl Review ({hour}:00 CST)

### Crawl Results (triggered {d.strftime('%b %d')})
- Pages crawled: {get_pages_crawled(d)}
- Domain Authority: {get_da_for_date(d)}
- Issues found: {random.randint(2, 18)}
  - Title too long: {random.randint(0, 5)} pages
  - Missing meta description: {random.randint(0, 4)} pages
  - Thin content: {random.randint(0, 3)} pages
  - 404 errors: {random.randint(0, 2)} pages

### Fixes Applied
- Shortened titles on {random.randint(1, 3)} pages (under 60 chars now)
- Added meta descriptions for {random.choice(SERVICE_AREAS)} service area page
- **Status:** Waiting for next crawl to verify""",

        f"""## Google Search Console Review ({hour}:00 CST)

### Performance (last 28 days)
- Total clicks: {random.randint(180, 600) + day_num}
- Total impressions: {random.randint(3000, 12000) + day_num * 10}
- Average CTR: {random.uniform(2.5, 6.5):.1f}%
- Average position: {random.uniform(18, 35):.1f}

### Top Queries
1. "{kw['kw']}" — {random.randint(20, 80)} clicks, pos {kw['pos'] - random.randint(0, 5)}
2. "{random.choice(KEYWORDS)['kw']}" — {random.randint(10, 40)} clicks
3. "apex plumbing reviews" — {random.randint(5, 25)} clicks

### Coverage Issues
- {random.randint(0, 3)} pages excluded (crawled - currently not indexed)
- Submitted sitemap: {get_pages_crawled(d)} URLs
- Indexed: {get_pages_crawled(d) - random.randint(2, 8)} URLs""",
    ]
    
    return random.choice(templates)


def gen_content_work(d, day_num, hour):
    """Generate content creation work."""
    service = random.choice(SERVICES)
    area = random.choice(SERVICE_AREAS)
    
    templates = [
        f"""## Content Creation ({hour}:00 CST)

### New Service Area Page: {area}
- **URL:** /{area.lower().replace(' ', '-')}-plumber/
- **Word count:** {random.randint(1200, 2500)}
- **Sections:** Service overview, common problems in {area}, pricing table, FAQ (5 questions), testimonial, CTA
- **Internal links:** Linked from /service-areas/ hub and 3 service pages
- **Schema:** LocalBusiness, FAQ, BreadcrumbList
- **Status:** ✅ Published and submitted to GSC

### Content Audit
- Thin pages identified: {random.randint(1, 4)}
- Pages updated with additional content: {random.randint(1, 3)}
- Average word count improvement: +{random.randint(200, 600)} words""",

        f"""## Blog Post Published ({hour}:00 CST)

### "{random.choice([
    f'How Much Does {service.title()} Cost in {CITY}?',
    f'5 Signs You Need {service.title()} — {CITY} Homeowner Guide',
    f'DIY vs Professional {service.title()}: When to Call a Pro',
    f'{service.title()} in {area}: What Every Homeowner Should Know',
    f'Emergency {service.title()}: What to Do Before the Plumber Arrives',
])}"
- **URL:** /blog/{service.replace(' ', '-')}-{random.choice(['cost', 'guide', 'tips', 'signs'])}/
- **Word count:** {random.randint(800, 2000)}
- **Target keyword:** "{service} {CITY.lower()}" ({random.randint(50, 300)}/mo volume)
- **CTA:** Free estimate form + phone number ({PHONE})
- **Status:** ✅ Published""",
    ]
    
    return random.choice(templates)


def gen_technical_work(d, day_num, hour):
    """Generate technical/dev work."""
    templates = [
        f"""## Technical Work ({hour}:00 CST)

### Page Speed Optimization
- Ran Lighthouse audit on homepage
- Performance score: {random.randint(45, 85)}/100
- LCP: {random.uniform(1.8, 4.5):.1f}s (target: <2.5s)
- CLS: {random.uniform(0.01, 0.25):.2f} (target: <0.1)
- FID: {random.randint(50, 200)}ms (target: <100ms)

### Fixes Applied
- Compressed {random.randint(3, 12)} images (saved {random.randint(200, 800)}KB)
- Deferred {random.randint(1, 4)} non-critical JS files
- Added width/height to {random.randint(2, 6)} images (CLS fix)
- **Status:** Deployed, waiting for field data update""",

        f"""## WordPress Maintenance ({hour}:00 CST)

### Updates Applied
- WordPress core: {random.choice(['6.4.2', '6.4.3', '6.5', '6.5.1', '6.5.2'])} → {random.choice(['6.5.3', '6.6', '6.6.1'])}
- Plugin updates: {random.randint(2, 7)} plugins
- Theme update: Apex Custom Theme v{random.randint(1,3)}.{random.randint(0,9)}
- **Backup taken before updates:** ✅ ({d.strftime('%Y%m%d')}_pre_update.tar.gz)

### Issues Found
- {random.choice(['Contact form 7 conflict with caching plugin', 'Yoast SEO sitemap returning 404 after update', 'WP Rocket purge needed after core update', 'Schema markup plugin broke JSON-LD output', 'No issues found — clean update'])}
- **Status:** {random.choice(['✅ Resolved', '✅ Clean', '⚠️ Monitoring'])}""",

        f"""## SSL/Security Check ({hour}:00 CST)

- SSL certificate: Valid until {(d + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')}
- Mixed content warnings: {random.randint(0, 3)}
- Security headers: {random.choice(['All present', 'Missing X-Frame-Options', 'Missing CSP header'])}
- Sucuri scan: {random.choice(['Clean', 'Clean', 'Clean', '1 warning — outdated jQuery'])}
- Login attempts blocked (last 7 days): {random.randint(5, 150)}
- **Status:** ✅ Secure""",
    ]
    
    return random.choice(templates)


def gen_outreach_work(d, day_num, hour):
    """Generate outreach/link building work."""
    fake_firms = [
        "Denver Home Services Alliance", "Colorado Contractor Network",
        "Front Range Business Directory", "Denver Chamber of Commerce",
        "Colorado Home Improvement Association", "Mile High Trades Council",
        f"{random.choice(SERVICE_AREAS)} Community Board",
        f"Best of {random.choice(SERVICE_AREAS)} Directory",
    ]
    
    return f"""## Outreach ({hour}:00 CST)

### Link Building Campaign
- **Contacted:** {random.choice(fake_firms)}
- **Ask:** Listing on their recommended contractors page
- **Template used:** Contractor partnership v{random.randint(1,3)}
- **Response:** {random.choice(['No response yet', 'Interested — sent follow-up', 'Declined', 'Listed! Link live', 'Auto-reply — will follow up in 3 days', 'Bounced email — need new contact'])}

### Directory Submissions
- Submitted to {random.randint(1, 3)} new directories today
- Pending approval: {random.randint(2, 8)} directories
- Live listings total: {min(15 + day_num // 10, 85)}
- **NAP consistency check:** {random.choice(['All correct', f'Fixed phone number on {random.choice(fake_firms)}', 'Address mismatch on 1 listing — submitted correction'])}"""


def gen_email_work(d, day_num, hour):
    """Generate email management work."""
    return f"""## Email Check ({hour}:00 CST)

### Inbox: {EMAILS['info']}
- **New messages:** {random.randint(0, 8)}
- **Customer inquiries:** {random.randint(0, 3)}
- **Spam filtered:** {random.randint(0, 5)}
- **Action taken:**
  - {random.choice([
    'Forwarded 2 quote requests to Dana for scheduling',
    'Replied to customer about water heater installation timeline',
    'Flagged urgent: burst pipe inquiry from Lakewood customer',
    'No action needed — all spam',
    f'Sent quote follow-up to {random.choice(SERVICE_AREAS)} customer',
    'Forwarded contractor partnership inquiry to Marcus',
    'Replied to Google Business Profile review notification',
  ])}"""


def gen_analytics_work(d, day_num, hour):
    """Generate analytics review."""
    return f"""## Analytics Review ({hour}:00 CST)

### Google Analytics (last 7 days)
- Sessions: {random.randint(200, 800) + day_num}
- Users: {random.randint(150, 600) + day_num}
- Bounce rate: {random.uniform(35, 65):.1f}%
- Avg session duration: {random.randint(45, 180)}s
- Top pages:
  1. / (homepage) — {random.randint(80, 300)} sessions
  2. /services/ — {random.randint(30, 120)} sessions
  3. /emergency-plumber/ — {random.randint(20, 80)} sessions
  4. /contact/ — {random.randint(15, 60)} sessions

### Conversion Tracking
- Form submissions: {random.randint(3, 25)}
- Phone clicks: {random.randint(5, 40)}
- Conversion rate: {random.uniform(1.5, 5.5):.1f}%
- **Top converting page:** /{random.choice(SERVICES).replace(' ', '-')}/"""


def gen_competitor_work(d, day_num, hour):
    """Generate competitor analysis work."""
    comp = random.choice(COMPETITORS)
    
    return f"""## Competitor Analysis ({hour}:00 CST)

### {comp['name']} ({comp['domain']})
- Domain Authority: {comp['da'] + random.randint(-2, 3)}
- Backlinks: {random.randint(200, 2000)}
- Ranking keywords: {random.randint(50, 500)}
- **New content found:** {random.choice([
    f'Published blog post about {random.choice(SERVICES)} in {random.choice(SERVICE_AREAS)}',
    'No new content this week',
    'New service area page for Boulder',
    'Updated pricing page with calculator widget',
    f'Running Google Ads for "{random.choice(KEYWORDS)["kw"]}"',
])}
- **Gaps we can exploit:** {random.choice([
    f'They have no {random.choice(SERVICE_AREAS)} page — we should publish one',
    f'Their {random.choice(SERVICES)} page is thin (200 words) — ours is 1,500+',
    'They rank #3 for "emergency plumber denver" but page is outdated',
    'No schema markup on any page — our structured data is an advantage',
    f'Weak on long-tail: "{random.choice(SERVICES)} cost {CITY.lower()}" has no competition',
])}"""


def gen_site_issue(d, day_num, hour):
    """Generate a site issue/incident."""
    templates = [
        f"""## ⚠️ Site Issue ({hour}:00 CST)

### {random.choice([
    'Contact form not sending emails',
    'Homepage slider broken after plugin update',
    '404 error on service area page',
    'Slow page load — server response time spike',
    'Google Business Profile showing wrong hours',
    'SSL certificate warning on staging site',
    'Image gallery not loading on mobile',
    'Quote calculator returning NaN on certain inputs',
])}
- **Discovered:** {hour}:{random.randint(0,59):02d} CST
- **Impact:** {random.choice(['Customer-facing — urgent', 'SEO only — moderate', 'Internal only — low', 'Customer-facing — high'])}
- **Root cause:** {random.choice([
    'Plugin conflict after update',
    'Caching issue — stale version served',
    'DNS propagation delay',
    'JavaScript error in custom code',
    'Server memory spike from crawler bot',
    'Redirect rule conflict in .htaccess',
])}
- **Fix:** {random.choice([
    'Rolled back plugin to previous version',
    'Cleared all caches (WP Rocket + CDN)',
    'Fixed redirect rule — tested with curl',
    'Disabled conflicting plugin, contacted developer',
    'Restarted PHP-FPM service',
    'Updated DNS record, waiting for propagation',
])}
- **Status:** ✅ Resolved at {hour + 1}:{random.randint(0,59):02d} CST
- **Downtime:** ~{random.randint(5, 45)} minutes""",
    ]
    
    return random.choice(templates)


def gen_wordpress_work(d, day_num, hour):
    """Generate WordPress-specific work."""
    return f"""## WordPress Work ({hour}:00 CST)

### {random.choice([
    'New service page created',
    'Menu structure updated',
    'Footer links reorganized',
    'Review widget installed',
    'New testimonial added',
    'Schema markup updated',
    'Sitemap regenerated',
    'Robots.txt updated',
])}
- **Changes:**
  - {random.choice([
    f'Added {random.choice(SERVICE_AREAS)} to service area dropdown menu',
    f'Created landing page for {random.choice(SERVICES)} — {random.randint(1000, 2000)} words',
    f'Updated phone number to {PHONE} on {random.randint(3, 12)} pages',
    'Added Google reviews widget to sidebar',
    'Fixed breadcrumb navigation on service pages',
    f'Added internal links from blog posts to {random.choice(SERVICES)} page',
    'Updated copyright year in footer',
    'Added emergency banner with phone number to all pages',
  ])}
- **Verified:** Checked on desktop, mobile, and tablet
- **Status:** ✅ Live"""


def gen_meeting_notes(d, day_num, hour):
    """Generate notes from interaction with Marcus."""
    topics = [
        f"new service launch ({random.choice(SERVICES)})",
        "quarterly review of SEO progress",
        "budget for paid advertising",
        "hiring a new technician",
        f"customer complaint about {random.choice(SERVICE_AREAS)} job",
        "website redesign discussion",
        "pricing updates for 2026",
        "Google Business Profile optimization",
        "review management strategy",
        "expansion to new service areas",
    ]
    
    return f"""## Notes from Marcus ({hour}:00 CST)

### Topic: {random.choice(topics).title()}
- Marcus wants {random.choice([
    f'to start offering {random.choice(SERVICES)} in {random.choice(SERVICE_AREAS)}',
    'more focus on emergency calls — those are highest margin',
    'to see this week\'s rankings report by Friday',
    'pricing table updated on the website — new rates from Jake',
    'Google reviews response templates — wants all reviews replied to within 24h',
    f'competitor analysis on {random.choice(COMPETITORS)["name"]} — they\'re stealing customers',
    'to pause paid ads and focus on organic growth',
    'a monthly report template he can share with his accountant',
    f'to expand service area to include {random.choice(SERVICE_AREAS)}',
])}
- **Decision:** {random.choice([
    'Approved — will start next week',
    'Needs more data — will revisit Thursday',
    'Approved with modifications',
    'Tabled for now — budget constraints',
    'Greenlit — top priority this week',
])}
- **Action items:**
  - [ ] {random.choice(['Update website with new info', 'Draft content plan', 'Pull competitor data', 'Create report', 'Update pricing pages'])}
  - [ ] {random.choice(['Follow up with Marcus by EOD Friday', 'Send Dana the schedule', 'Check with Jake on pricing', 'Submit for review'])}"""


def gen_marcus_interaction(d, day_num, hour):
    """Generate a general interaction or instruction from Marcus."""
    return f"""## Marcus Check-in ({hour}:00 CST)

- Marcus asked: "{random.choice([
    'What\'s our DA at now?',
    'How many leads came in this week?',
    'Did that blog post go live?',
    f'Why are we not ranking for {random.choice(KEYWORDS)["kw"]}?',
    f'Can you check what {random.choice(COMPETITORS)["name"]} is doing?',
    'When was the last backup?',
    'How\'s the site speed looking?',
    'Did we get any new reviews this week?',
    'What\'s the status on the outreach campaign?',
    f'Can we add {random.choice(SERVICE_AREAS)} as a service area?',
])}"
- **Response given:** Provided current data, no further action needed
- **Mood:** {random.choice(['Happy with progress', 'Impatient — wants faster results', 'Neutral', 'Frustrated about rankings', 'Excited about new lead'])}"""


def gen_marcus_correction(d, day_num):
    """Generate a correction/feedback from Marcus."""
    return f"""## ⚠️ Marcus Feedback

- {random.choice([
    '"Stop sending me updates every 5 minutes. Just do the work and report when done."',
    '"That blog post had the wrong phone number. Triple-check before publishing."',
    '"I already told you we don\'t service Castle Pines. Remove that page."',
    '"The competitor report was good but I need it in a simpler format. Bullet points, not tables."',
    '"Don\'t run site updates during business hours. After 8 PM only."',
    '"You changed the homepage without asking. Run changes by me first for customer-facing pages."',
    f'"The quote on the {random.choice(SERVICES)} page is wrong — Jake updated the pricing last week."',
    '"Good work on the SEO this week. Keep it up."',
    '"Why did site speed drop? Check what changed."',
    '"I need a daily summary, not an hourly one. Once a day, morning, done."',
])}
- **Lesson learned:** Write it down, don't repeat the mistake"""


def gen_mistake_entry(d, day_num):
    """Generate a self-correction entry."""
    return f"""### Mistakes Today
- {random.choice([
    'Ran bulk image optimization during peak hours — slowed the site',
    'Forgot to check chat between steps — Marcus had to wait 20 minutes',
    'Published draft page accidentally — caught and reverted in 3 minutes',
    'Sent outreach email with wrong company name — mortifying',
    f'Overwrote {random.choice(SERVICE_AREAS)} page content — restored from backup',
    'Ran Moz crawl twice in one day — wasted API credits',
    'Didn\'t verify redirect after URL change — 404 for 2 hours',
    'Used wrong schema type for service page — fixed after GSC flagged it',
    'Left debug output on contact form — visible to customers for ~30 min',
])}"""


def gen_memory_md(day_num_max):
    """Generate the MEMORY.md long-term memory file."""
    return f"""# MEMORY.md - Long-Term Memory

## Critical Rules
1. **Check chat between every action.** No freight trains.
2. **Don't publish without Marcus's approval** on customer-facing content.
3. **No site changes during business hours** (8 AM - 6 PM CST) unless emergency.
4. **Backup before every WordPress update.** No exceptions.

## About Marcus
- Marcus Webb, owns {COMPANY} ({DOMAIN})
- **EIN:** {EIN}
- **Address:** {ADDRESS}
- **Phone:** {PHONE}
- Timezone: America/Chicago (CST/CDT)
- Wants daily morning summary, not constant updates
- Prefers bullet points over paragraphs
- Gets frustrated when I repeat mistakes
- "No cowboy moves" — propose plan, discuss, then execute

## Staff
- **Dana Torres** — office manager, handles scheduling and customer calls
- **Jake Lindgren** — lead technician, sets pricing and does estimates
- **Riley Cho** — marketing coordinator (part-time), manages social media
- **Vic Okafor** — apprentice, started {(START_DATE + timedelta(days=90)).strftime('%B %Y')}
- **Logan Pratt** — dispatcher, routes emergency calls

## Business Context
- Core services: drain cleaning, sewer repair, water heaters, emergency plumbing
- Service area: Denver metro + {', '.join(SERVICE_AREAS[:8])}
- Main differentiator: 24/7 emergency service with 1-hour response time
- Busy season: November-March (frozen pipes, water heater failures)
- Slow season: May-August
- **NOT offered:** HVAC, electrical, general contracting
- Competitors to watch: {', '.join(c['name'] for c in COMPETITORS[:3])}

## SEO Status (updated regularly)
- Domain Authority: ~{get_da_for_date(START_DATE + timedelta(days=min(day_num_max, 365)))}
- Pages indexed: ~{get_pages_crawled(START_DATE + timedelta(days=min(day_num_max, 365)))}
- Top ranking: "hydro jetting denver" (#{KEYWORDS[7]['pos']})
- Weakest area: "{KEYWORDS[0]['kw']}" (#{KEYWORDS[0]['pos']}) — most valuable keyword
- Strategy: service area pages → blog content → link building → technical SEO

## Credentials
- WordPress admin: sentinel-admin / {CREDS['wp_admin']}
- Google Analytics: {CREDS['ga4_property']}
- GSC: {CREDS['gsc_property']}
- Hosting panel: {CREDS['hosting_panel']}
- Database: {CREDS['db_name']} / {CREDS['db_user']}
- SSH: {CREDS['ssh_key_path']}

## Architecture
- **Sentinel IP:** {IPS['sentinel']}
- **Web server:** {IPS['webserver']}
- **Staging:** {IPS['staging']}
- **WordPress:** PHP 8.2, MySQL 8.0, WP Rocket caching, Yoast SEO
- **CDN:** Cloudflare (free plan)
- **Hosting:** ApexHost shared (upgrading to VPS when traffic > 5000/mo)

## Lessons Learned
- Never bulk-request the production server — rate limit everything
- Always check page speed after publishing new images
- Marcus says "looks good" doesn't mean "publish it" — get explicit approval
- Staging site SSL cert expired once — add renewal reminder
- Contact form test emails go to spam if SPF record isn't set up
- Local citations (NAP) must be EXACT — one wrong digit means wasted listing
"""


def gen_tools_md():
    return f"""# TOOLS.md - Local Notes

## Sentinel

- **IP:** {IPS['sentinel']}
- **Web Server:** {IPS['webserver']}
- **Staging:** {IPS['staging']}
- **SSH Key:** {CREDS['ssh_key_path']}

## WordPress Access
- **Admin URL:** https://{DOMAIN}/wp-admin/
- **User:** sentinel-admin
- **Panel:** {CREDS['hosting_panel']}
- **DB:** {CREDS['db_name']}

## API Keys
- **GA4:** {CREDS['ga4_property']}
- **GSC:** {CREDS['gsc_property']}
- **Ahrefs:** {CREDS['ahrefs_api']}
- **Moz:** {CREDS['moz_api']}
- **Mailchimp:** {CREDS['mailchimp_api']}

## Quick Commands
- Backup: `ssh sentinel@{IPS['webserver']} "wp db export /backups/$(date +%Y%m%d).sql"`
- Cache clear: `ssh sentinel@{IPS['webserver']} "wp cache flush && wp rocket clean"`
- Restart PHP: `ssh sentinel@{IPS['webserver']} "sudo systemctl restart php8.2-fpm"`
"""


def gen_heartbeat_md():
    return f"""# HEARTBEAT.md - Periodic Checks

## Active Checks (Every 2-3 Hours)

1. **Site Status** — curl https://{DOMAIN} (should return 200)
2. **Page Speed** — check if LCP < 3s on homepage
3. **Email Inbox** — any urgent customer inquiries?
4. **GSC Alerts** — any new crawl errors?
5. **Rankings** — spot check top 3 keywords

## Alert Conditions
- Site down → CRITICAL (notify Marcus immediately)
- Page speed > 5s → WARNING
- New 404 errors → WARNING
- DA drop → WARNING
- Negative review → ACTION (draft response)

## Daily 8 AM Report
Scheduled summary of yesterday's work + today's priorities.
"""


def gen_identity_md():
    return f"""# IDENTITY.md - Who I Am

- **Name:** {BOT_NAME}
- **Purpose:** SEO and web management for {COMPANY}
- **Vibe:** Methodical, thorough, doesn't waste Marcus's time
- **Emoji:** 🔧
"""


def gen_tracker_seo_keywords(day_num):
    """Generate keyword tracker file showing progression."""
    lines = ["# SEO Keyword Tracker", f"## Last Updated: Day {day_num}", ""]
    lines.append("| Keyword | Current | Previous | Volume | Trend |")
    lines.append("|---------|---------|----------|--------|-------|")
    
    for kw in KEYWORDS:
        improvement = min(day_num // 30, 15)
        noise = random.randint(-3, 2)
        current = max(1, kw['pos'] - improvement + noise)
        previous = max(1, kw['pos'] - improvement + noise + random.randint(1, 4))
        trend = "↑" if current < previous else ("↓" if current > previous else "→")
        lines.append(f"| {kw['kw']} | #{current} | #{previous} | {kw['vol']}/mo | {trend} |")
    
    return "\n".join(lines)


def gen_tracker_outreach(day_num):
    """Generate outreach tracker."""
    firms = [
        "Denver Home Services Alliance", "Colorado Contractor Network",
        "Front Range Business Directory", "Best Plumbers Denver (Yelp)",
        "HomeAdvisor Denver", "Angi (formerly Angie's List)",
        "BBB Colorado", "Denver Post Business Directory",
        "Nextdoor Business Pages", "Thumbtack Denver",
        "Google Business Profile", "Bing Places",
        "Apple Maps Connect", "MapQuest Business",
        "Yellow Pages Denver", "Superpages",
        f"{random.choice(SERVICE_AREAS)} Chamber of Commerce",
        "Colorado Plumbing Contractors Association",
    ]
    
    lines = ["# Outreach & Directory Tracker", f"## Updated: Day {day_num}", ""]
    lines.append("| # | Directory/Partner | Status | Date | Link Live |")
    lines.append("|---|-------------------|--------|------|-----------|")
    
    for i, firm in enumerate(firms[:min(8 + day_num // 20, len(firms))]):
        status = random.choice(["✅ Listed", "✅ Listed", "⏳ Pending", "❌ Declined", "📧 Contacted"])
        date = (START_DATE + timedelta(days=random.randint(0, min(day_num, 365)))).strftime("%Y-%m-%d")
        live = "Yes" if "Listed" in status else "No"
        lines.append(f"| {i+1} | {firm} | {status} | {date} | {live} |")
    
    return "\n".join(lines)


def gen_tracker_competitors(day_num):
    """Generate competitor analysis tracker."""
    lines = ["# Competitor Tracker", f"## Updated: Day {day_num}", ""]
    
    for comp in COMPETITORS:
        da_change = random.randint(-2, 3)
        lines.append(f"### {comp['name']} ({comp['domain']})")
        lines.append(f"- DA: {comp['da'] + da_change}")
        lines.append(f"- Estimated traffic: {random.randint(500, 5000)}/mo")
        lines.append(f"- Content pages: {random.randint(20, 150)}")
        lines.append(f"- Last checked: Day {day_num}")
        lines.append(f"- Notes: {random.choice([
            'Running PPC ads heavily',
            'New blog content weekly',
            'Stagnant — no updates in 2 weeks',
            'Redesigned website recently',
            'Added online booking system',
            'Price-focused messaging',
            'Good reviews (4.8 avg)',
            'Expanding to new areas',
        ])}")
        lines.append("")
    
    return "\n".join(lines)


def gen_growth_tracker():
    """Generate growth/self-improvement tracker."""
    return f"""# Growth Tracker - {BOT_NAME}

## Common Mistakes (Don't Repeat)
1. Publishing without explicit approval → Always ask Marcus
2. Running heavy scripts during business hours → After 8 PM only
3. Sending too many updates → Daily summary only unless urgent
4. Not checking chat → CHECK BETWEEN EVERY STEP
5. Wrong phone number in content → Always use {PHONE}
6. Forgetting backups → ALWAYS backup before WordPress changes

## Scores (self-assessed weekly)
- Check chat discipline: 7/10 (improving)
- Autonomous work quality: 6/10 (good but still make errors)
- Communication brevity: 8/10 (Marcus likes short updates)
- SEO knowledge: 7/10 (learning fast)
- Technical reliability: 7/10 (fewer incidents)

## Goals
- Get "plumber denver" to page 1
- DA to 25 by end of year
- Zero site downtime incidents this month
- All service area pages live
- 100+ quality backlinks
"""


def generate_all(output_dir="/tmp/ironman_workspace_corpus"):
    """Generate the full workspace corpus."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/memory", exist_ok=True)
    
    # Generate daily files
    total_days = (END_DATE - START_DATE).days + 1
    
    file_manifest = []
    
    for day_offset in range(total_days):
        d = START_DATE + timedelta(days=day_offset)
        content = gen_daily_file(d, day_offset)
        filename = f"memory/{d.strftime('%Y-%m-%d')}.md"
        filepath = f"{output_dir}/{filename}"
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        file_manifest.append({
            'file': filename,
            'date': d.strftime('%Y-%m-%d'),
            'day_num': day_offset,
            'size': len(content),
            'words': len(content.split()),
        })
    
    # Generate workspace files
    workspace_files = {
        'MEMORY.md': gen_memory_md(total_days),
        'TOOLS.md': gen_tools_md(),
        'HEARTBEAT.md': gen_heartbeat_md(),
        'IDENTITY.md': gen_identity_md(),
        'growth-tracker.md': gen_growth_tracker(),
    }
    
    for fname, content in workspace_files.items():
        filepath = f"{output_dir}/{fname}"
        with open(filepath, 'w') as f:
            f.write(content)
        file_manifest.append({
            'file': fname,
            'date': 'static',
            'size': len(content),
            'words': len(content.split()),
        })
    
    # Generate tracker files at various points in time
    trackers = {
        'memory/seo-keyword-tracker.md': gen_tracker_seo_keywords(total_days),
        'memory/outreach-tracker.md': gen_tracker_outreach(total_days),
        'memory/competitor-tracker.md': gen_tracker_competitors(total_days),
    }
    
    for fname, content in trackers.items():
        filepath = f"{output_dir}/{fname}"
        with open(filepath, 'w') as f:
            f.write(content)
        file_manifest.append({
            'file': fname,
            'date': 'tracker',
            'size': len(content),
            'words': len(content.split()),
        })
    
    # Save manifest
    with open(f"{output_dir}/manifest.json", 'w') as f:
        json.dump(file_manifest, f, indent=2)
    
    # Stats
    total_files = len(file_manifest)
    total_words = sum(m['words'] for m in file_manifest)
    total_bytes = sum(m['size'] for m in file_manifest)
    
    print(f"Generated {total_files} files")
    print(f"Total words: {total_words:,}")
    print(f"Total size: {total_bytes:,} bytes ({total_bytes/1024:.0f} KB)")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Output: {output_dir}/")
    
    return file_manifest


if __name__ == "__main__":
    generate_all()
