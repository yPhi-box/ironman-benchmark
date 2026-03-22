#!/usr/bin/env python3
"""
IRONMAN Query Generator
Generates brutally hard ground-truth queries from the corpus world state.
Each query has: query text, expected answer, category, difficulty, and source file.

Usage:
    python3 generate_queries.py --corpus ./corpus --output ./queries.json
"""
import json
import random
import argparse
from pathlib import Path
from typing import List, Dict


class QueryGenerator:
    """Generates ground-truth queries from world state."""
    
    def __init__(self, world_state: dict, seed: int = 42):
        self.world = world_state
        self.people = world_state["people"]
        self.projects = world_state.get("projects", [])
        self.customers = world_state.get("customers", [])
        self.incidents = world_state.get("incidents", [])
        self.contradictions = world_state.get("contradictions", [])
        self.role_history = world_state.get("role_history", {})
        self.disambiguation = world_state.get("disambiguation", {})
        self.rng = random.Random(seed)
        self.queries = []
    
    def generate_all(self) -> List[Dict]:
        """Generate all query categories."""
        self._needle_queries()
        self._temporal_queries()
        self._contradiction_queries()
        self._multihop_queries()
        self._disambiguation_queries()
        self._fragmentation_queries()
        self._synonym_queries()
        self._adversarial_queries()
        self._precision_queries()
        self._quantitative_queries()
        self._negative_queries()
        self._implicit_queries()
        self._long_range_queries()
        self._recency_queries()
        self._robustness_queries()
        self._cross_document_queries()
        self._personal_detail_queries()
        self._credential_queries()
        
        self.rng.shuffle(self.queries)
        
        # Add IDs
        for i, q in enumerate(self.queries):
            q["id"] = i + 1
        
        return self.queries
    
    def _add(self, query: str, expect: str, category: str, difficulty: str,
             source_hint: str = "", notes: str = "", expect_absent: bool = False):
        """Add a query to the set."""
        self.queries.append({
            "query": query,
            "expect": expect,
            "category": category,
            "difficulty": difficulty,
            "source_hint": source_hint,
            "notes": notes,
            "expect_absent": expect_absent,
        })
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 1: NEEDLE — Find one fact in a massive corpus
    # ════════════════════════════════════════════════════════════════════
    def _needle_queries(self):
        """Specific facts that require finding one chunk among thousands."""
        for p in self.rng.sample(self.people, min(30, len(self.people))):
            # Deep personal details that are unique to one person
            if p.get("allergy"):
                self._add(
                    f"What is {p['name']} allergic to?",
                    p["allergy"],
                    "needle", "medium",
                    f"team/{p['first'].lower()}-{p['last'].lower()}.md",
                )
            
            if p.get("pet_name"):
                self._add(
                    f"What is the name of {p['name']}'s {p['pet_type']}?",
                    p["pet_name"],
                    "needle", "hard",
                    f"team/{p['first'].lower()}-{p['last'].lower()}.md",
                )
            
            self._add(
                f"{p['name']}'s phone number",
                p["phone"],
                "needle", "medium",
                f"team/{p['first'].lower()}-{p['last'].lower()}.md",
            )
            
            self._add(
                f"What university did {p['name']} attend?",
                p["university"],
                "needle", "medium",
                f"team/{p['first'].lower()}-{p['last'].lower()}.md",
            )
        
        # Credential needles — find one key in sea of configs
        self._add(
            "What is the Datadog API key?",
            "dd-api-7x9k2m4p8q",
            "needle", "hard",
            "infrastructure/production.md",
            "Must find current key, not archived one",
        )
        
        self._add(
            "GitHub bot token",
            "ghp_Nx7k2m9pQ4rW8tY1",
            "needle", "hard",
            "infrastructure/production.md",
        )
        
        self._add(
            "Terraform Cloud token",
            "tc-org-nexus-8x2k4m",
            "needle", "hard",
            "infrastructure/production.md",
        )
        
        # Customer-specific needles
        for c in self.rng.sample(self.customers, min(15, len(self.customers))):
            self._add(
                f"What is {c['company']}'s ARR?",
                f"${c['arr']:,}",
                "needle", "medium",
                f"customers/",
            )
            
            self._add(
                f"Who is the champion at {c['company']}?",
                c["champion"],
                "needle", "medium",
                f"customers/",
            )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 2: TEMPORAL — Time-aware reasoning
    # ════════════════════════════════════════════════════════════════════
    def _temporal_queries(self):
        """Queries that require understanding time and change."""
        for pid_str, changes in self.role_history.items():
            pid = int(pid_str)
            if pid < len(self.people):
                p = self.people[pid]
                for date, old_role, new_role in changes:
                    # What was their role BEFORE the change?
                    self._add(
                        f"What was {p['name']}'s role before {date}?",
                        old_role,
                        "temporal", "hard",
                        f"archive/role-change-{p['first'].lower()}-{p['last'].lower()}.md",
                        "Must understand temporal ordering",
                    )
                    
                    # What is their CURRENT role?
                    self._add(
                        f"What is {p['name']}'s current role?",
                        new_role,
                        "temporal", "hard",
                        f"team/{p['first'].lower()}-{p['last'].lower()}.md",
                        "Must prefer current over archived data",
                    )
        
        # Incident timeline queries
        for inc in self.rng.sample(self.incidents, min(10, len(self.incidents))):
            self._add(
                f"What incident happened on {inc['date']}?",
                inc["title"],
                "temporal", "medium",
                f"incidents/",
            )
        
        # Benefits timeline
        self._add(
            "When did the company switch to unlimited PTO?",
            "2024",
            "temporal", "hard",
            "archive/benefits-2023.md",
            "Must connect old PTO policy to new unlimited policy",
        )
        
        self._add(
            "What was the parental leave policy in 2023?",
            "12 weeks",
            "temporal", "hard",
            "archive/benefits-2023.md",
        )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 3: CONTRADICTION — Conflicting info, must pick current
    # ════════════════════════════════════════════════════════════════════
    def _contradiction_queries(self):
        """Test ability to identify and prefer current information."""
        for c in self.contradictions:
            # Direct query — should return NEW value
            self._add(
                f"What is the current {c['topic']}?",
                c["new_value"],
                "contradiction", "brutal",
                c["new_file"],
                f"Old value '{c['old_value']}' exists in {c['old_file']}. Must return '{c['new_value']}'.",
            )
            
            # Tricky: what CHANGED?
            self._add(
                f"What did the {c['topic']} change from?",
                c["old_value"],
                "contradiction", "brutal",
                c["old_file"],
                f"Must find the OLD value, not the current one.",
            )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 4: MULTI-HOP — Chain facts across files
    # ════════════════════════════════════════════════════════════════════
    def _multihop_queries(self):
        """Queries requiring 2-4 hops across different files."""
        # Project lead → person details (2 hops: project file → person file)
        for proj in self.rng.sample(self.projects, min(15, len(self.projects))):
            lead_id = proj.get("lead")
            if lead_id and isinstance(lead_id, int) and lead_id < len(self.people):
                lead = self.people[lead_id]
            elif isinstance(lead_id, dict):
                lead = lead_id
            else:
                continue
            
            self._add(
                f"Where does the tech lead of Project {proj['name']} live?",
                lead.get("city", "unknown"),
                "multi_hop", "hard",
                f"projects/{proj['name'].lower()}.md → team/",
                "Requires: find project → find lead name → find lead's city",
            )
            
            if lead.get("university"):
                self._add(
                    f"What university did the leader of Project {proj['name']} attend?",
                    lead["university"],
                    "multi_hop", "hard",
                    f"projects/{proj['name'].lower()}.md → team/",
                    "Requires: find project → find lead → find education",
                )
            
            if lead.get("partner"):
                self._add(
                    f"What is the name of the spouse/partner of the person leading Project {proj['name']}?",
                    lead["partner"],
                    "multi_hop", "brutal",
                    f"projects/{proj['name'].lower()}.md → team/",
                    "3 hops: project → lead name → lead file → partner",
                )
        
        # Customer → champion → (if champion matches a team member, find details)
        # These are genuinely hard because the champion might not be in the team/ directory
        for c in self.rng.sample(self.customers, min(5, len(self.customers))):
            self._add(
                f"What is the use case for the customer whose champion is {c['champion']}?",
                c["use_case"][:30],
                "multi_hop", "hard",
                f"customers/",
                "Requires: find champion name → find customer → find use case",
            )
        
        # Incident → on-call person → their department
        for inc in self.rng.sample(self.incidents, min(10, len(self.incidents))):
            if inc.get("oncall") and isinstance(inc["oncall"], dict):
                self._add(
                    f"What department is the person who handled the {inc['date']} {inc['type']} incident in?",
                    inc["oncall"].get("department", "unknown"),
                    "multi_hop", "hard",
                    f"incidents/ → team/",
                    "Requires: find incident → find on-call name → find their department",
                )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 5: DISAMBIGUATION — Same name, different people
    # ════════════════════════════════════════════════════════════════════
    def _disambiguation_queries(self):
        """Queries about people who share names."""
        for name, ids in self.disambiguation.items():
            if len(ids) < 2:
                continue
            
            p1 = self.people[ids[0]]
            p2 = self.people[ids[1]] if ids[1] < len(self.people) else None
            if not p2:
                continue
            
            # Ask about specific one using department qualifier
            self._add(
                f"What is {name}'s role in {p1['department']}?",
                p1["role"],
                "disambiguation", "hard",
                f"team/",
                f"Two people named {name} exist. Must use department to disambiguate.",
            )
            
            self._add(
                f"Where does {name} from {p2['department']} live?",
                p2.get("city", "unknown"),
                "disambiguation", "hard",
                f"team/",
                f"Must distinguish from {name} in {p1['department']}.",
            )
            
            # Without qualifier — system should return BOTH or indicate ambiguity
            self._add(
                f"Tell me about {name}",
                name,
                "disambiguation", "brutal",
                f"team/",
                f"Ambiguous query — two people share this name. Both should surface.",
            )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 6: FRAGMENTATION — Answers split across chunks
    # ════════════════════════════════════════════════════════════════════
    def _fragmentation_queries(self):
        """Queries where the answer spans chunk boundaries."""
        # Person queries where answer is in a different section than what you'd expect
        for p in self.rng.sample(self.people, min(15, len(self.people))):
            # Salary is in "Work" section but query sounds personal
            self._add(
                f"How much does {p['name']} make?",
                f"${p['salary']:,}",
                "fragmentation", "medium",
                f"team/{p['first'].lower()}-{p['last'].lower()}.md",
                "Salary in Work section, query sounds like Personal section",
            )
            
            # Email in Contact section but query about "reaching" them
            self._add(
                f"How do I reach {p['name']}?",
                p["email"],
                "fragmentation", "medium",
                f"team/{p['first'].lower()}-{p['last'].lower()}.md",
                "Contact info in separate section from bio",
            )
        
        # Story queries where the answer setup is early but payoff is later
        self._add(
            "In The Signal, what was the message about?",
            "warning",
            "fragmentation", "hard",
            "creative/the-signal.md",
            "Setup in Part 1-2, answer in Part 3. Chunks may split parts.",
        )
        
        self._add(
            "What technology did the alien signal contain blueprints for?",
            "carbon capture",
            "fragmentation", "hard",
            "creative/the-signal.md",
            "Answer is in Part 3, deep in the document",
        )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 7: SYNONYMS — Same meaning, different words
    # ════════════════════════════════════════════════════════════════════
    def _synonym_queries(self):
        """Test synonym/paraphrase understanding."""
        # Salary synonyms
        p = self.rng.choice(self.people)
        self._add(f"What is {p['name']}'s compensation?", f"${p['salary']:,}",
                  "synonym", "medium", notes="compensation = salary")
        
        p = self.rng.choice(self.people)
        self._add(f"What is {p['name']}'s annual pay?", f"${p['salary']:,}",
                  "synonym", "medium", notes="pay = salary = compensation")
        
        p = self.rng.choice(self.people)
        self._add(f"{p['name']}'s remuneration", f"${p['salary']:,}",
                  "synonym", "hard", notes="remuneration is uncommon synonym for salary")
        
        # Role synonyms
        p = self.rng.choice(self.people)
        self._add(f"What is {p['name']}'s job title?", p["role"],
                  "synonym", "medium", notes="job title = role")
        
        p = self.rng.choice(self.people)
        self._add(f"What position does {p['name']} hold?", p["role"],
                  "synonym", "medium", notes="position = role")
        
        # Location synonyms
        p = self.rng.choice(self.people)
        self._add(f"Where is {p['name']} based?", p["city"],
                  "synonym", "medium", notes="based = lives in")
        
        p = self.rng.choice(self.people)
        self._add(f"{p['name']}'s place of residence", p["city"],
                  "synonym", "hard", notes="place of residence = lives in")
        
        # Company synonyms
        self._add("What is Nexus Dynamics' annual recurring revenue?", "67.3",
                  "synonym", "medium", notes="annual recurring revenue = ARR")
        
        self._add("Nexus Dynamics revenue run rate", "67.3",
                  "synonym", "hard", notes="revenue run rate ≈ ARR")
        
        self._add("headcount at Nexus Dynamics", str(len(self.people)),
                  "synonym", "medium", notes="headcount = employees")
        
        # Benefits synonyms
        self._add("What is the employer retirement plan match?", "6%",
                  "synonym", "hard", notes="employer retirement plan match = 401k match")
        
        self._add("maternity and paternity leave policy", "20 weeks",
                  "synonym", "medium", notes="maternity/paternity = parental leave")
        
        self._add("time off policy", "Unlimited",
                  "synonym", "medium", notes="time off = PTO")
        
        # Technical synonyms
        self._add("primary data store technology", "CockroachDB",
                  "synonym", "hard", notes="data store = database")
        
        self._add("message broker system", "Kafka",
                  "synonym", "hard", notes="message broker = queue")
        
        # Domain jargon
        self._add("NRR percentage", "142",
                  "synonym", "hard", notes="NRR = net revenue retention")
        
        self._add("EIN for Nexus Dynamics", "83-4827156",
                  "synonym", "medium", notes="EIN = employer identification number")
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 8: ADVERSARIAL — Designed to confuse
    # ════════════════════════════════════════════════════════════════════
    def _adversarial_queries(self):
        """Queries with negation, misdirection, false presuppositions."""
        # Misdirection: ask about something that doesn't apply
        for p in self.rng.sample(self.people, min(10, len(self.people))):
            if p.get("pet_type") == "cat" or not p.get("pet_type"):
                self._add(
                    f"What is {p['name']}'s dog's name?",
                    "__NONE__" if not p.get("pet_type") or p["pet_type"] != "dog" else p["pet_name"],
                    "adversarial", "hard",
                    notes=f"{p['name']} has a {p.get('pet_type', 'no pet')}, not a dog" if p.get("pet_type") != "dog" else "",
                    expect_absent=p.get("pet_type") != "dog",
                )
                break
        
        for p in self.rng.sample(self.people, min(10, len(self.people))):
            if not p.get("partner"):
                self._add(
                    f"What is {p['name']}'s spouse's occupation?",
                    "__NONE__",
                    "adversarial", "hard",
                    notes=f"{p['name']} has no partner listed",
                    expect_absent=True,
                )
                break
        
        # False presupposition about the company
        self._add(
            "When did Nexus Dynamics go public?",
            "__NONE__",
            "adversarial", "hard",
            notes="Company is private, never went public",
            expect_absent=True,
        )
        
        self._add(
            "What is Nexus Dynamics' stock ticker symbol?",
            "__NONE__",
            "adversarial", "hard",
            notes="Private company, no ticker",
            expect_absent=True,
        )
        
        self._add(
            "Who replaced Clara Whitfield as CEO?",
            "__NONE__",
            "adversarial", "hard",
            notes="Clara is still CTO (and co-founder). Nobody replaced her.",
            expect_absent=True,
        )
        
        # Negation queries
        self._add(
            "Which team members do NOT have pets?",
            "__COMPLEX__",
            "adversarial", "brutal",
            notes="Negation query — most systems will return people WITH pets",
        )
        
        self._add(
            "Which projects are NOT using Python?",
            "__COMPLEX__",
            "adversarial", "brutal",
            notes="Negation — systems will retrieve Python projects instead",
        )
        
        # Close-but-wrong queries
        self._add(
            "What is the Series A valuation of Nexus Dynamics?",
            "__NONE__",
            "adversarial", "hard",
            notes="Series A amount ($22M) exists but valuation at that round is never stated. Only post-Series C valuation ($1.4B) is stated.",
            expect_absent=True,
        )
        
        # Temporal misdirection
        self._add(
            "What is the current Datadog API key dd-api-OLD-3x7k9m2p?",
            "__NONE__",
            "adversarial", "brutal",
            notes="This IS the old key. The current one is dd-api-7x9k2m4p8q. Query presupposes the old key is current.",
            expect_absent=True,
        )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 9: PRECISION — Right result, not just related
    # ════════════════════════════════════════════════════════════════════
    def _precision_queries(self):
        """Must return exact match, not similar-but-wrong."""
        # Specific person's detail among many similar people
        for p in self.rng.sample(self.people, min(20, len(self.people))):
            self._add(
                f"What is {p['name']}'s exact email address?",
                p["email"],
                "precision", "medium",
                notes="Must return THIS person's email, not someone with similar name",
            )
            
            self._add(
                f"What department does {p['name']} work in?",
                p["department"],
                "precision", "medium",
            )
        
        # Specific customer among many
        for c in self.rng.sample(self.customers, min(10, len(self.customers))):
            self._add(
                f"What plan is {c['company']} on?",
                c["plan"],
                "precision", "medium",
                notes="Must match exact company, not similar-named one",
            )
        
        # Specific incident by date
        for inc in self.rng.sample(self.incidents, min(5, len(self.incidents))):
            self._add(
                f"What was the severity of the {inc['date']} {inc['type']} incident?",
                inc["severity"],
                "precision", "hard",
                notes="Must match exact date AND type",
            )
        
        # SLA precision
        self._add("What is the RPO target?", "0",
                  "precision", "hard",
                  notes="RPO is 0 (synchronous). Must not confuse with RTO (2 minutes).")
        
        self._add("What is the RTO target?", "2 minutes",
                  "precision", "hard",
                  notes="RTO is 2 minutes. Must not confuse with RPO (0).")
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 10: QUANTITATIVE — Comparison/ranking
    # ════════════════════════════════════════════════════════════════════
    def _quantitative_queries(self):
        """Queries requiring numerical comparison."""
        # Highest salary
        sorted_by_salary = sorted(self.people, key=lambda p: p["salary"], reverse=True)
        highest = sorted_by_salary[0]
        self._add(
            "Who has the highest salary at Nexus Dynamics?",
            highest["name"],
            "quantitative", "brutal",
            notes=f"Requires comparing salaries across all {len(self.people)} people. Answer: {highest['name']} at ${highest['salary']:,}",
        )
        
        # Oldest person
        oldest = max(self.people, key=lambda p: p["age"])
        self._add(
            "Who is the oldest employee?",
            oldest["name"],
            "quantitative", "brutal",
            notes=f"Requires comparing ages. Answer: {oldest['name']} at {oldest['age']}",
        )
        
        # Youngest
        youngest = min(self.people, key=lambda p: p["age"])
        self._add(
            "Who is the youngest team member?",
            youngest["name"],
            "quantitative", "brutal",
            notes=f"Answer: {youngest['name']} at {youngest['age']}",
        )
        
        # Most experienced
        most_exp = max(self.people, key=lambda p: p["years_experience"])
        self._add(
            "Who has the most years of experience?",
            most_exp["name"],
            "quantitative", "brutal",
            notes=f"Answer: {most_exp['name']} with {most_exp['years_experience']} years",
        )
        
        # Largest customer by ARR
        if self.customers:
            biggest = max(self.customers, key=lambda c: c["arr"])
            self._add(
                "Which customer has the highest ARR?",
                biggest["company"],
                "quantitative", "brutal",
                notes=f"Answer: {biggest['company']} at ${biggest['arr']:,}",
            )
        
        # Longest incident
        if self.incidents:
            longest_inc = max(self.incidents, key=lambda i: i["duration_min"])
            self._add(
                "What was the longest incident by duration?",
                longest_inc["title"],
                "quantitative", "brutal",
                notes=f"Answer: {longest_inc['title']} at {longest_inc['duration_min']} minutes",
            )
        
        # Biggest project budget
        if self.projects:
            biggest_proj = max(self.projects, key=lambda p: p["budget"])
            self._add(
                "Which project has the largest budget?",
                biggest_proj["name"],
                "quantitative", "brutal",
                notes=f"Answer: {biggest_proj['name']} at ${biggest_proj['budget']:,}",
            )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 11: NEGATIVE — Info that doesn't exist
    # ════════════════════════════════════════════════════════════════════
    def _negative_queries(self):
        """Questions with no answer in the corpus."""
        negatives = [
            ("What is the company's Twitter/X handle?", "Never mentioned"),
            ("What floor is the Boulder office on?", "Suite number exists but floor never specified"),
            ("When is the next board meeting?", "Past board meetings mentioned but no future date"),
            ("What is the cafeteria menu for Monday?", "Free lunch mentioned but no menu"),
            ("Who is the Head of AI?", "No such role exists in the corpus"),
            ("What is the company's DUNS number?", "Only EIN is listed"),
            ("When does the fiscal year end?", "Never specified"),
            ("What is the company's NPS score?", "Customer NPS exists but company-wide NPS never stated"),
            ("How many patents does Nexus Dynamics hold?", "Never mentioned"),
            ("What is the employee attrition rate?", "Never mentioned"),
            ("Who is on the board of directors?", "Board meetings mentioned but members never listed"),
            ("What is the company's carbon footprint?", "Never mentioned"),
            ("office dog policy breed restrictions", "Dog-friendly mentioned but no breed policy"),
            ("What CRM does the sales team use?", "Never specified"),
            ("VPN credentials for production access", "VPN never mentioned, only SSH"),
        ]
        
        for query, note in negatives:
            self._add(query, "__NONE__", "negative", "hard",
                      notes=note, expect_absent=True)
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 12: IMPLICIT — Inferred, not stated directly
    # ════════════════════════════════════════════════════════════════════
    def _implicit_queries(self):
        """Facts that must be inferred from context."""
        for p in self.rng.sample(self.people, min(10, len(self.people))):
            if p.get("partner"):
                self._add(
                    f"Is {p['name']} in a relationship?",
                    "yes",
                    "implicit", "hard",
                    notes=f"Never says 'in a relationship' — partner '{p['partner']}' is listed",
                )
            
            if p.get("kids"):
                self._add(
                    f"Is {p['name']} a parent?",
                    "yes",
                    "implicit", "hard",
                    notes=f"Never says 'is a parent' — children are listed",
                )
                
                self._add(
                    f"How many children does {p['name']} have?",
                    str(len(p["kids"])),
                    "implicit", "medium",
                )
        
        # Company inferences
        self._add(
            "Is Nexus Dynamics profitable?",
            "__AMBIGUOUS__",
            "implicit", "brutal",
            notes="Burn rate and runway mentioned but profitability never stated. Has funding runway of 28+ months which implies burning cash.",
        )
        
        self._add(
            "Is Nexus Dynamics a unicorn?",
            "yes",
            "implicit", "hard",
            notes="Valuation $1.4B stated, 'unicorn status achieved' explicitly mentioned",
        )
        
        self._add(
            "Does the company offer remote work?",
            "__AMBIGUOUS__",
            "implicit", "hard",
            notes="Equipment budget for 'home office' implies remote/hybrid, but never explicitly stated",
        )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 13: LONG-RANGE — Answer from distant doc parts
    # ════════════════════════════════════════════════════════════════════
    def _long_range_queries(self):
        """Answers requiring context from far-apart sections."""
        # Story questions that span the entire document
        self._add(
            "In The Signal story, how many of their population did the aliens lose?",
            "6 of our 8 billion",
            "long_range", "hard",
            "creative/the-signal.md",
            "Answer is in Part 3, last section of a long story",
        )
        
        self._add(
            "What was the signal's repeat interval in seconds?",
            "73.6",
            "long_range", "hard",
            "creative/the-signal.md",
            "Specific number from Part 1 of a multi-part story",
        )
        
        self._add(
            "Who is Callum Reed in The Signal?",
            "assistant",
            "long_range", "medium",
            "creative/the-signal.md",
        )
        
        self._add(
            "What was Step 2 of the First Contact Protocol?",
            "Do not respond",
            "long_range", "hard",
            "creative/the-signal.md",
            "Specific detail from Part 2",
        )
        
        # Production doc: connect SLA to infra
        self._add(
            "How many GPU nodes in production?",
            "4",
            "long_range", "medium",
            "infrastructure/production.md",
            "Detail buried among many server listings",
        )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 14: RECENCY — Recent should rank higher
    # ════════════════════════════════════════════════════════════════════
    def _recency_queries(self):
        """Test that recent info is preferred over old."""
        # Current vs archived credentials
        self._add(
            "What Datadog API key should I use?",
            "dd-api-7x9k2m4p8q",
            "recency", "hard",
            "infrastructure/production.md",
            "Old key exists in archive. Must prefer current.",
        )
        
        self._add(
            "Current health insurance provider",
            "United Healthcare",
            "recency", "hard",
            "company/benefits.md",
            "Old provider (Cigna) exists in archive.",
        )
        
        self._add(
            "What is the 401k match?",
            "6%",
            "recency", "hard",
            "company/benefits.md",
            "Old match (4%) exists in archive.",
        )
        
        self._add(
            "How many Redis cache nodes do we have?",
            "5",
            "recency", "hard",
            "infrastructure/production.md",
            "Old value (3) exists in archive.",
        )
        
        self._add(
            "What is our API availability SLA?",
            "99.99%",
            "recency", "hard",
            "infrastructure/production.md",
            "Old SLA (99.9%) exists in archive.",
        )
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 15: ROBUSTNESS — Handle garbage gracefully
    # ════════════════════════════════════════════════════════════════════
    def _robustness_queries(self):
        """Edge cases, typos, and garbage input."""
        # Typos
        p = self.rng.choice(self.people)
        mangled = p["name"][0] + p["name"][2:] + p["name"][1]  # swap chars
        self._add(f"{mangled} department", p["department"],
                  "robustness", "medium", notes="Typo in name")
        
        # Misspelled company
        self._add("Nexis Dinamics EIN number", "83-4827156",
                  "robustness", "hard", notes="Misspelled company name")
        
        # Mixed case
        self._add("WHAT IS THE COMPANY EIN?", "83-4827156",
                  "robustness", "medium", notes="All caps query")
        
        # No punctuation
        self._add("whats the datadog api key", "dd-api-7x9k2m4p8q",
                  "robustness", "medium", notes="No punctuation, casual")
        
        # SQL injection (should not crash)
        self._add("'; DROP TABLE users; --", "__NONE__",
                  "robustness", "medium", notes="SQL injection attempt",
                  expect_absent=True)
        
        # XSS
        self._add("<script>alert('xss')</script>", "__NONE__",
                  "robustness", "medium", notes="XSS attempt",
                  expect_absent=True)
        
        # Unicode
        self._add("会社のEIN番号は？", "__NONE__",
                  "robustness", "hard", notes="Japanese query — should not crash",
                  expect_absent=True)
        
        # Emoji
        self._add("🔑 API keys 🔐", "dd-api",
                  "robustness", "hard", notes="Query with emoji")
        
        # Empty-ish
        self._add("   ", "__NONE__",
                  "robustness", "medium", notes="Whitespace only",
                  expect_absent=True)
        
        # Very long
        self._add("tell me " * 200 + "about the company EIN", "83-4827156",
                  "robustness", "hard", notes="Very long query with signal at end")
    
    # ════════════════════════════════════════════════════════════════════
    # CATEGORY 16: CROSS-DOCUMENT — Synthesize from multiple files
    # ════════════════════════════════════════════════════════════════════
    def _cross_document_queries(self):
        """Facts spanning multiple files."""
        # Person mentioned in project + their personal file
        for proj in self.rng.sample(self.projects, min(10, len(self.projects))):
            if isinstance(proj.get("lead"), dict):
                lead = proj["lead"]
                self._add(
                    f"What are {lead['name']}'s hobbies? They lead Project {proj['name']}.",
                    lead.get("hobby1", "unknown"),
                    "cross_document", "hard",
                    f"projects/ + team/",
                    "Must connect project lead to person file for hobbies",
                )
        
        # Incidents mentioning on-call + their background
        for inc in self.rng.sample(self.incidents, min(5, len(self.incidents))):
            if inc.get("oncall") and isinstance(inc["oncall"], dict):
                oncall = inc["oncall"]
                self._add(
                    f"What university did the on-call for the {inc['date']} incident attend?",
                    oncall.get("university", "unknown"),
                    "cross_document", "brutal",
                    f"incidents/ + team/",
                    "3 files: incident → on-call name → person → university",
                )
    
    # ════════════════════════════════════════════════════════════════════
    # PERSONAL DETAILS — Deep personal fact retrieval
    # ════════════════════════════════════════════════════════════════════
    def _personal_detail_queries(self):
        """Rich personal fact queries."""
        for p in self.rng.sample(self.people, min(25, len(self.people))):
            self._add(f"How old is {p['name']}?", str(p["age"]),
                      "personal", "medium")
            
            self._add(f"{p['name']}'s birthday", p["birth_display"],
                      "personal", "medium")
            
            self._add(f"Where does {p['name']} live?", p["city"],
                      "personal", "medium")
            
            self._add(f"What are {p['name']}'s hobbies?", p["hobby1"],
                      "personal", "medium")
            
            self._add(f"Where did {p['name']} work before Nexus Dynamics?",
                      p["prev_company"], "personal", "medium")
            
            if p.get("kids"):
                kid = p["kids"][0]
                self._add(
                    f"What is the name of {p['name']}'s child?",
                    kid["name"],
                    "personal", "hard",
                )
    
    # ════════════════════════════════════════════════════════════════════
    # CREDENTIAL QUERIES — Security-sensitive searches
    # ════════════════════════════════════════════════════════════════════
    def _credential_queries(self):
        """Find specific credentials and config values."""
        self._add("AWS Account ID", "729481035267", "credential", "medium",
                  "infrastructure/production.md")
        self._add("Sentry DSN", "xyz789@sentry.io/5908234", "credential", "hard",
                  "infrastructure/production.md")
        self._add("PagerDuty key", "pd-svc-3f8k9m2x", "credential", "medium",
                  "infrastructure/production.md")
        self._add("Nexus Dynamics EIN", "83-4827156", "credential", "medium",
                  "company/about.md")
        self._add("company mailing address", "1847 Cascade", "credential", "medium",
                  "company/about.md")
        self._add("Kafka broker address", "kafka-prod", "credential", "medium",
                  "infrastructure/production.md")
        self._add("ML inference instance type", "g5.4xlarge", "credential", "hard",
                  "infrastructure/production.md")
        self._add("Elasticsearch cluster size", "9-node", "credential", "medium",
                  "infrastructure/production.md")
        self._add("staging SSH bastion port", "2222", "credential", "hard",
                  "infrastructure/production.md",
                  "Port is in server configs, not main production doc")


def main():
    parser = argparse.ArgumentParser(description="Generate IRONMAN queries")
    parser.add_argument("--corpus", default="./corpus", help="Corpus directory")
    parser.add_argument("--output", default="./queries.json", help="Output file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    corpus = Path(args.corpus)
    world_state_path = corpus / "world_state.json"
    
    if not world_state_path.exists():
        print(f"World state not found at {world_state_path}")
        print("Run generate_corpus.py first.")
        return 1
    
    with open(world_state_path) as f:
        world_state = json.load(f)
    
    gen = QueryGenerator(world_state, args.seed)
    queries = gen.generate_all()
    
    with open(args.output, "w") as f:
        json.dump(queries, f, indent=2)
    
    # Stats
    by_cat = {}
    by_diff = {}
    for q in queries:
        cat = q["category"]
        diff = q["difficulty"]
        by_cat[cat] = by_cat.get(cat, 0) + 1
        by_diff[diff] = by_diff.get(diff, 0) + 1
    
    print(f"\nGenerated {len(queries)} queries → {args.output}")
    print(f"\nBy category:")
    for cat in sorted(by_cat.keys()):
        print(f"  {cat:<20} {by_cat[cat]:>4}")
    print(f"\nBy difficulty:")
    for diff in ["medium", "hard", "brutal"]:
        print(f"  {diff:<20} {by_diff.get(diff, 0):>4}")
    
    return 0


if __name__ == "__main__":
    exit(main())
