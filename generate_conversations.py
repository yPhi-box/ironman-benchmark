#!/usr/bin/env python3
"""
IRONMAN Conversation Corpus Generator v1.0
Generates RICH conversation blocks — multi-paragraph, realistic density.

Each message is a conversation block (5-15 sentences) not a one-liner.
Daily files should produce 30-100+ chunks when ingested by any chunking system.

Output: JSON array of {"timestamp", "message"} sorted chronologically.
Tiers are slices: day=1-20, month=1-600, year=all.

No LLM calls. Pure procedural generation with a world state that evolves.
"""
import json
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple


# ============================================================================
# WORLD STATE — everything that exists in the fictional company
# ============================================================================

COMPANY = {
    "name": "Nexus Dynamics",
    "industry": "Supply Chain AI",
    "hq": "1847 Cascade Avenue, Suite 300, Boulder, CO 80302",
    "founded": "2020-06-15",
    "ein": "83-4827156",
    "headcount": 94,
    "arr": 4600000,
    "burn_rate": 1270000,
    "runway_months": 18.7,
    "valuation": 1400000000,
}

FIRST_NAMES = [
    "Kai", "Mina", "Stefan", "Annika", "Leo", "Priya", "Derek", "Maya",
    "Noah", "Ava", "Ethan", "Lena", "Omar", "Yuki", "Bram", "Ingrid",
    "Caleb", "Freya", "Henrik", "Leila", "Matteo", "Nkechi", "Oscar",
    "Quinn", "Ravi", "Sofia", "Tomas", "Uma", "Victor", "Wren",
    "Adrian", "Bella", "Cyrus", "Diana", "Emil", "Fiona", "Gavin",
    "Hana", "Ivan", "Jade", "Kenji", "Luna", "Marco", "Nina",
    "Pavel", "Rosa", "Soren", "Tessa", "Uri", "Vera", "Anders",
    "Bianca", "Dante", "Elena", "Felix", "Greta", "Hugo", "Iris",
    "Jakob", "Kira", "Lars", "Maren", "Nico", "Olga", "Petra",
]

LAST_NAMES = [
    "Richter", "Park", "Lang", "Watanabe", "Martinez", "Nair", "Lam",
    "Singh", "Feld", "Thompson", "Cole", "Volkov", "Chen", "Tanaka",
    "Mueller", "Okonkwo", "Foster", "Yamamoto", "Horvat", "Osei",
    "Blackwood", "Camara", "Adeyemi", "Reyes", "Petrov", "Berg",
    "Rossi", "Holloway", "Kim", "Delgado", "Moreno", "Brooks",
    "Han", "Iqbal", "Ramirez", "Patel", "Alvarez", "Lee",
    "Nguyen", "Banerjee", "Reed", "Shah", "Wu", "Morgan",
    "Ortega", "Vega", "Becker", "Wei", "Costa", "Dubois",
]

ROLES = [
    "ML Engineer", "Backend Engineer", "Frontend Engineer", "Data Scientist",
    "DevOps Engineer", "Security Engineer", "QA Engineer", "Product Manager",
    "UX Designer", "Engineering Manager", "VP Engineering", "CTO",
    "Sales Rep", "Account Executive", "Customer Success Manager", "Support Engineer",
    "Finance Manager", "HR Manager", "Legal Counsel", "Office Manager",
    "Data Engineer", "Platform Engineer", "Site Reliability Engineer",
    "Solutions Architect", "Technical Writer",
]

TEAMS = [
    "Aurora", "Mercury", "Atlas", "Beacon", "Polaris", "Platform",
    "Infrastructure", "Security", "Sales", "Customer Success",
    "Finance", "People Ops", "Legal", "Product", "Design",
]

CITIES = [
    "Munich", "Portland", "Denver", "Austin", "Chicago", "Seattle",
    "Boston", "Miami", "Phoenix", "Minneapolis", "Irvine", "Edison",
    "Tucson", "Fort Collins", "Sacramento", "Atlanta", "Providence",
    "Boise", "Madison", "Ann Arbor", "Cleveland", "Omaha", "Dallas",
    "St. Louis", "San Diego", "El Paso", "Santa Fe", "Richmond",
    "Kansas City", "Karachi", "Sofia", "Pune", "Seoul", "Tokyo",
    "Stockholm", "Milan", "São Paulo", "Toronto", "Melbourne",
]

HOBBIES = [
    "pottery", "rock climbing", "chess", "piano", "photography",
    "woodworking", "trail running", "painting miniatures", "cooking Thai food",
    "surfing", "snowboarding", "playing cello", "drone racing",
    "baking sourdough", "collecting vinyl", "restoring old cameras",
    "spin class", "hot yoga", "bouldering", "fly fishing",
    "pickup basketball", "futsal", "golf", "softball", "trivia nights",
    "keeping reef tanks", "gardening tomatoes", "collecting keyboards",
    "trail photography", "growing chili plants",
]

ALLERGIES = [
    "shellfish", "peanuts", "eggs", "bee stings", "latex", "kiwi",
    "strawberries", "dairy", "sesame", "tree nuts", "gluten",
    "soy", "sulfa drugs", "penicillin", None, None, None, None,
]

PET_TYPES = [
    ("dog", ["Scout", "Maple", "Juniper", "Nox", "Biscuit", "Rosie", "Bear", "Ziggy"]),
    ("cat", ["Kernel", "Pixel", "Newton", "Ada", "Orbit", "Mochi", "Fig", "Sage"]),
    ("rabbit", ["Bramble", "Mochi", "Clover", "Hazel"]),
    ("parrot", ["Pico", "Rio", "Kiwi"]),
    ("husky", ["Sable", "Ghost", "Storm"]),
    ("corgi", ["Tofu", "Bento", "Waffle"]),
    ("beagle", ["Juniper", "Copper", "Daisy"]),
    ("dachshund", ["Fig", "Pretzel", "Olive"]),
    ("border collie", ["Nox", "Ace", "Dash"]),
    ("golden retriever", ["Maple", "Sunny", "Goldie"]),
]

CUSTOMER_COMPANIES = [
    ("Acme Manufacturing", "Manufacturing", "VP Operations"),
    ("Atlas Shipping", "Maritime Logistics", "Director of Supply Chain"),
    ("Blue Mesa Grocers", "Grocery Retail", "Head of Planning"),
    ("Helio Freight", "Freight & Logistics", "VP Logistics"),
    ("Northstar Medical Supply", "Healthcare", "Director of Procurement"),
    ("RedPeak Retail", "Retail", "VP Digital"),
    ("Summit Auto Parts", "Automotive", "COO"),
    ("Cascade Energy", "Energy", "Head of Operations"),
    ("Pinnacle Foods", "Food Distribution", "Supply Chain Director"),
    ("Ironwood Timber", "Forestry", "Operations Manager"),
    ("Cobalt Electronics", "Consumer Electronics", "VP Supply Chain"),
    ("Sterling Pharma", "Pharmaceuticals", "Chief Procurement Officer"),
    ("Verdant Agriculture", "AgTech", "Director of Logistics"),
    ("Crestline Aviation", "Aviation Services", "Head of Parts Supply"),
    ("Horizon Textiles", "Textiles", "VP Manufacturing"),
]

PROJECTS = [
    {"name": "Aurora", "desc": "core supply chain prediction engine", "tech": "Spark, Python, Kafka"},
    {"name": "Mercury", "desc": "forecast API for customer dashboards", "tech": "FastAPI, Redis, Snowflake"},
    {"name": "Atlas", "desc": "customer-facing SAML SSO portal", "tech": "React, Okta, Node.js"},
    {"name": "Beacon", "desc": "mobile warehouse scanning app", "tech": "React Native, Android, BLE"},
    {"name": "Polaris", "desc": "anomaly detection for supply chain data", "tech": "PyTorch, Kafka Streams"},
    {"name": "Vanguard", "desc": "internal admin and billing portal", "tech": "Next.js, Stripe, PostgreSQL"},
    {"name": "Meridian", "desc": "supplier onboarding automation", "tech": "Python, Airflow, S3"},
]

SERVERS = [
    "192.0.2.14", "192.0.2.27", "192.0.2.61", "198.51.100.18",
    "198.51.100.44", "198.51.100.88", "198.51.100.129", "203.0.113.9",
    "203.0.113.27", "203.0.113.73", "203.0.113.114", "10.40.1.5",
    "10.40.1.12", "10.40.1.88", "10.40.2.3",
]

JIRA_PREFIXES = ["ENG", "SEC", "OPS", "INF", "MOB", "PLT", "SAL", "HR", "FIN"]

MEETING_ROOMS = [
    "Flatirons-1", "Flatirons-2", "Cascade", "Alpine", "Summit",
    "Ridgeline", "Basecamp", "Treeline", "Timberline", "Keystone",
]

SLACK_CHANNELS = [
    "#engineering", "#infrastructure", "#security", "#sales",
    "#general", "#incidents", "#mobile", "#product", "#hiring",
    "#customer-success", "#finance", "#random", "#aurora",
    "#mercury", "#atlas-project", "#beacon-mobile",
]


def gen_phone():
    return f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"

def gen_email(first, last, domain="nexus-dynamics.example"):
    return f"{first.lower()}.{last.lower()}@{domain}"

def gen_employee_id():
    return f"NX-{random.randint(1000,9999)}"

def gen_desk():
    return f"{random.choice('ABCDEF')}{random.randint(1,6)}-{random.randint(1,20)}"

def gen_api_key(prefix, length=20):
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return prefix + "".join(random.choice(chars) for _ in range(length))

def gen_salary():
    return random.randint(85, 220) * 1000

def gen_arr():
    return random.choice([90, 120, 150, 190, 220, 280, 310, 340, 420, 480, 560, 610, 750, 890, 1100]) * 1000

def gen_jira(rng):
    return f"{rng.choice(JIRA_PREFIXES)}-{rng.randint(100,999)}"

def gen_zoom_id(rng):
    return f"{rng.randint(100,999)}-{rng.randint(1000,9999)}-{rng.randint(1000,9999)}"

def gen_pr_number(rng):
    return rng.randint(800, 2500)

def gen_build_version(rng):
    return f"{rng.randint(1,3)}.{rng.randint(0,9)}.{rng.randint(0,9)}"


class WorldState:
    """Tracks everything in the world. Evolves over time."""
    
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        random.seed(seed)
        self.people = []
        self.customers = []
        self.credentials = []
        self.projects = list(PROJECTS)
        self.incidents = []
        self.meetings = []
        self.policies = []
        self.events_log = []
        
        self._used_names = set()
        self._generate_initial_people(100)
        self._generate_initial_customers(12)
        self._generate_initial_credentials(25)
        self._generate_initial_policies()
    
    def _pick_name(self, force_duplicate_first=False):
        if force_duplicate_first and self.people:
            existing_first = self.rng.choice([p["first"] for p in self.people])
            last = self.rng.choice(LAST_NAMES)
            while f"{existing_first} {last}" in self._used_names:
                last = self.rng.choice(LAST_NAMES)
            self._used_names.add(f"{existing_first} {last}")
            return existing_first, last
        
        for _ in range(100):
            first = self.rng.choice(FIRST_NAMES)
            last = self.rng.choice(LAST_NAMES)
            if f"{first} {last}" not in self._used_names:
                self._used_names.add(f"{first} {last}")
                return first, last
        return self.rng.choice(FIRST_NAMES), self.rng.choice(LAST_NAMES)
    
    def _generate_initial_people(self, count=100):
        for i in range(count):
            force_dup = (i > 10 and i % 7 == 0)
            first, last = self._pick_name(force_duplicate_first=force_dup)
            
            pet = None
            if self.rng.random() < 0.4:
                pet_type, pet_names = self.rng.choice(PET_TYPES)
                pet = {"type": pet_type, "name": self.rng.choice(pet_names)}
            
            kids = None
            if self.rng.random() < 0.35:
                kid_count = self.rng.randint(1, 3)
                kid_names = self.rng.sample(FIRST_NAMES, kid_count)
                kids = kid_names
            
            person = {
                "first": first, "last": last, "full": f"{first} {last}",
                "role": self.rng.choice(ROLES),
                "team": self.rng.choice(TEAMS),
                "city": self.rng.choice(CITIES),
                "email": gen_email(first, last),
                "phone": gen_phone(),
                "employee_id": gen_employee_id(),
                "desk": gen_desk(),
                "salary": gen_salary(),
                "hobby": self.rng.choice(HOBBIES),
                "allergy": self.rng.choice(ALLERGIES),
                "pet": pet,
                "kids": kids,
                "start_date": f"202{self.rng.randint(0,4)}-{self.rng.randint(1,12):02d}-{self.rng.randint(1,28):02d}",
                "active": True,
                "role_history": [],
            }
            self.people.append(person)
    
    def _generate_initial_customers(self, count):
        for i in range(min(count, len(CUSTOMER_COMPANIES))):
            company, industry, champion_title = CUSTOMER_COMPANIES[i]
            first, last = self._pick_name()
            arr = gen_arr()
            domain = company.lower().replace(" ", "") + ".example"
            
            customer = {
                "company": company, "industry": industry,
                "arr": arr,
                "champion": f"{first} {last}",
                "champion_title": champion_title,
                "champion_email": gen_email(first, last, domain),
                "contract_start": f"2024-{self.rng.randint(1,12):02d}-{self.rng.randint(1,28):02d}",
                "contract_years": self.rng.choice([1, 2, 3]),
                "status": "active",
                "use_case": self.rng.choice([
                    "demand forecasting across distribution centers",
                    "supplier lead time optimization",
                    "real-time supply chain visibility",
                    "inventory optimization for retail stores",
                    "logistics route optimization",
                    "warehouse automation and scanning",
                ]),
            }
            self.customers.append(customer)
    
    def _generate_initial_credentials(self, count):
        prefixes = [
            ("dd-api-", "Datadog"), ("pd-svc-", "PagerDuty"),
            ("sk-test-nexus-", "OpenAI"), ("glsa-nexus-", "Grafana"),
            ("rk-test-nexus-", "Stripe"), ("twilio-", "Twilio"),
            ("ghp-", "GitHub"), ("AKIA", "AWS"),
        ]
        for i in range(count):
            prefix, service = prefixes[i % len(prefixes)]
            key = gen_api_key(prefix)
            self.credentials.append({
                "service": service, "key": key,
                "created": None, "rotated_from": None, "active": True,
            })
    
    def _generate_initial_policies(self):
        self.policies = [
            {"name": "office days", "value": "Tuesday through Thursday", "changed": None},
            {"name": "401k match", "value": "4%", "changed": None},
            {"name": "PTO policy", "value": "unlimited with 15-day minimum", "changed": None},
            {"name": "parental leave", "value": "16 weeks paid", "changed": None},
            {"name": "equipment budget", "value": "$3,000 per employee", "changed": None},
            {"name": "bereavement leave", "value": "3 days", "changed": None},
        ]
    
    def get_active_people(self):
        return [p for p in self.people if p["active"]]
    
    def get_active_customers(self):
        return [c for c in self.customers if c["status"] == "active"]
    
    def hire_person(self, timestamp):
        force_dup = self.rng.random() < 0.15
        first, last = self._pick_name(force_duplicate_first=force_dup)
        pet = None
        if self.rng.random() < 0.4:
            pet_type, pet_names = self.rng.choice(PET_TYPES)
            pet = {"type": pet_type, "name": self.rng.choice(pet_names)}
        kids = None
        if self.rng.random() < 0.3:
            kids = self.rng.sample(FIRST_NAMES, self.rng.randint(1, 2))
        person = {
            "first": first, "last": last, "full": f"{first} {last}",
            "role": self.rng.choice(ROLES),
            "team": self.rng.choice(TEAMS),
            "city": self.rng.choice(CITIES),
            "email": gen_email(first, last),
            "phone": gen_phone(),
            "employee_id": gen_employee_id(),
            "desk": gen_desk(),
            "salary": gen_salary(),
            "hobby": self.rng.choice(HOBBIES),
            "allergy": self.rng.choice(ALLERGIES),
            "pet": pet, "kids": kids,
            "start_date": timestamp[:10],
            "active": True, "role_history": [],
        }
        self.people.append(person)
        return person
    
    def fire_person(self, timestamp):
        active = self.get_active_people()
        if len(active) < 30:
            return None
        person = self.rng.choice(active)
        person["active"] = False
        person["end_date"] = timestamp[:10]
        return person
    
    def promote_person(self, timestamp):
        active = self.get_active_people()
        if not active: return None, None, None
        person = self.rng.choice(active)
        old_role = person["role"]
        new_role = self.rng.choice(ROLES)
        while new_role == old_role:
            new_role = self.rng.choice(ROLES)
        person["role_history"].append({"old": old_role, "new": new_role, "date": timestamp[:10]})
        person["role"] = new_role
        return person, old_role, new_role
    
    def move_team(self, timestamp):
        active = self.get_active_people()
        if not active: return None, None, None
        person = self.rng.choice(active)
        old_team = person["team"]
        new_team = self.rng.choice(TEAMS)
        while new_team == old_team:
            new_team = self.rng.choice(TEAMS)
        person["team"] = new_team
        return person, old_team, new_team
    
    def rotate_credential(self, timestamp):
        active_creds = [c for c in self.credentials if c["active"]]
        if not active_creds: return None
        cred = self.rng.choice(active_creds)
        old_key = cred["key"]
        new_key = gen_api_key(old_key[:len(old_key)//2])
        cred["rotated_from"] = old_key
        cred["key"] = new_key
        cred["rotated_date"] = timestamp[:10]
        return cred, old_key, new_key
    
    def change_policy(self, timestamp):
        policy = self.rng.choice(self.policies)
        old_val = policy["value"]
        changes = {
            "office days": ["Monday through Wednesday", "Tuesday and Wednesday only", "Monday through Thursday", "fully remote"],
            "401k match": ["5%", "6%", "4.5%", "8%"],
            "PTO policy": ["unlimited with 20-day minimum", "25 days fixed", "unlimited with 10-day minimum"],
            "parental leave": ["20 weeks paid", "18 weeks paid", "24 weeks paid"],
            "equipment budget": ["$4,000 per employee", "$5,000 per employee", "$3,500 per employee"],
            "bereavement leave": ["5 days", "7 days", "4 days"],
        }
        options = [v for v in changes.get(policy["name"], ["updated"]) if v != old_val]
        if not options: return None
        new_val = self.rng.choice(options)
        policy["changed"] = {"old": old_val, "new": new_val, "date": timestamp[:10]}
        policy["value"] = new_val
        return policy, old_val, new_val
    
    def add_customer(self, timestamp):
        remaining = [c for c in CUSTOMER_COMPANIES if c[0] not in [x["company"] for x in self.customers]]
        if not remaining: return None
        company, industry, title = self.rng.choice(remaining)
        first, last = self._pick_name()
        domain = company.lower().replace(" ", "") + ".example"
        customer = {
            "company": company, "industry": industry,
            "arr": gen_arr(),
            "champion": f"{first} {last}",
            "champion_title": title,
            "champion_email": gen_email(first, last, domain),
            "contract_start": timestamp[:10],
            "contract_years": self.rng.choice([1, 2, 3]),
            "status": "active",
            "use_case": self.rng.choice(["demand forecasting", "supplier optimization",
                "real-time visibility", "inventory optimization"]),
        }
        self.customers.append(customer)
        return customer
    
    def churn_customer(self, timestamp):
        active = self.get_active_customers()
        if len(active) < 5: return None
        customer = self.rng.choice(active)
        customer["status"] = "churned"
        customer["churn_date"] = timestamp[:10]
        return customer


# ============================================================================
# RICH MESSAGE GENERATORS — multi-paragraph conversation blocks
# ============================================================================

class MessageGenerator:
    """Generates RICH multi-paragraph messages from world state events."""
    
    def __init__(self, world: WorldState):
        self.world = world
        self.rng = world.rng
    
    def _context_padding(self, people, ts) -> str:
        """Add realistic surrounding context to a message block."""
        pads = []
        
        p1 = self.rng.choice(people) if people else None
        p2 = self.rng.choice(people) if people else None
        
        context_options = [
            lambda: f"This came up during the {self.rng.choice(['morning standup', 'afternoon sync', 'weekly review', 'team huddle', 'planning session', 'design review', 'sprint retro'])} today.",
            lambda: f"I followed up on Slack in {self.rng.choice(SLACK_CHANNELS)} and got confirmation.",
            lambda: f"The related Jira ticket is {gen_jira(self.rng)} — I added the details there too.",
            lambda: f"Meeting room was {self.rng.choice(MEETING_ROOMS)} in the Boulder office, with Zoom fallback {gen_zoom_id(self.rng)}.",
            lambda: f"I'll send the notes to the team by end of day. PR #{gen_pr_number(self.rng)} is already up for review." if self.rng.random() < 0.5 else f"Notes going out in the next hour.",
            lambda: f"{p1['full']} mentioned this during coffee break and I wanted to capture it before I forgot." if p1 else "",
            lambda: f"This was discussed at length — took about {self.rng.randint(15,90)} minutes to resolve.",
            lambda: f"Next check-in on this is {(datetime.fromisoformat(ts) + timedelta(days=self.rng.randint(1,14))).strftime('%Y-%m-%d')}.",
        ]
        
        # Pick 2-4 context sentences
        count = self.rng.randint(2, 4)
        chosen = self.rng.sample(context_options, min(count, len(context_options)))
        for fn in chosen:
            line = fn()
            if line:
                pads.append(line)
        
        return " ".join(pads)
    
    def person_intro(self, person, timestamp, people) -> str:
        """Rich new hire introduction block."""
        ctx = self._context_padding(people, timestamp)
        
        block = [
            f"New hire announcement: {person['full']} is joining us as {person['role']} on the {person['team']} team, starting {timestamp[:10]}.",
            f"{person['first']} is coming from {person['city']} and will be sitting at desk {person['desk']} in the Boulder office.",
            f"Employee ID is {person['employee_id']}, email is {person['email']}, phone is {person['phone']}.",
        ]
        
        if person["allergy"]:
            block.append(f"Important for team lunches: {person['first']} has an allergy to {person['allergy']}. Please keep this in mind when ordering food for meetings.")
        
        block.append(f"Outside of work, {person['first']} is into {person['hobby']}.")
        
        if person["pet"]:
            block.append(f"{person['first']} has a {person['pet']['type']} named {person['pet']['name']} — might show up on video calls.")
        
        if person["kids"]:
            names = " and ".join(person["kids"])
            block.append(f"Has {'a kid' if len(person['kids'])==1 else 'kids'} named {names}.")
        
        block.append(f"Salary for this role is ${person['salary']:,}. {person['first']}'s manager will be setting up 1:1s this week.")
        block.append(ctx)
        
        return "\n\n".join([" ".join(block[i:i+2]) for i in range(0, len(block), 2)])
    
    def person_departure(self, person, timestamp, people) -> str:
        ctx = self._context_padding(people, timestamp)
        block = [
            f"Unfortunately, {person['full']} is leaving Nexus Dynamics. Their last day will be {timestamp[:10]}.",
            f"{person['first']} was {person['role']} on the {person['team']} team, based in {person['city']}. They've been with us since {person.get('start_date', 'unknown')}.",
            f"We'll need to backfill this role — {person['first']}'s responsibilities included work on the {person['team']} project and they were a key contributor to several cross-team initiatives.",
            f"Employee ID {person['employee_id']} will be deactivated, and their email {person['email']} will be forwarded to the team lead for 90 days.",
            f"There will be a farewell lunch on their last day. {ctx}",
        ]
        return "\n\n".join(block)
    
    def person_promotion(self, person, old_role, new_role, timestamp, people) -> str:
        ctx = self._context_padding(people, timestamp)
        block = [
            f"Promotion announcement: {person['full']} is moving from {old_role} to {new_role}, effective {timestamp[:10]}.",
            f"{person['first']} has been on the {person['team']} team and has consistently delivered strong work. This promotion recognizes their growth and expanding responsibilities.",
            f"Their salary will be adjusted as part of this change. {person['first']} will continue to be based in {person['city']} and will keep their current desk at {person['desk']}.",
            f"Contact remains the same: {person['email']}, {person['phone']}. {ctx}",
        ]
        return "\n\n".join(block)
    
    def team_move(self, person, old_team, new_team, timestamp, people) -> str:
        ctx = self._context_padding(people, timestamp)
        block = [
            f"Team transfer: {person['full']} is moving from the {old_team} team to {new_team}, starting {timestamp[:10]}.",
            f"{person['first']} will be bringing their experience as {person['role']} to the {new_team} team. This move was discussed during the quarterly planning session and both team leads agreed it was the right call.",
            f"Their desk assignment ({person['desk']}) and contact info ({person['email']}, {person['phone']}) stay the same. Employee ID is still {person['employee_id']}.",
            f"{person['first']} will finish their current sprint on {old_team} before fully transitioning. {ctx}",
        ]
        return "\n\n".join(block)
    
    def credential_rotation(self, cred, old_key, new_key, timestamp, people) -> str:
        ctx = self._context_padding(people, timestamp)
        block = [
            f"Security credential rotation completed for {cred['service']}. The old key was {old_key} and has been disabled.",
            f"The new {cred['service']} key is {new_key}. This has been stored in the vault and all dependent services have been updated.",
            f"Please update any local development environments that reference the old key. If you see auth failures in your logs, this is probably why.",
            f"Rotation was performed at {timestamp[:16]} UTC. The Jira ticket tracking this is {gen_jira(self.rng)}. {ctx}",
        ]
        return "\n\n".join(block)
    
    def policy_change(self, policy, old_val, new_val, timestamp, people) -> str:
        ctx = self._context_padding(people, timestamp)
        block = [
            f"Policy update: the {policy['name']} policy is changing. The old policy was {old_val}. The new policy is {new_val}, effective {timestamp[:10]}.",
            f"This change was approved by the leadership team after reviewing employee feedback and benchmarking against industry standards.",
            f"HR will send out a formal announcement with full details. If you have questions, reach out to the People Ops team. The updated employee handbook will be posted by end of week.",
            f"{ctx}",
        ]
        return "\n\n".join(block)
    
    def customer_update(self, customer, timestamp, people) -> str:
        ctx = self._context_padding(people, timestamp)
        p = self.rng.choice(people) if people else {"full": "the account team"}
        name = p["full"] if isinstance(p, dict) else p
        
        templates = [
            [
                f"Customer update for {customer['company']} ({customer['industry']}): current ARR is ${customer['arr']:,}, and the relationship is in good shape.",
                f"Champion is {customer['champion']} ({customer['champion_title']}), reachable at {customer['champion_email']}. They've been responsive and engaged on {customer['use_case']}.",
                f"Contract started {customer['contract_start']}, {customer['contract_years']}-year term. Next touchpoint is a QBR with {name} leading the prep.",
                f"No major issues flagged. Support ticket volume is within normal range. {ctx}",
            ],
            [
                f"QBR with {customer['company']} went well today. They're at ${customer['arr']:,} ARR in the {customer['industry']} vertical.",
                f"{customer['champion']} ({customer['champion_email']}) is happy with progress on {customer['use_case']}. They asked about expanding to additional use cases next quarter.",
                f"Action items: {name} will send the updated ROI analysis, and the technical team will prep the integration roadmap. Contract is a {customer['contract_years']}-year deal.",
                f"Overall sentiment is positive. NPS from {customer['champion']} was 9/10. {ctx}",
            ],
            [
                f"Account review: {customer['company']}. Industry: {customer['industry']}. ARR: ${customer['arr']:,}. Status: {customer['status']}.",
                f"Primary contact: {customer['champion']}, {customer['champion_title']}. Email: {customer['champion_email']}. They've been the main driver for {customer['use_case']}.",
                f"The contract started on {customer['contract_start']} and runs for {customer['contract_years']} years. Renewal planning should start 90 days out.",
                f"{name} owns this account. No escalations pending. {ctx}",
            ],
        ]
        return "\n\n".join(self.rng.choice(templates))
    
    def customer_churn(self, customer, timestamp, people) -> str:
        ctx = self._context_padding(people, timestamp)
        block = [
            f"Bad news: we've lost {customer['company']}. They churned as of {timestamp[:10]}.",
            f"This was ${customer['arr']:,} ARR in the {customer['industry']} vertical. {customer['champion']} ({customer['champion_email']}) said they're going with a competitor who offered a lower price point.",
            f"Post-mortem: the main issues were pricing (they felt the per-DC cost was too high) and implementation timeline (they wanted faster onboarding for {customer['use_case']}). We should review these learnings for similar accounts.",
            f"All access will be revoked by end of day. Data retention policy applies for 90 days. {ctx}",
        ]
        return "\n\n".join(block)
    
    def new_customer(self, customer, timestamp, people) -> str:
        ctx = self._context_padding(people, timestamp)
        block = [
            f"New customer signed! {customer['company']} ({customer['industry']}) is coming on board at ${customer['arr']:,} ARR.",
            f"Champion is {customer['champion']} ({customer['champion_title']}), email {customer['champion_email']}. They're focused on {customer['use_case']}.",
            f"This is a {customer['contract_years']}-year deal, starting {timestamp[:10]}. Onboarding kickoff is being scheduled for next week.",
            f"Implementation plan: data ingestion first, then dashboard setup, then training. Target go-live is 6 weeks out. {ctx}",
        ]
        return "\n\n".join(block)
    
    def project_update(self, project, people, timestamp) -> str:
        ctx = self._context_padding(people, timestamp)
        lead = self.rng.choice(people) if people else {"full": "the team lead"}
        eng = self.rng.choice(people) if people else {"full": "an engineer"}
        name_lead = lead["full"] if isinstance(lead, dict) else lead
        name_eng = eng["full"] if isinstance(eng, dict) else eng
        
        status = self.rng.choice([
            "on track for the next milestone",
            "slightly behind — about a week",
            "ahead of schedule, which is rare",
            "blocked on an infrastructure dependency",
            "in code review, should merge by end of week",
            "wrapping up testing before the release candidate",
        ])
        
        sprint_pts = self.rng.randint(30, 89)
        total_pts = sprint_pts + self.rng.randint(10, 40)
        pr = gen_pr_number(self.rng)
        build = gen_build_version(self.rng)
        jira = gen_jira(self.rng)
        
        block = [
            f"Project {project['name']} update from {name_lead}: the {project['desc']} is {status}. Current tech stack: {project['tech']}.",
            f"Sprint progress: {sprint_pts}/{total_pts} story points completed. {name_eng} is working on the main feature branch, PR #{pr} is up for review. Target build is {build}.",
            f"Key blocker: {self.rng.choice(['waiting on API spec from partner team', 'test environment is flaky', 'dependency version conflict needs resolution', 'security review is pending', 'design handoff was delayed'])}. Tracked in {jira}.",
            f"Next checkpoint is {(datetime.fromisoformat(timestamp) + timedelta(days=self.rng.randint(2,7))).strftime('%Y-%m-%d')}. {ctx}",
        ]
        return "\n\n".join(block)
    
    def incident(self, people, timestamp) -> str:
        ctx = self._context_padding(people, timestamp)
        oncall = self.rng.choice(people) if people else {"full": "the on-call engineer"}
        helper = self.rng.choice(people) if people else {"full": "a teammate"}
        name_oncall = oncall["full"] if isinstance(oncall, dict) else oncall
        name_helper = helper["full"] if isinstance(helper, dict) else helper
        server = self.rng.choice(SERVERS)
        port = self.rng.choice([5432, 6379, 8080, 8443, 9090, 3000])
        duration = self.rng.randint(4, 120)
        jira = gen_jira(self.rng)
        
        root_cause = self.rng.choice([
            "stale DNS cache entries that pointed to a decommissioned host",
            "a non-backward-compatible schema change in the producer",
            "disk space running out on the primary database volume",
            "a misconfigured load balancer health check that was too aggressive",
            "an expired TLS certificate on the internal gateway",
            "a memory leak in the connection pool that accumulated over 48 hours",
            "a runaway cron job consuming all available CPU cores",
            "a bad config push that bypassed the staging environment",
        ])
        
        block = [
            f"Incident report: outage on {server}:{port} lasting {duration} minutes. Severity: {'Sev1' if duration > 30 else 'Sev2'}. Impact: {self.rng.choice(['customer-facing API returned 503s', 'internal dashboards were down', 'data pipeline stalled', 'webhook deliveries delayed', 'mobile app showed stale data'])}.",
            f"Root cause: {root_cause}. {name_oncall} was on-call and started investigating at {timestamp[:16]}. {name_helper} joined to help with the remediation.",
            f"Resolution: {self.rng.choice(['rolled back the config', 'restarted the affected service', 'expanded the disk volume', 'renewed the certificate', 'applied a hotfix', 'failed over to the secondary'])}. Service restored at {(datetime.fromisoformat(timestamp) + timedelta(minutes=duration)).strftime('%H:%M')}.",
            f"Postmortem is scheduled. Jira ticket: {jira}. Action items include adding monitoring for this failure mode and updating the runbook. {ctx}",
        ]
        return "\n\n".join(block)
    
    def meeting(self, people, timestamp) -> str:
        ctx = self._context_padding(people, timestamp)
        attendees = self.rng.sample(people, min(self.rng.randint(3, 7), len(people)))
        names = ", ".join(p["full"] for p in attendees)
        room = self.rng.choice(MEETING_ROOMS)
        zoom = gen_zoom_id(self.rng)
        topic = self.rng.choice([
            "Sprint planning", "Architecture review", "Product roadmap sync",
            "Security standup", "All-hands", "Board prep", "Customer review",
            "Hiring committee", "Incident postmortem", "Budget review",
            "Design critique", "Release readiness", "Quarterly planning",
        ])
        decision = self.rng.choice([
            "decided to push the launch by one week to allow more testing",
            "approved the budget increase to $45,000 for infrastructure upgrades",
            "agreed to hire two more engineers for the Aurora team",
            "chose to deprecate the old API endpoint after the migration window",
            "signed off on the security remediation plan with a 30-day timeline",
            "postponed the migration until next quarter due to resource constraints",
            "approved the new vendor contract pending legal review",
        ])
        follow_up = (datetime.fromisoformat(timestamp) + timedelta(days=self.rng.randint(1,7))).strftime('%Y-%m-%d')
        
        block = [
            f"{topic} meeting today in {room} (Zoom fallback: {zoom}). Attendees: {names}.",
            f"Main discussion: we {decision}. This was debated for about {self.rng.randint(15, 60)} minutes before reaching consensus.",
            f"Additional items covered: {self.rng.choice(['team velocity review', 'open headcount planning', 'customer escalation status', 'upcoming conference travel', 'Q&A with leadership'])}. Several follow-up items were assigned.",
            f"Action items are tracked in {gen_jira(self.rng)}. Next meeting is {follow_up}. {ctx}",
        ]
        return "\n\n".join(block)
    
    def infra_note(self, people, timestamp) -> str:
        ctx = self._context_padding(people, timestamp)
        server = self.rng.choice(SERVERS)
        port = self.rng.choice([5432, 6379, 8080, 8443, 9090, 3000, 27017])
        cpu = self.rng.randint(20, 85)
        mem = self.rng.randint(30, 90)
        p95 = self.rng.randint(5, 500)
        conn = self.rng.randint(20, 500)
        disk = self.rng.randint(30, 92)
        eng = self.rng.choice(people) if people else {"full": "the infra team"}
        name = eng["full"] if isinstance(eng, dict) else eng
        jira = gen_jira(self.rng)
        
        block = [
            f"Infrastructure status for {server}:{port} — CPU at {cpu}%, memory at {mem}%, disk at {disk}%. P95 latency is {p95}ms with {conn} active connections.",
            f"{name} ran the checks this morning. {'Everything looks stable and within thresholds.' if cpu < 70 and mem < 80 else 'Some metrics are elevated — we may need to scale up or investigate the root cause.'}",
            f"The last deployment to this host was {self.rng.choice(['yesterday', 'two days ago', 'last week', 'this morning'])}. Config changes tracked in {jira}. {'No alerts fired overnight.' if self.rng.random() < 0.7 else f'Got {self.rng.randint(1,5)} PagerDuty alerts overnight.'}",
            f"{ctx}",
        ]
        return "\n\n".join(block)
    
    def financial_note(self, people, timestamp) -> str:
        ctx = self._context_padding(people, timestamp)
        month_name = datetime.fromisoformat(timestamp).strftime('%B')
        burn = self.rng.randint(1100, 1400)
        payroll = self.rng.randint(550, 700)
        aws = self.rng.randint(22, 35)
        snow = self.rng.randint(15, 25)
        runway = self.rng.randint(14, 22)
        collections = self.rng.randint(80, 300)
        ar = self.rng.randint(100, 250)
        biggest = self.rng.choice(self.world.customers)["company"] if self.world.customers else "TBD"
        
        block = [
            f"Finance update for {month_name}: monthly burn is ${burn}K, putting us at {runway} months of runway. Cash position remains solid but we need to keep an eye on the AWS spend trend.",
            f"Payroll this month: ${payroll}K. Cloud costs: AWS ${aws}K, Snowflake ${snow}K. Total infrastructure spend is running about {self.rng.randint(2, 8)}% {'above' if self.rng.random() < 0.4 else 'below'} budget.",
            f"Collections update: ${collections}K received this period. Open accounts receivable is ${ar}K, with {biggest} being the largest outstanding invoice.",
            f"Board packet is being prepared. {ctx}",
        ]
        return "\n\n".join(block)
    
    def casual_mention(self, person, people, timestamp) -> str:
        """Rich casual mention with personal details woven in."""
        ctx = self._context_padding(people, timestamp)
        other = self.rng.choice(people) if people else None
        
        templates = []
        
        if person.get("kids"):
            kid = self.rng.choice(person["kids"])
            templates.append([
                f"Had lunch with {person['full']} today. {person['first']} had to duck out a bit early because {kid} had a {'soccer game' if self.rng.random() < 0.3 else 'school event' if self.rng.random() < 0.5 else 'dentist appointment'}.",
                f"We talked about the {person['team']} project and {person['first']} seems really engaged. {person['first']} is {person['role']} and has been doing solid work, especially on the recent sprint.",
                f"{person['first']} mentioned {kid} is {'starting middle school next year' if self.rng.random() < 0.3 else 'doing well in school' if self.rng.random() < 0.5 else 'really into sports lately'}. Nice to see the team bonding over non-work stuff.",
                f"{ctx}",
            ])
        
        if person.get("pet"):
            templates.append([
                f"{person['full']} brought {person['pet']['name']} (their {person['pet']['type']}) up on the video call today — {person['pet']['name']} made a cameo in the background during the standup.",
                f"We were talking about the weekend and {person['first']} mentioned taking {person['pet']['name']} to the {'park' if self.rng.random() < 0.5 else 'vet' if self.rng.random() < 0.3 else 'groomer'}. {person['first']} is based in {person['city']} and really loves the outdoor access there.",
                f"On the work front, {person['first']} is {person['role']} on {person['team']} and has been {self.rng.choice(['crushing it', 'keeping things on track', 'handling a lot right now', 'ramping up on new responsibilities'])}.",
                f"{ctx}",
            ])
        
        if person.get("hobby"):
            templates.append([
                f"Coffee chat with {person['full']} this morning. {person['first']} was talking about {person['hobby']} — apparently {'started recently' if self.rng.random() < 0.3 else 'has been doing it for years' if self.rng.random() < 0.5 else 'is getting really serious about it'}.",
                f"{person['first']} is from {person['city']} and says the {person['hobby']} scene there is {'great' if self.rng.random() < 0.5 else 'growing' if self.rng.random() < 0.5 else 'pretty competitive'}.",
                f"At work, {person['first']} is still {person['role']} on {person['team']}, desk {person['desk']}. Contact: {person['email']}.",
                f"{ctx}",
            ])
        
        if person.get("allergy"):
            templates.append([
                f"Reminder for the upcoming team lunch: {person['full']} is allergic to {person['allergy']}. We need to make sure the catering order accounts for this.",
                f"{person['first']} mentioned it again today when we were planning the {self.rng.choice(['sprint celebration', 'team outing', 'Friday lunch', 'welcome event'])}. Please double-check the menu with the restaurant.",
                f"On another note, {person['first']} ({person['role']}, {person['team']} team) has been {self.rng.choice(['doing great work on the latest feature', 'helping onboard the new hire', 'leading the code review process', 'wrapping up a key deliverable'])}.",
                f"{ctx}",
            ])
        
        if not templates:
            templates.append([
                f"Quick chat with {person['full']} today. {person['first']} is {person['role']} on the {person['team']} team, based in {person['city']}.",
                f"We talked about the current sprint and {person['first']} seems {'optimistic' if self.rng.random() < 0.5 else 'a bit concerned about the timeline'}. Employee ID {person['employee_id']}.",
                f"Reach them at {person['email']} or {person['phone']}. Desk: {person['desk']}.",
                f"{ctx}",
            ])
        
        return "\n\n".join(self.rng.choice(templates))
    
    def person_directory(self, person, people, timestamp) -> str:
        """Rich directory entry for a person."""
        ctx = self._context_padding(people, timestamp)
        block = [
            f"Directory entry: {person['full']} — {person['role']} on the {person['team']} team. Based in {person['city']}, joined on {person.get('start_date', 'unknown')}.",
            f"Contact information: email {person['email']}, phone {person['phone']}. Employee ID: {person['employee_id']}. Desk location: {person['desk']}.",
        ]
        
        personal = []
        if person.get("hobby"):
            personal.append(f"hobbies include {person['hobby']}")
        if person.get("allergy"):
            personal.append(f"allergic to {person['allergy']}")
        if person.get("pet"):
            personal.append(f"has a {person['pet']['type']} named {person['pet']['name']}")
        if person.get("kids"):
            personal.append(f"{'kid' if len(person['kids'])==1 else 'kids'} named {' and '.join(person['kids'])}")
        
        if personal:
            block.append(f"Personal notes: {'; '.join(personal)}. Salary: ${person['salary']:,}.")
        
        if person.get("role_history"):
            latest = person["role_history"][-1]
            block.append(f"Role history: was previously {latest['old']}, changed to {latest['new']} on {latest['date']}.")
        
        block.append(ctx)
        return "\n\n".join(block)


# ============================================================================
# CORPUS GENERATOR — orchestrates the whole thing
# ============================================================================

class ConversationCorpusGenerator:
    def __init__(self, seed=42):
        self.world = WorldState(seed)
        self.gen = MessageGenerator(self.world)
        self.messages = []
        self.facts = []
    
    def generate(self, days=365) -> List[dict]:
        start_date = datetime(2025, 3, 15, 8, 0, 0)
        
        for day_num in range(days):
            current_date = start_date + timedelta(days=day_num)
            is_weekend = current_date.weekday() >= 5
            
            if is_weekend:
                msg_count = self.world.rng.choices([12, 18, 22, 28], weights=[25, 35, 25, 15])[0]
            else:
                if self.world.rng.random() < 0.08:
                    msg_count = self.world.rng.randint(55, 75)
                elif self.world.rng.random() < 0.05:
                    msg_count = self.world.rng.randint(30, 40)
                else:
                    msg_count = self.world.rng.randint(40, 55)
            
            day_messages = self._generate_day(current_date, msg_count, day_num)
            self.messages.extend(day_messages)
        
        return self.messages
    
    def _generate_day(self, date: datetime, msg_count: int, day_num: int) -> list:
        messages = []
        active_people = self.world.get_active_people()
        
        for i in range(msg_count):
            hour = 8 + int((i / max(msg_count, 1)) * 10)
            minute = self.world.rng.randint(0, 59)
            ts = date.replace(hour=min(hour, 18), minute=minute).isoformat()
            
            msg = self._pick_message_type(ts, day_num, active_people)
            if msg:
                messages.append({"timestamp": ts, "message": msg})
        
        return messages
    
    def _pick_message_type(self, ts, day_num, people) -> str:
        # World state events — phased by tier
        if day_num > 0:
            r = self.world.rng.random()
            
            if day_num >= 3:
                if r < 0.03:
                    person = self.world.hire_person(ts)
                    self._record_fact(ts, "hire", person)
                    return self.gen.person_intro(person, ts, people)
            
            if day_num >= 7:
                if r < 0.04:
                    person, old, new = self.world.move_team(ts)
                    if person:
                        self._record_fact(ts, "team_move", {"person": person, "old": old, "new": new})
                        return self.gen.team_move(person, old, new, ts, people)
            
            if day_num >= 14:
                if r < 0.05:
                    person, old, new = self.world.promote_person(ts)
                    if person:
                        self._record_fact(ts, "promotion", {"person": person, "old": old, "new": new})
                        return self.gen.person_promotion(person, old, new, ts, people)
                
                if r < 0.07:
                    result = self.world.rotate_credential(ts)
                    if result:
                        cred, old, new = result
                        self._record_fact(ts, "credential_rotation", {"service": cred["service"], "old": old, "new": new})
                        return self.gen.credential_rotation(cred, old, new, ts, people)
            
            if day_num >= 31:
                if r < 0.04:
                    person = self.world.fire_person(ts)
                    if person:
                        self._record_fact(ts, "departure", person)
                        return self.gen.person_departure(person, ts, people)
                
                if r < 0.06:
                    person = self.world.hire_person(ts)
                    self._record_fact(ts, "hire", person)
                    return self.gen.person_intro(person, ts, people)
                
                if r < 0.09:
                    person, old, new = self.world.promote_person(ts)
                    if person:
                        self._record_fact(ts, "promotion", {"person": person, "old": old, "new": new})
                        return self.gen.person_promotion(person, old, new, ts, people)
                
                if r < 0.12:
                    person, old, new = self.world.move_team(ts)
                    if person:
                        self._record_fact(ts, "team_move", {"person": person, "old": old, "new": new})
                        return self.gen.team_move(person, old, new, ts, people)
                
                if r < 0.16:
                    result = self.world.rotate_credential(ts)
                    if result:
                        cred, old, new = result
                        self._record_fact(ts, "credential_rotation", {"service": cred["service"], "old": old, "new": new})
                        return self.gen.credential_rotation(cred, old, new, ts, people)
                
                if r < 0.18:
                    result = self.world.change_policy(ts)
                    if result:
                        policy, old, new = result
                        self._record_fact(ts, "policy_change", {"name": policy["name"], "old": old, "new": new})
                        return self.gen.policy_change(policy, old, new, ts, people)
                
                if r < 0.20:
                    customer = self.world.add_customer(ts)
                    if customer:
                        self._record_fact(ts, "new_customer", customer)
                        return self.gen.new_customer(customer, ts, people)
                
                churned_count = sum(1 for c in self.world.customers if c["status"] == "churned")
                if r < 0.22 and day_num > 90 and churned_count < 4:
                    customer = self.world.churn_customer(ts)
                    if customer:
                        self._record_fact(ts, "customer_churn", customer)
                        return self.gen.customer_churn(customer, ts, people)
        
        # Regular message types (weighted)
        msg_types = [
            (0.15, "person_mention"),
            (0.15, "project_update"),
            (0.15, "meeting"),
            (0.12, "customer_update"),
            (0.10, "infra"),
            (0.08, "incident"),
            (0.08, "financial"),
            (0.10, "casual"),
            (0.07, "person_details"),
        ]
        
        choice = self.world.rng.random()
        cumulative = 0
        selected = "person_mention"
        for weight, mtype in msg_types:
            cumulative += weight
            if choice < cumulative:
                selected = mtype
                break
        
        if not people:
            return self.gen.infra_note(people, ts)
        
        if selected == "person_mention":
            person = self.world.rng.choice(people)
            return self.gen.casual_mention(person, people, ts)
        elif selected == "project_update":
            project = self.world.rng.choice(self.world.projects)
            return self.gen.project_update(project, people, ts)
        elif selected == "meeting":
            return self.gen.meeting(people, ts)
        elif selected == "customer_update":
            customers = self.world.get_active_customers()
            if customers:
                customer = self.world.rng.choice(customers)
                return self.gen.customer_update(customer, ts, people)
            return self.gen.financial_note(people, ts)
        elif selected == "infra":
            return self.gen.infra_note(people, ts)
        elif selected == "incident":
            return self.gen.incident(people, ts)
        elif selected == "financial":
            return self.gen.financial_note(people, ts)
        elif selected == "casual":
            person = self.world.rng.choice(people)
            return self.gen.casual_mention(person, people, ts)
        elif selected == "person_details":
            person = self.world.rng.choice(people)
            return self.gen.person_directory(person, people, ts)
        
        return self.gen.infra_note(people, ts)
    
    def _record_fact(self, ts, fact_type, data):
        self.facts.append({"timestamp": ts, "type": fact_type, "data": data})
    
    def save(self, output_path: str):
        with open(output_path, "w") as f:
            json.dump(self.messages, f, indent=2)
        
        state_path = output_path.replace(".json", "_world_state.json")
        state = {
            "people": self.world.people,
            "customers": self.world.customers,
            "credentials": self.world.credentials,
            "projects": [p for p in self.world.projects],
            "policies": self.world.policies,
            "facts": self.facts,
        }
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2, default=str)
        
        return output_path, state_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate IRONMAN conversation corpus")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="/tmp/ironman_corpus.json")
    args = parser.parse_args()
    
    print(f"Generating {args.days}-day corpus (seed={args.seed})...")
    gen = ConversationCorpusGenerator(seed=args.seed)
    messages = gen.generate(days=args.days)
    
    corpus_path, state_path = gen.save(args.output)
    
    total_words = sum(len(m["message"].split()) for m in messages)
    total_chars = sum(len(m["message"]) for m in messages)
    dates = set(m["timestamp"][:10] for m in messages)
    
    # Calculate avg file size
    files = {}
    for m in messages:
        d = m["timestamp"][:10]
        files[d] = files.get(d, 0) + len(m["message"]) + 50  # 50 for header
    avg_file_kb = sum(files.values()) / len(files) / 1024 if files else 0
    
    print(f"\nCorpus generated:")
    print(f"  Messages: {len(messages)}")
    print(f"  Words: {total_words:,}")
    print(f"  Characters: {total_chars:,}")
    print(f"  Days with messages: {len(dates)}")
    print(f"  Date range: {messages[0]['timestamp'][:10]} to {messages[-1]['timestamp'][:10]}")
    print(f"  People: {len(gen.world.people)} ({len(gen.world.get_active_people())} active)")
    print(f"  Customers: {len(gen.world.customers)} ({len(gen.world.get_active_customers())} active)")
    print(f"  Credentials: {len(gen.world.credentials)}")
    print(f"  World events: {len(gen.facts)}")
    print(f"  Avg file size: {avg_file_kb:.1f} KB")
    print(f"  Est. chunks/file (at 800 chars): {int(avg_file_kb * 1024 / 800)}")
    print(f"\n  Tier slices:")
    print(f"    Day (1-50):     messages[0:50]")
    print(f"    Month (1-1200): messages[0:1200]")
    print(f"    Year (all):     messages[0:{len(messages)}]")
    print(f"\n  Saved: {corpus_path}")
    print(f"  State: {state_path}")


if __name__ == "__main__":
    main()
