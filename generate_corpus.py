#!/usr/bin/env python3
"""
IRONMAN Corpus Generator
Generates a massive, internally-consistent synthetic workspace for benchmarking.
All data is fictional — zero personal information from any real person.

Usage:
    python3 generate_corpus.py --scale medium --output ./corpus
    
Scales:
    small:  ~100 files, ~500 chunks
    medium: ~1,000 files, ~5,000 chunks
    large:  ~5,000 files, ~25,000 chunks
    stress: ~10,000 files, ~50,000 chunks
"""
import argparse
import json
import random
import os
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ============================================================================
# SEED DATA — Building blocks for consistent generation
# ============================================================================

COMPANY = {
    "name": "Nexus Dynamics",
    "legal": "Nexus Dynamics Inc.",
    "founded": "2020-06-15",
    "founders": ["Clara Whitfield", "Tomás Reyes"],
    "hq": "1847 Cascade Avenue, Suite 300, Boulder, CO 80302",
    "state_inc": "Delaware",
    "ein": "83-4827156",
    "mission": "Building autonomous supply chain intelligence for global enterprises.",
    "industry": "Supply Chain AI / Enterprise Software",
}

DEPARTMENTS = [
    "Engineering", "Product", "Design", "QA", "DevOps", "Security",
    "Data Science", "Sales", "Marketing", "Customer Success", "Finance",
    "Legal", "HR", "Operations", "Research",
]

FIRST_NAMES = [
    "Clara", "Tomás", "Priya", "James", "Yuki", "Marcus", "Fatima", "Chen",
    "Sasha", "Devon", "Amara", "Nikolai", "Lena", "Rafael", "Ingrid", "Omar",
    "Zara", "Kenji", "Astrid", "Dante", "Nia", "Viktor", "Elena", "Kwame",
    "Mei", "Alejandro", "Signe", "Ravi", "Camille", "Henrik", "Adaeze", "Finn",
    "Lucia", "Tariq", "Maren", "Kofi", "Isabelle", "Dmitri", "Aisha", "Lars",
    "Rosa", "Idris", "Hana", "Matteo", "Nkechi", "Anders", "Yara", "Stefan",
    "Olga", "Jamal", "Petra", "Kai", "Constance", "Elio", "Freya", "Nolan",
    "Maeve", "Joaquin", "Solene", "Theo", "Ximena", "Rohan", "Brigitte", "Emeka",
    "Leila", "Oscar", "Dalia", "Hugo", "Chiara", "Rex", "Annika", "Bram",
    "Pilar", "Soren", "Vivienne", "Atlas", "Nadia", "Felix", "Aurelia", "Caspian",
]

LAST_NAMES = [
    "Whitfield", "Reyes", "Sharma", "Okonkwo", "Tanaka", "DeLuca", "Al-Rashid",
    "Wei", "Volkov", "Osei", "Nakamura", "Santos", "Lindqvist", "Petrov",
    "Blackwood", "Kim", "Johansson", "Adeyemi", "Kowalski", "Chen",
    "Moreau", "Gupta", "Andersson", "Nkosi", "Fernandez", "Yilmaz",
    "Berger", "Takahashi", "Olsen", "Mensah", "Rossi", "Park",
    "Novak", "Dubois", "Ishikawa", "Larsson", "Okafor", "Horvat",
    "Lebedev", "Tran", "Magnusson", "Diallo", "Bauer", "Yamamoto",
    "Hansen", "Asante", "Richter", "Ito", "Pedersen", "Owusu",
    "Fischer", "Sato", "Lund", "Mensah", "Weber", "Morita",
    "Dahl", "Kone", "Schmidt", "Fujita", "Berg", "Traore",
    "Mueller", "Hayashi", "Holm", "Bamba", "Hoffmann", "Watanabe",
    "Strand", "Camara", "Braun", "Mori", "Nyman", "Toure",
    "Lang", "Ueda", "Vik", "Keita", "Krause", "Ogawa",
]

CITIES = [
    ("Boulder", "CO"), ("Portland", "OR"), ("Austin", "TX"), ("Seattle", "WA"),
    ("Denver", "CO"), ("Chicago", "IL"), ("Boston", "MA"), ("San Francisco", "CA"),
    ("New York", "NY"), ("Los Angeles", "CA"), ("Miami", "FL"), ("Atlanta", "GA"),
    ("Nashville", "TN"), ("Minneapolis", "MN"), ("Salt Lake City", "UT"),
    ("London", "UK"), ("Berlin", "DE"), ("Stockholm", "SE"), ("Tokyo", "JP"),
    ("Singapore", "SG"), ("Toronto", "CA"), ("Sydney", "AU"), ("Dublin", "IE"),
    ("Amsterdam", "NL"), ("Zurich", "CH"),
]

UNIVERSITIES = [
    "MIT", "Stanford", "Carnegie Mellon", "UC Berkeley", "Georgia Tech",
    "Caltech", "Oxford", "Cambridge", "ETH Zurich", "University of Toronto",
    "Imperial College London", "TU Munich", "University of Tokyo", "NUS",
    "KAIST", "Tsinghua", "IIT Bombay", "EPFL", "University of Michigan",
    "Columbia", "Harvard", "Princeton", "Yale", "Cornell", "Brown",
]

PREV_COMPANIES = [
    "Google", "Amazon", "Microsoft", "Apple", "Meta", "Netflix", "Stripe",
    "Shopify", "Datadog", "Snowflake", "Databricks", "Confluent", "MongoDB",
    "Elastic", "Cloudflare", "Twilio", "Palantir", "Salesforce", "Oracle",
    "SAP", "IBM", "Cisco", "VMware", "Red Hat", "Atlassian",
    "GitHub", "GitLab", "JetBrains", "Docker", "HashiCorp",
]

HOBBIES = [
    "rock climbing", "marathon running", "woodworking", "painting",
    "photography", "brewing beer", "playing piano", "chess",
    "mountain biking", "surfing", "pottery", "gardening",
    "cooking", "reading sci-fi", "board games", "hiking",
    "sailing", "archery", "birdwatching", "calligraphy",
    "playing guitar", "yoga", "scuba diving", "astronomy",
    "beekeeping", "knitting", "skateboarding", "fencing",
    "drone racing", "bouldering", "foraging", "metalworking",
]

PET_TYPES = [
    ("dog", ["Luna", "Milo", "Pixel", "Byte", "Scout", "Ziggy", "Maple", "Finn",
             "Nori", "Sage", "Atlas", "Echo", "Pepper", "Cleo", "Rex", "Biscuit"]),
    ("cat", ["Kernel", "Panic", "Mutex", "Socket", "Whiskers", "Shadow", "Mochi",
             "Olive", "Pepper", "Nimbus", "Toast", "Cosmo", "Pebble", "Void"]),
    ("rabbit", ["Clover", "Hazel", "Nutmeg", "Basil", "Thistle", "Bramble"]),
    ("none", []),
]

ROLES = [
    "Software Engineer", "Senior Software Engineer", "Staff Engineer",
    "Principal Engineer", "Engineering Manager", "Senior Engineering Manager",
    "Director of Engineering", "VP of Engineering",
    "Product Manager", "Senior Product Manager", "Director of Product",
    "VP of Product", "Chief Product Officer",
    "Designer", "Senior Designer", "Design Lead", "Head of Design",
    "Data Scientist", "Senior Data Scientist", "ML Engineer", "Data Engineer",
    "DevOps Engineer", "Senior DevOps Engineer", "SRE", "Platform Engineer",
    "Security Engineer", "Senior Security Engineer", "Security Lead", "CISO",
    "QA Engineer", "Senior QA Engineer", "QA Lead",
    "Technical Writer", "Developer Advocate",
    "Account Executive", "Senior AE", "Sales Director", "VP of Sales",
    "Solutions Engineer", "Customer Success Manager",
    "Recruiter", "HR Business Partner", "Head of People",
    "Financial Analyst", "Controller", "CFO",
    "General Counsel", "Paralegal",
]

PROJECT_NAMES = [
    "Aurora", "Beacon", "Catalyst", "Dynamo", "Eclipse", "Falcon",
    "Genesis", "Horizon", "Icarus", "Javelin", "Keystone", "Labyrinth",
    "Meridian", "Nova", "Olympus", "Phoenix", "Quantum", "Raptor",
    "Sentinel", "Titan", "Umbra", "Vanguard", "Wavelength", "Xenon",
    "Zenith", "Apex", "Bastion", "Cipher", "Delphi", "Ember",
    "Flux", "Gryphon", "Helix", "Impulse", "Juno",
]

CUSTOMER_COMPANIES = [
    "Acme Manufacturing", "GlobalTech Solutions", "Pinnacle Logistics",
    "Vertex Healthcare", "Cascade Energy", "Summit Retail Group",
    "Ironclad Defense", "Silverline Financial", "Cobalt Mining Corp",
    "Atlas Shipping", "Meridian Foods", "Prism Pharmaceuticals",
    "Quantum Aerospace", "Redwood Construction", "Sapphire Electronics",
    "Trident Maritime", "Unity Automotive", "Vantage Media",
    "Windward Agriculture", "Zenith Telecommunications",
    "Pacific Freight", "Nordic Textiles", "Emerald Hotels",
    "Diamond Logistics", "Obsidian Security", "Coral Healthcare",
    "Amber Energy", "Jade Technology", "Onyx Manufacturing",
    "Ruby Financial", "Topaz Consulting", "Opal Retail",
]

TECH_STACKS = {
    "languages": ["Python", "Rust", "Go", "TypeScript", "Java", "Kotlin", "C++", "Scala"],
    "databases": ["PostgreSQL", "CockroachDB", "MongoDB", "DynamoDB", "Redis", "Cassandra",
                  "ClickHouse", "TimescaleDB", "ScyllaDB", "FoundationDB"],
    "queues": ["Kafka", "RabbitMQ", "SQS", "Pulsar", "NATS", "Redis Streams"],
    "clouds": ["AWS", "GCP", "Azure", "Cloudflare"],
    "frameworks": ["FastAPI", "Django", "Express", "Spring Boot", "Axum", "Gin"],
    "ml": ["PyTorch", "TensorFlow", "scikit-learn", "XGBoost", "ONNX", "Triton"],
}

INCIDENT_SEVERITIES = ["P1 Critical", "P2 High", "P3 Medium", "P4 Low"]

ALLERGIES = [
    "shellfish", "peanuts", "tree nuts", "dairy", "gluten", "eggs",
    "soy", "sesame", "bee stings", "penicillin", "latex", None, None, None, None,
]

CERTIFICATIONS = [
    "CISSP", "OSCP", "CEH", "AWS Solutions Architect", "CKA",
    "PMP", "CCNA", "GCP Professional", "Azure Architect",
    "CISM", "CompTIA Security+", "Terraform Associate",
]


class WorldState:
    """Maintains consistent state across all generated files."""
    
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.people = []
        self.projects = []
        self.customers = []
        self.incidents = []
        self.org_chart = {}  # person_id -> manager_id
        self.project_assignments = {}  # project_name -> [person_ids]
        self.role_history = {}  # person_id -> [(date, old_role, new_role)]
        self.ip_registry = {}  # server_name -> ip
        self.credentials = {}
        self.timeline = []  # (date, event_description, related_entities)
        self.contradictions = []  # (topic, old_value, new_value, old_file, new_file)
        self.disambiguation_groups = {}  # name -> [person_ids]
        
    def generate_person(self, idx: int, force_name: str = None) -> dict:
        """Generate a person with rich, unique details."""
        if force_name:
            first, last = force_name.split(" ", 1)
        else:
            first = self.rng.choice(FIRST_NAMES)
            last = self.rng.choice(LAST_NAMES)
        
        name = f"{first} {last}"
        age = self.rng.randint(24, 62)
        birth_year = 2026 - age
        birth_month = self.rng.randint(1, 12)
        birth_day = self.rng.randint(1, 28)
        city, state = self.rng.choice(CITIES)
        dept = self.rng.choice(DEPARTMENTS)
        role = self.rng.choice([r for r in ROLES if self._role_fits_dept(r, dept)])
        university = self.rng.choice(UNIVERSITIES)
        prev_company = self.rng.choice(PREV_COMPANIES)
        years_exp = self.rng.randint(2, age - 22)
        start_year = self.rng.randint(2020, 2025)
        start_month = self.rng.randint(1, 12)
        salary = self.rng.randint(85, 350) * 1000
        
        hobby1, hobby2 = self.rng.sample(HOBBIES, 2)
        allergy = self.rng.choice(ALLERGIES)
        
        pet_type, pet_names = self.rng.choice(PET_TYPES)
        pet_name = self.rng.choice(pet_names) if pet_names else None
        
        # Family
        has_partner = self.rng.random() > 0.35
        partner_name = f"{self.rng.choice(FIRST_NAMES)} {last}" if has_partner else None
        num_kids = self.rng.choice([0, 0, 0, 1, 1, 2, 2, 3]) if has_partner else 0
        kids = []
        for _ in range(num_kids):
            kid_name = self.rng.choice(FIRST_NAMES)
            kid_age = self.rng.randint(1, 18)
            kids.append({"name": kid_name, "age": kid_age})
        
        phone_area = self.rng.randint(200, 999)
        phone_mid = self.rng.randint(200, 999)
        phone_end = self.rng.randint(1000, 9999)
        
        email_user = f"{first.lower()}.{last.lower()}"
        
        certs = self.rng.sample(CERTIFICATIONS, self.rng.randint(0, 3)) if dept in ["Security", "DevOps", "Engineering"] else []
        
        person = {
            "id": idx,
            "name": name,
            "first": first,
            "last": last,
            "age": age,
            "birthday": f"{birth_year}-{birth_month:02d}-{birth_day:02d}",
            "birth_display": f"{self._month_name(birth_month)} {birth_day}, {birth_year}",
            "city": city,
            "state": state,
            "department": dept,
            "role": role,
            "university": university,
            "degree_year": birth_year + self.rng.randint(21, 26),
            "prev_company": prev_company,
            "years_experience": years_exp,
            "start_date": f"{start_year}-{start_month:02d}-01",
            "salary": salary,
            "email": f"{email_user}@nexusdynamics.com",
            "phone": f"({phone_area}) {phone_mid}-{phone_end}",
            "slack": f"@{first.lower()}{last[0].lower()}",
            "hobby1": hobby1,
            "hobby2": hobby2,
            "allergy": allergy,
            "pet_type": pet_type if pet_type != "none" else None,
            "pet_name": pet_name,
            "partner": partner_name,
            "kids": kids,
            "certs": certs,
            "fun_fact": self._generate_fun_fact(first),
        }
        
        self.people.append(person)
        
        # Track disambiguation
        if name in self.disambiguation_groups:
            self.disambiguation_groups[name].append(idx)
        else:
            self.disambiguation_groups[name] = [idx]
        
        return person
    
    def generate_project(self, idx: int) -> dict:
        """Generate a project with timeline and team."""
        name = PROJECT_NAMES[idx % len(PROJECT_NAMES)]
        
        # Assign team from existing people
        team_size = self.rng.randint(3, 12)
        available = [p for p in self.people if p["department"] in ["Engineering", "Product", "Design", "Data Science", "QA"]]
        team = self.rng.sample(available, min(team_size, len(available)))
        lead = team[0] if team else self.people[0]
        pm = self.rng.choice([p for p in self.people if "Product" in p["role"]] or [self.people[1]])
        
        start_month = self.rng.randint(1, 12)
        start_year = self.rng.choice([2024, 2025, 2026])
        duration_months = self.rng.randint(3, 18)
        budget = self.rng.randint(200, 5000) * 1000
        
        tech = {
            "language": self.rng.choice(TECH_STACKS["languages"]),
            "database": self.rng.choice(TECH_STACKS["databases"]),
            "queue": self.rng.choice(TECH_STACKS["queues"]),
            "cloud": self.rng.choice(TECH_STACKS["clouds"]),
            "framework": self.rng.choice(TECH_STACKS["frameworks"]),
        }
        
        status = self.rng.choice(["planning", "in-progress", "on-track", "behind-schedule", "completed", "on-hold"])
        
        project = {
            "id": idx,
            "name": name,
            "codename": f"Project {name}",
            "lead": lead,
            "pm": pm,
            "team": team,
            "start": f"{start_year}-{start_month:02d}-01",
            "duration_months": duration_months,
            "budget": budget,
            "tech": tech,
            "status": status,
            "description": self._generate_project_description(name),
            "repo": f"github.com/nexus-dynamics/{name.lower()}",
        }
        
        self.projects.append(project)
        self.project_assignments[name] = [p["id"] for p in team]
        
        return project
    
    def generate_customer(self, idx: int) -> dict:
        """Generate a customer with rich profile."""
        company = CUSTOMER_COMPANIES[idx % len(CUSTOMER_COMPANIES)]
        
        arr = self.rng.randint(50, 2000) * 1000
        employees = self.rng.randint(100, 50000)
        deal_date = f"202{self.rng.randint(3, 6)}-{self.rng.randint(1, 12):02d}-{self.rng.randint(1, 28):02d}"
        contract_years = self.rng.choice([1, 2, 3])
        nps = self.rng.randint(1, 10)
        
        champion = f"{self.rng.choice(FIRST_NAMES)} {self.rng.choice(LAST_NAMES)}"
        champion_role = self.rng.choice(["VP of Engineering", "CTO", "Head of Data", "Director of Operations", "Chief Digital Officer"])
        
        customer = {
            "id": idx,
            "company": company,
            "industry": self._industry_for_company(company),
            "hq_city": self.rng.choice(CITIES),
            "employees": employees,
            "arr": arr,
            "deal_date": deal_date,
            "contract_years": contract_years,
            "plan": self.rng.choice(["Starter", "Professional", "Enterprise", "Enterprise Plus"]),
            "nps": nps,
            "champion": champion,
            "champion_role": champion_role,
            "use_case": self._use_case_for_industry(company),
            "events_per_month": self.rng.randint(1, 500) * 1_000_000,
            "risk": self.rng.choice(["low", "medium", "high"]),
        }
        
        self.customers.append(customer)
        return customer

    def generate_incident(self, idx: int) -> dict:
        """Generate an incident report."""
        severity = self.rng.choice(INCIDENT_SEVERITIES)
        
        incident_types = [
            ("database", "Database connection pool exhaustion", "Increased pool size, added connection monitoring"),
            ("network", "Network partition between regions", "Improved failover, added redundant links"),
            ("security", "Unauthorized access attempt detected", "Revoked credentials, added MFA requirement"),
            ("storage", "Disk space exhaustion on production server", "Added monitoring alerts, expanded storage"),
            ("api", "API gateway timeout under load", "Horizontal scaling, added circuit breaker"),
            ("deploy", "Failed deployment caused service degradation", "Added canary deployment, rollback automation"),
            ("dns", "DNS resolution failure", "Added secondary DNS provider"),
            ("certificate", "SSL certificate expiration", "Automated cert renewal with Let's Encrypt"),
            ("memory", "Memory leak in processing service", "Fixed object lifecycle, added heap monitoring"),
            ("kafka", "Kafka consumer lag spike", "Added partition rebalancing, increased consumers"),
        ]
        
        itype, title, resolution = self.rng.choice(incident_types)
        
        year = self.rng.choice([2024, 2025, 2026])
        month = self.rng.randint(1, 12)
        day = self.rng.randint(1, 28)
        hour = self.rng.randint(0, 23)
        minute = self.rng.randint(0, 59)
        duration = self.rng.randint(5, 480)
        
        oncall = self.rng.choice(self.people) if self.people else None
        
        incident = {
            "id": idx,
            "title": title,
            "type": itype,
            "severity": severity,
            "date": f"{year}-{month:02d}-{day:02d}",
            "time": f"{hour:02d}:{minute:02d}",
            "duration_min": duration,
            "oncall": oncall,
            "resolution": resolution,
            "customers_affected": self.rng.randint(0, 50),
            "root_cause": self._root_cause_for_type(itype),
        }
        
        self.incidents.append(incident)
        return incident
    
    def add_role_change(self, person_id: int, date: str, new_role: str):
        """Record a role change for temporal testing."""
        person = self.people[person_id]
        old_role = person["role"]
        if person_id not in self.role_history:
            self.role_history[person_id] = []
        self.role_history[person_id].append((date, old_role, new_role))
        person["role"] = new_role
    
    def add_contradiction(self, topic, old_val, new_val, old_file, new_file):
        """Record a deliberate contradiction for testing."""
        self.contradictions.append({
            "topic": topic,
            "old_value": old_val,
            "new_value": new_val,
            "old_file": old_file,
            "new_file": new_file,
        })
    
    # ── Helper methods ──────────────────────────────────────────────────
    
    def _role_fits_dept(self, role: str, dept: str) -> bool:
        """Check if role fits department (loose match)."""
        dept_l = dept.lower()
        role_l = role.lower()
        if "engineer" in role_l and dept_l in ["engineering", "devops", "qa", "security", "data science"]:
            return True
        if "product" in role_l and dept_l == "product":
            return True
        if "design" in role_l and dept_l == "design":
            return True
        if "data" in role_l and dept_l == "data science":
            return True
        if "sales" in role_l or "account" in role_l:
            return dept_l == "sales"
        if "recruit" in role_l or "hr" in role_l or "people" in role_l:
            return dept_l == "hr"
        if "financ" in role_l or "controller" in role_l or "cfo" in role_l:
            return dept_l == "finance"
        if "counsel" in role_l or "paralegal" in role_l:
            return dept_l == "legal"
        if "security" in role_l:
            return dept_l == "security"
        if "writer" in role_l or "advocate" in role_l:
            return dept_l in ["marketing", "engineering"]
        if "success" in role_l:
            return dept_l == "customer success"
        if "sre" in role_l or "platform" in role_l:
            return dept_l in ["devops", "engineering"]
        return True  # fallback
    
    def _month_name(self, m: int) -> str:
        return ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"][m - 1]
    
    def _generate_fun_fact(self, first_name: str) -> str:
        facts = [
            f"Once met a bear while hiking and calmly backed away — claims the bear was more scared",
            f"Can solve a Rubik's cube in under 90 seconds",
            f"Has visited 34 countries across 6 continents",
            f"Holds a black belt in Brazilian jiu-jitsu",
            f"Was a nationally ranked debate champion in high school",
            f"Built a working trebuchet in their backyard",
            f"Speaks three languages fluently",
            f"Once accidentally deleted a production database on their first day (and recovered it)",
            f"Competed in a hot dog eating contest and placed 7th",
            f"Has a twin sibling who works in a completely different field",
            f"Plays competitive Scrabble and has memorized all two-letter words",
            f"Ran with the bulls in Pamplona — never again",
            f"Volunteers at the local animal shelter every Saturday",
            f"Built their own electric skateboard from scratch",
            f"Can identify over 200 bird species by their calls",
            f"Was an extra in a Marvel movie (refuses to say which one)",
        ]
        return self.rng.choice(facts)
    
    def _generate_project_description(self, name: str) -> str:
        descs = {
            "Aurora": "Real-time supply chain visibility dashboard with predictive analytics",
            "Beacon": "Customer notification and alerting system overhaul",
            "Catalyst": "ML pipeline for demand forecasting using transformer models",
            "Dynamo": "API gateway modernization — migrate from monolith to microservices",
            "Eclipse": "Dark mode and accessibility compliance across all products",
            "Falcon": "High-speed data ingestion pipeline for IoT sensor data",
            "Genesis": "New customer onboarding automation platform",
            "Horizon": "Long-term strategic planning and roadmap tool",
            "Icarus": "Experimental edge computing deployment for low-latency inference",
            "Javelin": "Performance optimization sprint — target 50% latency reduction",
            "Keystone": "Core authentication and authorization system rebuild",
            "Labyrinth": "Complex workflow automation engine",
            "Meridian": "European data residency and GDPR compliance",
            "Nova": "Next-generation analytics engine with sub-second queries",
            "Olympus": "Enterprise tier features — SSO, SCIM, audit logs",
            "Phoenix": "Legacy system migration from Python 2 to Python 3",
            "Quantum": "Quantum-resistant encryption research project",
            "Raptor": "Rapid prototyping framework for internal tools",
            "Sentinel": "Security monitoring and threat detection platform",
            "Titan": "Infrastructure scaling — support 10x current load",
        }
        return descs.get(name, f"Cross-functional initiative to improve {self.rng.choice(['reliability', 'scalability', 'security', 'performance', 'user experience'])}")
    
    def _industry_for_company(self, company: str) -> str:
        mapping = {
            "Manufacturing": "Industrial / Manufacturing",
            "Tech": "Technology / Software",
            "Logistics": "Logistics / Supply Chain",
            "Healthcare": "Healthcare / Life Sciences",
            "Energy": "Energy / Utilities",
            "Retail": "Retail / E-Commerce",
            "Defense": "Defense / Aerospace",
            "Financial": "Financial Services",
            "Mining": "Mining / Natural Resources",
            "Shipping": "Maritime / Shipping",
            "Foods": "Food & Beverage",
            "Pharma": "Pharmaceuticals",
            "Aerospace": "Aerospace / Defense",
            "Construction": "Construction / Infrastructure",
            "Electronics": "Electronics / Hardware",
            "Maritime": "Maritime / Shipping",
            "Automotive": "Automotive",
            "Media": "Media / Entertainment",
            "Agriculture": "Agriculture",
            "Telecom": "Telecommunications",
            "Freight": "Freight / Logistics",
            "Textiles": "Textiles / Apparel",
            "Hotels": "Hospitality",
            "Security": "Cybersecurity",
            "Consulting": "Management Consulting",
        }
        for key, val in mapping.items():
            if key in company:
                return val
        return "Technology"
    
    def _use_case_for_industry(self, company: str) -> str:
        cases = [
            "Real-time supply chain visibility across 50+ distribution centers",
            "Predictive maintenance using IoT sensor data from manufacturing lines",
            "Demand forecasting for seasonal inventory planning",
            "Supplier risk monitoring and automated alerting",
            "Logistics route optimization reducing delivery times by 23%",
            "Warehouse automation and inventory tracking",
            "Cold chain monitoring for perishable goods",
            "Fleet management and driver performance analytics",
            "Raw material procurement optimization",
            "Cross-border shipping compliance automation",
        ]
        return self.rng.choice(cases)
    
    def _root_cause_for_type(self, itype: str) -> str:
        causes = {
            "database": "Connection pool configured too small for peak load. Connections not properly released after timeout.",
            "network": "BGP route leak from upstream provider caused traffic misrouting between availability zones.",
            "security": "Former employee credentials not revoked during offboarding. No automated key expiry policy.",
            "storage": "Log rotation misconfigured — debug logs accumulating without cleanup. No disk space alerts below 90%.",
            "api": "Single-threaded request handler couldn't scale with traffic spike. No circuit breaker pattern implemented.",
            "deploy": "Integration tests passed but canary health check had too-generous thresholds. Bad config merged.",
            "dns": "TTL set too high (24h). When primary DNS went down, cached records kept serving stale data.",
            "certificate": "Cert renewal cron job silently failing for 3 weeks. No monitoring on cert expiry date.",
            "memory": "Event listener not being unregistered on object cleanup. Gradual heap growth over 72 hours.",
            "kafka": "Consumer group rebalancing triggered by network blip. Offset commit race condition during rebalance.",
        }
        return causes.get(itype, "Root cause under investigation.")


# ============================================================================
# FILE GENERATORS
# ============================================================================

class CorpusGenerator:
    """Generates the complete workspace corpus."""
    
    def __init__(self, scale: str, output_dir: Path, seed: int = 42):
        self.scale = scale
        self.output = output_dir
        self.world = WorldState(seed)
        self.files_written = 0
        
        self.scale_config = {
            "small":  {"people": 30,  "projects": 8,  "customers": 15,  "incidents": 20,  "daily_notes_days": 60,   "meetings": 30},
            "medium": {"people": 100, "projects": 25, "customers": 50,  "incidents": 60,  "daily_notes_days": 365,  "meetings": 150},
            "large":  {"people": 250, "projects": 50, "customers": 100, "incidents": 150, "daily_notes_days": 730,  "meetings": 500},
            "stress": {"people": 500, "projects": 80, "customers": 200, "incidents": 300, "daily_notes_days": 1095, "meetings": 1000},
        }[scale]
    
    def generate(self) -> dict:
        """Generate complete corpus. Returns metadata."""
        print(f"Generating {self.scale} corpus...")
        
        # Order matters — people first, then things that reference people
        self._generate_company()
        self._generate_people()
        self._generate_disambiguation_people()
        self._generate_projects()
        self._generate_customers()
        self._generate_incidents()
        self._generate_daily_notes()
        self._generate_meetings()
        self._generate_infrastructure()
        self._generate_policies()
        self._generate_creative()
        self._generate_archive()  # Old versions for contradiction testing
        
        # Save world state for query generation
        meta = {
            "scale": self.scale,
            "files": self.files_written,
            "people": len(self.world.people),
            "projects": len(self.world.projects),
            "customers": len(self.world.customers),
            "incidents": len(self.world.incidents),
            "contradictions": len(self.world.contradictions),
            "disambiguation_groups": {k: v for k, v in self.world.disambiguation_groups.items() if len(v) > 1},
            "role_changes": len(self.world.role_history),
        }
        
        # Save world state
        with open(self.output / "world_state.json", "w") as f:
            json.dump({
                "people": self.world.people,
                "projects": [{k: v for k, v in p.items() if k not in ("team", "lead", "pm")} for p in self.world.projects],
                "customers": self.world.customers,
                "incidents": [{k: v for k, v in i.items() if k != "oncall"} for i in self.world.incidents],
                "contradictions": self.world.contradictions,
                "role_history": {str(k): v for k, v in self.world.role_history.items()},
                "disambiguation": {k: v for k, v in self.world.disambiguation_groups.items() if len(v) > 1},
            }, f, indent=2, default=str)
        
        print(f"\nCorpus generated: {self.files_written} files")
        print(f"  People: {len(self.world.people)}")
        print(f"  Projects: {len(self.world.projects)}")
        print(f"  Customers: {len(self.world.customers)}")
        print(f"  Incidents: {len(self.world.incidents)}")
        print(f"  Contradictions: {len(self.world.contradictions)}")
        print(f"  Disambiguation groups: {len(meta['disambiguation_groups'])}")
        
        return meta
    
    def _write(self, rel_path: str, content: str):
        """Write a file and increment counter."""
        full = self.output / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content.strip() + "\n")
        self.files_written += 1
    
    def _generate_company(self):
        """Generate company-level docs."""
        c = COMPANY
        self._write("company/about.md", f"""# {c['name']} — Company Overview

## Founded
- Date: {c['founded']}
- Founders: {' and '.join(c['founders'])}
- Incorporated in: {c['state_inc']}
- HQ: {c['hq']}
- EIN: {c['ein']}

## Mission
{c['mission']}

## Industry
{c['industry']}

## Funding
- Seed: $3.2M (2020) — Led by Founders Fund
- Series A: $22M (2022) — Led by Benchmark
- Series B: $78M (2024) — Led by Sequoia Capital
- Series C: $180M (2025) — Led by Coatue Management
- Total raised: $283.2M
- Current valuation: $1.4B (post-Series C, unicorn status achieved Oct 2025)

## Key Metrics (Q4 2025)
- ARR: $67.3M
- Customer count: 487
- Net revenue retention: 142%
- Gross margin: 81%
- Employees: {self.scale_config['people'] + 30} (as of March 2026)
""")
    
    def _generate_people(self):
        """Generate person profiles."""
        n = self.scale_config["people"]
        print(f"  Generating {n} people...")
        
        for i in range(n):
            p = self.world.generate_person(i)
            
            content = f"# {p['name']} — {p['role']}\n\n"
            content += f"## Background\n"
            content += f"{p['name']} joined {COMPANY['name']} on {p['start_date']}. "
            content += f"Previously at {p['prev_company']} for {self.world.rng.randint(2, 8)} years. "
            content += f"Holds a degree from {p['university']} ({p['degree_year']}).\n"
            content += f"{p['years_experience']} years of total experience in the field.\n\n"
            
            content += f"## Personal\n"
            content += f"- Age: {p['age']}\n"
            content += f"- Birthday: {p['birth_display']}\n"
            content += f"- Lives in: {p['city']}, {p['state']}\n"
            
            if p['partner']:
                content += f"- Partner: {p['partner']}\n"
            if p['kids']:
                kids_str = ", ".join(f"{k['name']} (age {k['age']})" for k in p['kids'])
                content += f"- Children: {kids_str}\n"
            if p['pet_type']:
                content += f"- Pet: {p['pet_type'].title()} named {p['pet_name']}\n"
            if p['allergy']:
                content += f"- Allergy: {p['allergy'].title()}\n"
            
            content += f"- Hobbies: {p['hobby1']}, {p['hobby2']}\n"
            content += f"- Fun fact: {p['fun_fact']}\n\n"
            
            content += f"## Work\n"
            content += f"- Department: {p['department']}\n"
            content += f"- Role: {p['role']}\n"
            content += f"- Compensation: ${p['salary']:,}/year\n"
            if p['certs']:
                content += f"- Certifications: {', '.join(p['certs'])}\n"
            content += f"\n"
            
            content += f"## Contact\n"
            content += f"- Email: {p['email']}\n"
            content += f"- Phone: {p['phone']}\n"
            content += f"- Slack: {p['slack']}\n"
            
            filename = f"{p['first'].lower()}-{p['last'].lower()}"
            self._write(f"team/{filename}.md", content)
    
    def _generate_disambiguation_people(self):
        """Generate duplicate-name people for disambiguation testing."""
        # Create 5-10 pairs of people with the same first+last name but different departments
        num_dupes = min(10, self.scale_config["people"] // 10)
        
        for i in range(num_dupes):
            # Pick an existing person and create someone with the same name
            original = self.world.people[i]
            name = original["name"]
            
            # Generate with same name but different details
            dupe = self.world.generate_person(len(self.world.people), force_name=name)
            
            # Make sure they're in a different department
            other_depts = [d for d in DEPARTMENTS if d != original["department"]]
            dupe["department"] = self.world.rng.choice(other_depts)
            dupe["role"] = self.world.rng.choice(ROLES)
            dupe["city"], dupe["state"] = self.world.rng.choice([c for c in CITIES if c[0] != original["city"]])
            
            content = f"# {dupe['name']} — {dupe['role']}\n\n"
            content += f"## Background\n"
            content += f"Not to be confused with {name} in {original['department']}.\n"
            content += f"{dupe['name']} works in {dupe['department']} and joined in {dupe['start_date']}.\n"
            content += f"Previously at {dupe['prev_company']}.\n\n"
            content += f"## Personal\n"
            content += f"- Age: {dupe['age']}\n"
            content += f"- Lives in: {dupe['city']}, {dupe['state']}\n"
            content += f"- Department: {dupe['department']}\n"
            content += f"- Role: {dupe['role']}\n"
            content += f"- Email: {dupe['email']}\n"
            
            filename = f"{dupe['first'].lower()}-{dupe['last'].lower()}-{dupe['department'].lower()}"
            self._write(f"team/{filename}.md", content)
    
    def _generate_projects(self):
        """Generate project docs."""
        n = self.scale_config["projects"]
        print(f"  Generating {n} projects...")
        
        for i in range(n):
            p = self.world.generate_project(i)
            
            content = f"# {p['codename']} — {p['description']}\n\n"
            content += f"## Overview\n"
            content += f"- Status: {p['status']}\n"
            content += f"- Start date: {p['start']}\n"
            content += f"- Duration: {p['duration_months']} months\n"
            content += f"- Budget: ${p['budget']:,}\n"
            content += f"- Repository: {p['repo']}\n\n"
            
            content += f"## Team\n"
            content += f"- Tech Lead: {p['lead']['name']}\n"
            content += f"- Product Manager: {p['pm']['name']}\n"
            content += f"- Engineers: {', '.join(m['name'] for m in p['team'][1:min(6, len(p['team']))])}\n\n"
            
            content += f"## Tech Stack\n"
            for k, v in p['tech'].items():
                content += f"- {k.title()}: {v}\n"
            
            self._write(f"projects/{p['name'].lower()}.md", content)
    
    def _generate_customers(self):
        """Generate customer profiles."""
        n = self.scale_config["customers"]
        print(f"  Generating {n} customers...")
        
        for i in range(n):
            c = self.world.generate_customer(i)
            
            content = f"# {c['company']} — Customer Profile\n\n"
            content += f"## Account Details\n"
            content += f"- Company: {c['company']}\n"
            content += f"- Industry: {c['industry']}\n"
            content += f"- HQ: {c['hq_city'][0]}, {c['hq_city'][1]}\n"
            content += f"- Employees: {c['employees']:,}\n"
            content += f"- ARR: ${c['arr']:,}\n"
            content += f"- Contract signed: {c['deal_date']}\n"
            content += f"- Contract term: {c['contract_years']} year{'s' if c['contract_years'] > 1 else ''}\n"
            content += f"- Plan: {c['plan']}\n"
            content += f"- NPS: {c['nps']}\n"
            content += f"- Risk level: {c['risk']}\n\n"
            content += f"## Key Contact\n"
            content += f"- Champion: {c['champion']}, {c['champion_role']}\n\n"
            content += f"## Use Case\n"
            content += f"{c['use_case']}\n"
            content += f"Processing approximately {c['events_per_month']:,} events per month.\n"
            
            filename = c['company'].lower().replace(' ', '-').replace("'", "")
            self._write(f"customers/{filename}.md", content)
    
    def _generate_incidents(self):
        """Generate incident reports."""
        n = self.scale_config["incidents"]
        print(f"  Generating {n} incidents...")
        
        for i in range(n):
            inc = self.world.generate_incident(i)
            
            content = f"# Incident Report: {inc['title']}\n\n"
            content += f"## Summary\n"
            content += f"- **Date**: {inc['date']} at {inc['time']}\n"
            content += f"- **Severity**: {inc['severity']}\n"
            content += f"- **Duration**: {inc['duration_min']} minutes\n"
            content += f"- **Customers affected**: {inc['customers_affected']}\n\n"
            
            if inc['oncall']:
                content += f"## Response\n"
                content += f"On-call: {inc['oncall']['name']} ({inc['oncall']['role']})\n\n"
            
            content += f"## Root Cause\n"
            content += f"{inc['root_cause']}\n\n"
            content += f"## Resolution\n"
            content += f"{inc['resolution']}\n"
            
            self._write(f"incidents/{inc['date']}-{inc['type']}-{i}.md", content)
    
    def _generate_daily_notes(self):
        """Generate daily notes over the time span."""
        days = self.scale_config["daily_notes_days"]
        print(f"  Generating {days} days of notes...")
        
        start = datetime(2024, 1, 1)
        
        for d in range(days):
            date = start + timedelta(days=d)
            if date.weekday() >= 5:  # Skip weekends sometimes
                if self.world.rng.random() > 0.1:
                    continue
            
            date_str = date.strftime("%Y-%m-%d")
            
            # Pick 2-4 random people to mention
            mentioned = self.world.rng.sample(self.world.people, min(4, len(self.world.people)))
            
            # Pick a project or two
            projs = self.world.rng.sample(self.world.projects, min(2, len(self.world.projects))) if self.world.projects else []
            
            content = f"# Daily Notes — {date_str}\n\n"
            content += f"## Morning\n"
            content += f"- Worked on {projs[0]['name'] if projs else 'general tasks'}\n"
            content += f"- {mentioned[0]['name']} presented {self.world.rng.choice(['sprint progress', 'design review', 'architecture proposal', 'demo', 'quarterly metrics'])}\n"
            
            if len(mentioned) > 1:
                content += f"- Quick sync with {mentioned[1]['name']} about {self.world.rng.choice(['deployment', 'customer feedback', 'hiring', 'budget', 'tech debt', 'performance issues'])}\n"
            
            content += f"\n## Afternoon\n"
            if projs:
                content += f"- {projs[0]['name']} update: {self.world.rng.choice(['on track', 'slight delay', 'ahead of schedule', 'blocked on dependency', 'code review needed'])}\n"
            
            if len(mentioned) > 2:
                content += f"- {mentioned[2]['name']} flagged {self.world.rng.choice(['a bug in production', 'a customer escalation', 'a security concern', 'a performance regression', 'a hiring need'])}\n"
            
            if self.world.rng.random() > 0.7 and len(mentioned) > 3:
                content += f"\n## Personal\n"
                content += f"- {mentioned[3]['name']} {self.world.rng.choice(['brought cookies for the team', 'announced they are expecting a baby', 'got a new puppy', 'won an internal hackathon', 'celebrated their work anniversary'])}\n"
            
            self._write(f"memory/{date_str}.md", content)
    
    def _generate_meetings(self):
        """Generate meeting notes."""
        n = self.scale_config["meetings"]
        print(f"  Generating {n} meetings...")
        
        meeting_types = [
            "Leadership Sync", "Engineering Standup", "Product Review",
            "Design Critique", "Security Review", "Sprint Planning",
            "Sprint Retrospective", "All Hands", "Board Meeting",
            "Customer Review", "Architecture Review", "Incident Postmortem",
            "Budget Review", "Hiring Committee", "1:1",
        ]
        
        start = datetime(2024, 1, 1)
        
        for i in range(n):
            date = start + timedelta(days=self.world.rng.randint(0, self.scale_config["daily_notes_days"]))
            mtype = self.world.rng.choice(meeting_types)
            attendees = self.world.rng.sample(self.world.people, min(self.world.rng.randint(3, 8), len(self.world.people)))
            
            content = f"# {mtype} — {date.strftime('%Y-%m-%d')}\n\n"
            content += f"## Attendees\n"
            content += ", ".join(a['name'] for a in attendees) + "\n\n"
            
            content += f"## Discussion\n"
            
            # Generate 2-4 discussion points
            for j in range(self.world.rng.randint(2, 4)):
                speaker = self.world.rng.choice(attendees)
                topic = self.world.rng.choice([
                    f"{self.world.rng.choice(self.world.projects)['name'] if self.world.projects else 'the project'} progress update",
                    "hiring pipeline review",
                    "customer feedback discussion",
                    "technical debt prioritization",
                    "Q1 OKR review",
                    "security audit results",
                    "infrastructure cost optimization",
                    "product roadmap alignment",
                    "competitor analysis",
                    "team velocity metrics",
                ])
                content += f"\n### {j + 1}. {topic.title()} ({speaker['name']})\n"
                content += f"- {self.world.rng.choice(['Presented data showing', 'Discussed concerns about', 'Proposed changes to', 'Shared update on', 'Raised question about'])} {topic}\n"
                content += f"- {self.world.rng.choice(['Action item', 'Decision', 'Follow-up', 'Agreed to', 'Tabled for next meeting'])}: {self.world.rng.choice(['review by end of week', 'schedule deep-dive session', 'create RFC document', 'update the roadmap', 'assign owner for follow-up'])}\n"
            
            self._write(f"meetings/{date.strftime('%Y-%m-%d')}-{mtype.lower().replace(' ', '-')}-{i}.md", content)
    
    def _generate_infrastructure(self):
        """Generate infra docs with credentials and configs."""
        print("  Generating infrastructure docs...")
        
        # Production environment
        self._write("infrastructure/production.md", f"""# Production Environment

## Architecture
Multi-region deployment across AWS us-west-2, us-east-1, and eu-west-1.
Active-active with CockroachDB for cross-region consistency.

## Servers
- API Gateway: api.nexusdynamics.com (CloudFront → ALB → ECS Fargate)
- Primary DB: cockroach-prod-1.internal (r6g.8xlarge, 256GB RAM, 4TB NVMe)
- Replica DB: cockroach-prod-2.internal (r6g.4xlarge, 128GB RAM, 2TB NVMe)
- Cache: Redis cluster — cache.nexusdynamics.internal (r6g.2xlarge, 5 nodes)
- Search: Elasticsearch — es-prod.internal (m6g.4xlarge, 9-node cluster)
- Queue: Kafka — kafka-prod.internal (m6g.2xlarge, 7-broker cluster)
- ML Inference: ml-prod.internal (g5.4xlarge, 4 GPU nodes)

## Credentials
- AWS Account ID: 729481035267
- Datadog API Key: dd-api-7x9k2m4p8q
- PagerDuty Service Key: pd-svc-3f8k9m2x
- Sentry DSN: https://xyz789@sentry.io/5908234
- GitHub Bot Token: ghp_Nx7k2m9pQ4rW8tY1
- Terraform Cloud Token: tc-org-nexus-8x2k4m

## SLA Targets
- API availability: 99.99%
- P99 latency: < 150ms
- Data durability: 99.999999999%
- RPO: 0 (synchronous replication)
- RTO: 2 minutes
""")
        
        # Multiple server configs for precision testing
        regions = [
            ("us-west-2", "10.1.0.0/16", "Oregon"),
            ("us-east-1", "10.2.0.0/16", "Virginia"),
            ("eu-west-1", "10.3.0.0/16", "Ireland"),
        ]
        
        for region, cidr, location in regions:
            servers = []
            for j in range(self.world.rng.randint(5, 15)):
                name = f"srv-{region}-{j+1:03d}"
                ip = f"{cidr.split('.')[0]}.{cidr.split('.')[1]}.{self.world.rng.randint(1, 254)}.{self.world.rng.randint(1, 254)}"
                role = self.world.rng.choice(["api", "worker", "scheduler", "cache", "db-replica", "monitoring"])
                self.world.ip_registry[name] = ip
                servers.append({"name": name, "ip": ip, "role": role})
            
            content = f"# {location} Region ({region}) — Server Inventory\n\n"
            for s in servers:
                content += f"## {s['name']}\n"
                content += f"- IP: {s['ip']}\n"
                content += f"- Role: {s['role']}\n"
                content += f"- SSH: ssh admin@{s['ip']} -p 2222\n\n"
            
            self._write(f"infrastructure/servers-{region}.md", content)
    
    def _generate_policies(self):
        """Generate HR/company policies."""
        print("  Generating policies...")
        
        self._write("company/benefits.md", """# Employee Benefits — Nexus Dynamics

## Health Insurance
- Provider: United Healthcare PPO
- Company pays 95% of premiums for employees, 80% for dependents
- Dental: MetLife
- Vision: EyeMed
- Mental health: Spring Health (unlimited sessions)
- FSA: Up to $3,050/year

## Time Off
- Unlimited PTO (minimum 20 days encouraged)
- 13 company holidays
- 20 weeks paid parental leave (all parents)
- 6-week paid sabbatical after 4 years

## Financial
- 401(k): 6% match via Vanguard
- Employee stock options: 4-year vest, 1-year cliff
- Annual bonus: 15-25% of base salary (target)
- Equipment budget: $5,000 for home office setup
- $200/month learning stipend

## Perks
- $75/month wellness stipend
- Free lunch daily (Boulder office)
- Dog-friendly office
- Annual retreat (2025: Tulum, Mexico)
- Commuter benefits: $300/month
""")
        
        self._write("company/values.md", """# Nexus Dynamics — Core Values

## 1. Ship It
We bias toward action. Perfect is the enemy of done. Ship early, iterate fast, learn from users.

## 2. Own the Outcome
Don't just complete tasks — own results. If something's broken, fix it. If something's unclear, clarify it. Don't wait to be asked.

## 3. Radical Candor
Be honest and direct. Give feedback early and often. Disagree openly in meetings, commit fully after decisions.

## 4. Customer Obsession
Every decision starts with "how does this help our customers?" If you can't answer that, question the work.

## 5. Build for Scale
Think 10x ahead. Today's hack is tomorrow's tech debt. Invest in foundations that compound.
""")
    
    def _generate_creative(self):
        """Generate fiction and personal content for diversity."""
        print("  Generating creative content...")
        
        self._write("creative/the-signal.md", """# The Signal — A Short Story

## Part 1: Static

Dr. Yara Osei had been monitoring the deep space array for eleven years when she first heard it. Not the usual cosmic background radiation. Not a pulsar. Something structured. Something deliberate.

The signal repeated every 73.6 seconds — a prime number, which made her heart race. Natural phenomena don't use primes.

"Run it through the pattern matcher again," she told her assistant, Callum Reed. He was young, barely out of his postdoc, but he had the best ears in the lab.

"I've run it seventeen times, Dr. Osei. It's not noise. It's a 1,247-bit sequence that repeats with zero drift. Zero. Even our atomic clock has drift."

Yara stared at the waveform on her screen. Thirty years of SETI research, and she'd always believed they'd find something eventually. She just never expected it to come from the direction of Proxima Centauri, 4.24 light-years away. Which meant the signal was sent 4.24 years ago. Which meant...

"They know we're here," she whispered. "They've been listening to our radio leakage for decades and they just... answered."

## Part 2: Protocol

The First Contact Protocol, written in 1989 and updated seventeen times since, was maddeningly specific about some things and uselessly vague about others. Step 1: Verify independently. Step 2: Do not respond. Step 3: Notify the UN Secretary-General.

Yara did Step 1. She called Dr. Kenzo Fujita at the Nobeyama Radio Observatory in Japan. He found it within minutes. So did Dr. Ingrid Holm at the LOFAR array in the Netherlands.

Step 2 was harder than she expected. The signal was so clearly a greeting — a mathematical handshake, primes followed by the first 20 digits of pi, followed by what looked like a simple vocabulary builder. Like someone had read "Contact" and decided Sagan was basically right.

She wanted to say hello back. Every cell in her body wanted to say hello back.

She did Step 3 instead.

## Part 3: The Message

It took fourteen months for the world's best cryptographers, linguists, and mathematicians to decode the full message. When they did, the room went silent.

The message wasn't a greeting. It was a warning.

"We heard your signals. We have been where you are. The filter approaches. You have approximately 200 years. Here is what we learned. Here is what we wish someone had told us."

What followed was 847 pages of compressed data that, when decoded, contained something remarkable: a complete blueprint for atmospheric carbon capture at planetary scale, fusion reactor designs that made ITER look like a campfire, and a biological framework for extending human lifespan to approximately 400 years.

The last line of the message read: "We lost 6 of our 8 billion. The technology works. The politics is your problem. Good luck."

Yara read it three times. Then she cried.

Not because it was sad. Because for the first time in human history, someone had told the truth about the future and also given them the tools to survive it.

The politics, she knew, would be the hard part.
""")
    
    def _generate_archive(self):
        """Generate archived/old versions of docs for contradiction testing."""
        print("  Generating archive (contradiction data)...")
        
        # Server IP that changed
        self._write("archive/production-2024.md", """# Production Environment (ARCHIVED — January 2024)

**⚠️ This document is outdated. See infrastructure/production.md for current info.**

## Servers
- Primary DB: cockroach-prod-1.internal (r5.4xlarge, 128GB RAM, 2TB EBS)
- Cache: Redis — cache.nexusdynamics.internal (r5.xlarge, 3 nodes)

## Credentials
- AWS Account ID: 729481035267
- Datadog API Key: dd-api-OLD-3x7k9m2p
- PagerDuty Service Key: pd-svc-OLD-2f7k8m

## SLA Targets
- API availability: 99.9% (upgraded to 99.99% in 2025)
- P99 latency: < 500ms (improved to < 150ms)
""")
        
        self.world.add_contradiction(
            "Datadog API Key", "dd-api-OLD-3x7k9m2p", "dd-api-7x9k2m4p8q",
            "archive/production-2024.md", "infrastructure/production.md"
        )
        self.world.add_contradiction(
            "API availability SLA", "99.9%", "99.99%",
            "archive/production-2024.md", "infrastructure/production.md"
        )
        self.world.add_contradiction(
            "P99 latency target", "500ms", "150ms",
            "archive/production-2024.md", "infrastructure/production.md"
        )
        self.world.add_contradiction(
            "Primary DB instance type", "r5.4xlarge", "r6g.8xlarge",
            "archive/production-2024.md", "infrastructure/production.md"
        )
        self.world.add_contradiction(
            "Redis cache nodes", "3 nodes", "5 nodes",
            "archive/production-2024.md", "infrastructure/production.md"
        )
        
        # Benefits that changed
        self._write("archive/benefits-2023.md", """# Employee Benefits (ARCHIVED — 2023)

**⚠️ This document is outdated. See company/benefits.md for current info.**

## Health Insurance
- Provider: Cigna PPO (switched to United Healthcare in 2024)
- Company pays 80% of premiums (increased to 95% in 2024)

## Time Off
- 20 days PTO (switched to unlimited in 2024)
- 12 weeks parental leave (increased to 20 weeks in 2024)

## Financial
- 401(k): 4% match (increased to 6% in 2025)
- Equipment budget: $2,500 (increased to $5,000 in 2025)
""")
        
        self.world.add_contradiction(
            "Health insurance provider", "Cigna", "United Healthcare",
            "archive/benefits-2023.md", "company/benefits.md"
        )
        self.world.add_contradiction(
            "401k match", "4%", "6%",
            "archive/benefits-2023.md", "company/benefits.md"
        )
        self.world.add_contradiction(
            "Parental leave", "12 weeks", "20 weeks",
            "archive/benefits-2023.md", "company/benefits.md"
        )
        
        # Role changes
        if len(self.world.people) >= 5:
            # Pick some people to have role changes
            for i in range(min(8, len(self.world.people) // 5)):
                p = self.world.people[i]
                old_role = p["role"]
                new_role = self.world.rng.choice([r for r in ROLES if r != old_role])
                change_date = f"2025-{self.world.rng.randint(1, 12):02d}-01"
                
                self.world.add_role_change(i, change_date, new_role)
                
                self._write(f"archive/role-change-{p['first'].lower()}-{p['last'].lower()}.md", 
                    f"# Role Change: {p['name']}\n\n"
                    f"- **Date**: {change_date}\n"
                    f"- **Previous role**: {old_role}\n"
                    f"- **New role**: {new_role}\n"
                    f"- **Department**: {p['department']}\n"
                    f"- **Reason**: {self.world.rng.choice(['promotion', 'team restructuring', 'lateral move', 'new initiative'])}\n"
                )
                
                self.world.add_contradiction(
                    f"{p['name']} role", old_role, new_role,
                    f"archive/role-change-{p['first'].lower()}-{p['last'].lower()}.md",
                    f"team/{p['first'].lower()}-{p['last'].lower()}.md"
                )


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate IRONMAN benchmark corpus")
    parser.add_argument("--scale", choices=["small", "medium", "large", "stress"],
                        default="medium", help="Corpus scale")
    parser.add_argument("--output", default="./corpus", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    output = Path(args.output)
    if output.exists():
        print(f"Output directory {output} already exists. Remove it first.")
        return 1
    
    output.mkdir(parents=True)
    
    gen = CorpusGenerator(args.scale, output, args.seed)
    meta = gen.generate()
    
    print(f"\nCorpus saved to: {output}")
    print(f"World state saved to: {output}/world_state.json")
    
    return 0


if __name__ == "__main__":
    exit(main())
