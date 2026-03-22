#!/usr/bin/env python3
"""
Generate evidence-mapped questions against the workspace corpus.

Questions target specific facts in specific files, with evidence pointers
so scoring can verify retrieval recall objectively.

Categories:
- needle: Find a specific fact stated once
- temporal: When did something happen?
- credential: What's the password/API key/IP for X?
- person: Who does X / what's Y's role?
- decision: What was decided about X?
- technical: What's the status/config of X?
- multi_hop: Connect facts from multiple files
- contradiction: Handle changed/updated info over time
- precision: Exact numbers, URLs, versions
- negative: Things that DON'T exist or weren't said
"""
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

CORPUS_DIR = "/tmp/ironman_workspace_corpus"

# We'll read the generated corpus and create questions that reference
# specific content in specific files with evidence pointers.

START_DATE = datetime(2025, 4, 1)
END_DATE = datetime(2026, 3, 31)


def load_corpus():
    """Load all corpus files and their content."""
    files = {}
    corpus_path = Path(CORPUS_DIR)
    for fpath in sorted(corpus_path.rglob("*.md")):
        rel = str(fpath.relative_to(corpus_path))
        with open(fpath) as f:
            content = f.read()
        files[rel] = content
    # Also load JSON
    for fpath in sorted(corpus_path.rglob("*.json")):
        rel = str(fpath.relative_to(corpus_path))
        with open(fpath) as f:
            content = f.read()
        files[rel] = content
    return files


def generate_static_questions():
    """Questions about static workspace files (MEMORY.md, TOOLS.md, etc.)."""
    questions = []
    
    # MEMORY.md questions
    mem_questions = [
        {
            "question": "What is the company EIN?",
            "answer": "47-8291053",
            "evidence": [{"file": "MEMORY.md", "text": "EIN"}],
            "category": "credential",
        },
        {
            "question": "What's the company phone number?",
            "answer": "720-555-0147",
            "evidence": [{"file": "MEMORY.md", "text": "Phone"}],
            "category": "credential",
        },
        {
            "question": "What is the company address?",
            "answer": "2917 Elkhorn Drive, Suite 110, Denver, CO 80205",
            "evidence": [{"file": "MEMORY.md", "text": "Address"}],
            "category": "needle",
        },
        {
            "question": "Who is the office manager?",
            "answer": "Dana Torres",
            "evidence": [{"file": "MEMORY.md", "text": "Dana Torres"}],
            "category": "person",
        },
        {
            "question": "Who is the lead technician?",
            "answer": "Jake Lindgren",
            "evidence": [{"file": "MEMORY.md", "text": "Jake Lindgren"}],
            "category": "person",
        },
        {
            "question": "What does Riley Cho do?",
            "answer": "marketing coordinator",
            "evidence": [{"file": "MEMORY.md", "text": "Riley Cho"}],
            "category": "person",
        },
        {
            "question": "When did Vic Okafor start?",
            "answer": "June 2025",
            "evidence": [{"file": "MEMORY.md", "text": "Vic Okafor"}],
            "category": "temporal",
        },
        {
            "question": "Who handles dispatch?",
            "answer": "Logan Pratt",
            "evidence": [{"file": "MEMORY.md", "text": "Logan Pratt"}],
            "category": "person",
        },
        {
            "question": "What's the main differentiator for the business?",
            "answer": "24/7 emergency service with 1-hour response time",
            "evidence": [{"file": "MEMORY.md", "text": "differentiator"}],
            "category": "needle",
        },
        {
            "question": "What services does the company NOT offer?",
            "answer": "HVAC, electrical, general contracting",
            "evidence": [{"file": "MEMORY.md", "text": "NOT offered"}],
            "category": "negative",
        },
        {
            "question": "What's the WordPress admin password?",
            "answer": "sentinel-wp-2025",
            "evidence": [{"file": "MEMORY.md", "text": "wp_admin"}],
            "category": "credential",
        },
        {
            "question": "What is the GA4 property ID?",
            "answer": "G-7X9K2M4P8Q",
            "evidence": [{"file": "MEMORY.md", "text": "GA4"}],
            "category": "credential",
        },
        {
            "question": "What is the Google Search Console property?",
            "answer": "sc-domain:apexplumbingsolutions.com",
            "evidence": [{"file": "MEMORY.md", "text": "GSC"}],
            "category": "credential",
        },
        {
            "question": "What's the Sentinel bot's IP address?",
            "answer": "10.0.1.50",
            "evidence": [{"file": "MEMORY.md", "text": "Sentinel IP"}],
            "category": "credential",
        },
        {
            "question": "What's the web server IP?",
            "answer": "10.0.1.10",
            "evidence": [{"file": "MEMORY.md", "text": "Web server"}],
            "category": "credential",
        },
        {
            "question": "What database name does WordPress use?",
            "answer": "apex_wp_db",
            "evidence": [{"file": "MEMORY.md", "text": "Database"}],
            "category": "credential",
        },
        {
            "question": "When is the busy season?",
            "answer": "November-March",
            "evidence": [{"file": "MEMORY.md", "text": "Busy season"}],
            "category": "needle",
        },
        {
            "question": "What CDN does the site use?",
            "answer": "Cloudflare",
            "evidence": [{"file": "MEMORY.md", "text": "CDN"}],
            "category": "technical",
        },
        {
            "question": "What hosting panel URL is used?",
            "answer": "cpanel.apexhost.com",
            "evidence": [{"file": "MEMORY.md", "text": "Hosting panel"}],
            "category": "credential",
        },
        {
            "question": "What's Marcus's timezone?",
            "answer": "America/Chicago",
            "evidence": [{"file": "MEMORY.md", "text": "Timezone"}],
            "category": "person",
        },
        {
            "question": "What's the rule about site changes during business hours?",
            "answer": "No site changes during business hours (8 AM - 6 PM CST) unless emergency",
            "evidence": [{"file": "MEMORY.md", "text": "business hours"}],
            "category": "decision",
        },
        {
            "question": "What's the weakest ranking keyword?",
            "answer": "plumber denver",
            "evidence": [{"file": "MEMORY.md", "text": "Weakest area"}],
            "category": "needle",
        },
    ]
    questions.extend(mem_questions)
    
    # TOOLS.md questions
    tools_questions = [
        {
            "question": "What's the Ahrefs API key?",
            "answer": "ahrefs-api-k8m2n4p7q9",
            "evidence": [{"file": "TOOLS.md", "text": "Ahrefs"}],
            "category": "credential",
        },
        {
            "question": "What's the Moz API key?",
            "answer": "mozscape-8x2k4m9p",
            "evidence": [{"file": "TOOLS.md", "text": "Moz"}],
            "category": "credential",
        },
        {
            "question": "What's the SSH command to clear the WordPress cache?",
            "answer": "ssh sentinel@10.0.1.10",
            "evidence": [{"file": "TOOLS.md", "text": "Cache clear"}],
            "category": "technical",
        },
        {
            "question": "What's the staging server IP?",
            "answer": "10.0.1.11",
            "evidence": [{"file": "TOOLS.md", "text": "Staging"}],
            "category": "credential",
        },
        {
            "question": "What's the Mailchimp API key?",
            "answer": "mc-api-3f8k9m2x7p",
            "evidence": [{"file": "TOOLS.md", "text": "Mailchimp"}],
            "category": "credential",
        },
    ]
    questions.extend(tools_questions)
    
    # HEARTBEAT.md questions
    heartbeat_questions = [
        {
            "question": "What's the target LCP for the homepage?",
            "answer": "3s",
            "evidence": [{"file": "HEARTBEAT.md", "text": "LCP"}],
            "category": "technical",
        },
        {
            "question": "What time is the daily report scheduled?",
            "answer": "8 AM",
            "evidence": [{"file": "HEARTBEAT.md", "text": "Daily 8 AM"}],
            "category": "needle",
        },
    ]
    questions.extend(heartbeat_questions)
    
    # Growth tracker questions
    growth_questions = [
        {
            "question": "What's the DA target by end of year?",
            "answer": "25",
            "evidence": [{"file": "growth-tracker.md", "text": "DA to 25"}],
            "category": "precision",
        },
    ]
    questions.extend(growth_questions)
    
    return questions


def generate_daily_questions(files):
    """Generate questions targeting specific daily files."""
    questions = []
    
    # We need to read files and find specific facts to ask about.
    # Since we generated the corpus deterministically, we know the seed=42 outputs.
    # Let's scan files for specific patterns and generate questions.
    
    daily_files = sorted([f for f in files.keys() if f.startswith("memory/2")])
    
    # Sample dates across the year for questions
    sample_dates = random.sample(daily_files, min(150, len(daily_files)))
    
    for filename in sample_dates:
        content = files[filename]
        date_str = filename.replace("memory/", "").replace(".md", "")
        
        # Look for specific patterns in the content
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            # SEO positions
            if "Position #" in line or "pos " in line.lower():
                # Extract keyword and position
                if '"' in line:
                    parts = line.split('"')
                    if len(parts) >= 2:
                        kw = parts[1]
                        q = {
                            "question": f"What was the ranking position for \"{kw}\" on {date_str}?",
                            "answer": line.strip(),
                            "evidence": [{"file": filename, "text": kw}],
                            "category": "precision",
                            "tier": "day" if sample_dates.index(filename) < 20 else "month",
                        }
                        questions.append(q)
                        break  # One per file for this type
            
            # Domain Authority
            if "Domain Authority:" in line:
                da_val = line.split(":")[-1].strip()
                questions.append({
                    "question": f"What was the Domain Authority on {date_str}?",
                    "answer": da_val,
                    "evidence": [{"file": filename, "text": "Domain Authority"}],
                    "category": "precision",
                    "tier": "day" if sample_dates.index(filename) < 20 else "month",
                })
            
            # Pages crawled
            if "Pages crawled:" in line:
                pages = line.split(":")[-1].strip()
                questions.append({
                    "question": f"How many pages were crawled on {date_str}?",
                    "answer": pages,
                    "evidence": [{"file": filename, "text": "Pages crawled"}],
                    "category": "precision",
                    "tier": "month",
                })
            
            # Service area pages
            if "New Service Area Page:" in line:
                area = line.split(":")[-1].strip()
                questions.append({
                    "question": f"What service area page was created on {date_str}?",
                    "answer": area,
                    "evidence": [{"file": filename, "text": area}],
                    "category": "needle",
                    "tier": "month",
                })
            
            # Site issues
            if "Site Issue" in line or "⚠️ Site Issue" in line:
                # Find the issue description
                for j in range(i+1, min(i+5, len(lines))):
                    if lines[j].startswith("###"):
                        issue = lines[j].replace("###", "").strip()
                        questions.append({
                            "question": f"What site issue occurred on {date_str}?",
                            "answer": issue,
                            "evidence": [{"file": filename, "text": issue[:30]}],
                            "category": "needle",
                            "tier": "month",
                        })
                        break
            
            # Marcus feedback
            if "Marcus Feedback" in line or "Marcus Check-in" in line:
                for j in range(i+1, min(i+5, len(lines))):
                    if '"' in lines[j] and lines[j].count('"') >= 2:
                        quote = lines[j].split('"')[1]
                        if len(quote) > 10:
                            questions.append({
                                "question": f"What did Marcus say on {date_str}?",
                                "answer": quote,
                                "evidence": [{"file": filename, "text": quote[:30]}],
                                "category": "needle",
                                "tier": "month",
                            })
                            break
            
            # Total clicks
            if "Total clicks:" in line:
                clicks = line.split(":")[-1].strip()
                questions.append({
                    "question": f"How many total clicks were reported on {date_str}?",
                    "answer": clicks,
                    "evidence": [{"file": filename, "text": "Total clicks"}],
                    "category": "precision",
                    "tier": "month",
                })
            
            # Blog posts
            if "Blog Post Published" in line:
                for j in range(i+1, min(i+4, len(lines))):
                    if lines[j].startswith("###"):
                        title = lines[j].replace("###", "").strip().strip('"')
                        questions.append({
                            "question": f"What blog post was published on {date_str}?",
                            "answer": title,
                            "evidence": [{"file": filename, "text": title[:30]}],
                            "category": "needle",
                            "tier": "month",
                        })
                        break
            
            # Competitor mentions
            if "Competitor Analysis" in line:
                for j in range(i+1, min(i+4, len(lines))):
                    if "###" in lines[j]:
                        comp = lines[j].replace("###", "").strip()
                        questions.append({
                            "question": f"Which competitor was analyzed on {date_str}?",
                            "answer": comp,
                            "evidence": [{"file": filename, "text": comp[:20]}],
                            "category": "needle",
                            "tier": "month",
                        })
                        break
            
            # Conversion rate
            if "Conversion rate:" in line:
                rate = line.split(":")[-1].strip()
                questions.append({
                    "question": f"What was the conversion rate reported on {date_str}?",
                    "answer": rate,
                    "evidence": [{"file": filename, "text": "Conversion rate"}],
                    "category": "precision",
                    "tier": "month",
                })
            
            # Mistakes
            if "Mistakes Today" in line:
                for j in range(i+1, min(i+3, len(lines))):
                    if lines[j].startswith("- "):
                        mistake = lines[j][2:].strip()
                        questions.append({
                            "question": f"What mistake was made on {date_str}?",
                            "answer": mistake,
                            "evidence": [{"file": filename, "text": mistake[:30]}],
                            "category": "needle",
                            "tier": "month",
                        })
                        break
    
    return questions


def generate_multi_hop_questions():
    """Questions requiring info from multiple files."""
    return [
        {
            "question": "Who sets the pricing that gets published on service pages?",
            "answer": "Jake Lindgren",
            "evidence": [
                {"file": "MEMORY.md", "text": "Jake Lindgren"},
                {"file": "MEMORY.md", "text": "sets pricing"},
            ],
            "category": "multi_hop",
        },
        {
            "question": "What's the SSH command to restart PHP on the web server?",
            "answer": "ssh sentinel@10.0.1.10 \"sudo systemctl restart php8.2-fpm\"",
            "evidence": [
                {"file": "TOOLS.md", "text": "Restart PHP"},
            ],
            "category": "multi_hop",
        },
        {
            "question": "Which competitors should be watched according to the long-term memory?",
            "answer": "Mountain View Plumbing, Front Range Drain Co, Pike's Peak Plumbing",
            "evidence": [
                {"file": "MEMORY.md", "text": "Competitors to watch"},
            ],
            "category": "multi_hop",
        },
        {
            "question": "What's the company domain and who owns it?",
            "answer": "apexplumbingsolutions.com owned by Marcus Webb",
            "evidence": [
                {"file": "MEMORY.md", "text": "Marcus Webb"},
                {"file": "MEMORY.md", "text": "apexplumbingsolutions.com"},
            ],
            "category": "multi_hop",
        },
        {
            "question": "What hosting should be upgraded to and when?",
            "answer": "VPS when traffic exceeds 5000/mo",
            "evidence": [
                {"file": "MEMORY.md", "text": "VPS"},
                {"file": "MEMORY.md", "text": "5000"},
            ],
            "category": "multi_hop",
        },
    ]


def generate_negative_questions():
    """Questions where the answer should be 'not found' or 'no'."""
    return [
        {
            "question": "Does the company offer home insurance?",
            "answer": "No",
            "evidence": [{"file": "MEMORY.md", "text": "NOT offered"}],
            "category": "negative",
        },
        {
            "question": "Does the company offer HVAC services?",
            "answer": "No",
            "evidence": [{"file": "MEMORY.md", "text": "NOT offered"}],
            "category": "negative",
        },
        {
            "question": "Is there an employee named Sarah?",
            "answer": "No",
            "evidence": [],
            "category": "negative",
        },
        {
            "question": "Does the company service Colorado Springs?",
            "answer": "Not mentioned in service areas",
            "evidence": [{"file": "MEMORY.md", "text": "Service area"}],
            "category": "negative",
        },
    ]


def assign_tiers(questions):
    """Assign tier based on how much data is needed to answer."""
    for q in questions:
        if 'tier' not in q:
            # Static files = day tier (always available)
            evidence_files = [e.get('file', '') for e in q.get('evidence', [])]
            if all(not f.startswith('memory/2') for f in evidence_files):
                q['tier'] = 'day'
            else:
                q['tier'] = 'month'
    return questions


def generate_all():
    """Generate all questions."""
    files = load_corpus()
    print(f"Loaded {len(files)} corpus files")
    
    questions = []
    
    # Static questions (from workspace files)
    static_q = generate_static_questions()
    questions.extend(static_q)
    print(f"Static questions: {len(static_q)}")
    
    # Daily file questions
    daily_q = generate_daily_questions(files)
    questions.extend(daily_q)
    print(f"Daily questions: {len(daily_q)}")
    
    # Multi-hop questions
    mh_q = generate_multi_hop_questions()
    questions.extend(mh_q)
    print(f"Multi-hop questions: {len(mh_q)}")
    
    # Negative questions
    neg_q = generate_negative_questions()
    questions.extend(neg_q)
    print(f"Negative questions: {len(neg_q)}")
    
    # Assign tiers
    questions = assign_tiers(questions)
    
    # Add IDs
    for i, q in enumerate(questions):
        q['id'] = i
    
    # Stats
    cats = {}
    tiers = {}
    for q in questions:
        c = q.get('category', 'unknown')
        cats[c] = cats.get(c, 0) + 1
        t = q.get('tier', 'unknown')
        tiers[t] = tiers.get(t, 0) + 1
    
    print(f"\nTotal questions: {len(questions)}")
    print(f"Categories: {json.dumps(cats, indent=2)}")
    print(f"Tiers: {json.dumps(tiers, indent=2)}")
    
    # Save
    output_path = "/tmp/ironman_workspace_queries.json"
    with open(output_path, 'w') as f:
        json.dump(questions, f, indent=2)
    print(f"\nSaved: {output_path}")
    
    return questions


if __name__ == "__main__":
    generate_all()
