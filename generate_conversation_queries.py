#!/usr/bin/env python3
"""
IRONMAN Query Generator v3
Balanced categories following LoCoMo methodology.

Distribution:
  ~30% single-hop (needle/personal) — find one specific fact
  ~20% multi-hop — connect facts across messages
  ~15% temporal — time/order reasoning
  ~15% adversarial/negative — trick questions, unanswerable
  ~10% contradiction — facts that changed (month/year only)
  ~10% other (synonym, robustness, precision, implicit)

Rules:
  - Day tier: NO contradiction queries (nothing changes in one day)
  - Month tier: Some contradictions (things start changing)
  - Year tier: Full contradictions (lots has changed)
  - Cap categories to prevent skew
"""
import json
import random
from typing import List, Dict
from collections import Counter

COMPANY_EIN = "83-4827156"


class ConversationQueryGenerator:
    
    def __init__(self, world_state: dict, corpus: list, seed=42):
        self.world = world_state
        self.corpus = corpus
        self.rng = random.Random(seed)
        self.queries = []
        
        self.day_cutoff = 50
        self.month_cutoff = 1200
    
    def _tier_for_index(self, idx: int) -> str:
        if idx < self.day_cutoff:
            return "day"
        elif idx < self.month_cutoff:
            return "month"
        return "year"
    
    def _find_msg(self, text: str) -> int:
        """Find first message containing text."""
        t = text.lower()
        for i, m in enumerate(self.corpus):
            if t in m["message"].lower():
                return i
        return len(self.corpus) - 1
    
    def _find_msg_both(self, text1: str, text2: str) -> int:
        """Find message containing both texts."""
        t1, t2 = text1.lower(), text2.lower()
        for i, m in enumerate(self.corpus):
            msg = m["message"].lower()
            if t1 in msg and t2 in msg:
                return i
        return -1
    
    def _add(self, query, expect, category, difficulty, tier=None, msg_index=None):
        if msg_index is not None and msg_index >= 0:
            tier = self._tier_for_index(msg_index)
        elif tier is None:
            tier = "year"
        self.queries.append({
            "query": query, "expect": expect,
            "category": category, "difficulty": difficulty, "tier": tier,
        })
    
    def generate_all(self) -> list:
        self.queries = []
        
        # --- SINGLE-HOP (~30%) ---
        self._needle_queries()
        self._personal_queries()
        
        # --- MULTI-HOP (~20%) ---
        self._multi_hop_queries()
        self._cross_ref_queries()
        
        # --- TEMPORAL (~15%) ---
        self._temporal_queries()
        
        # --- ADVERSARIAL/NEGATIVE (~15%) ---
        self._negative_queries()
        self._adversarial_queries()
        
        # --- CONTRADICTION (~10%, month/year only) ---
        self._contradiction_queries()
        
        # --- OTHER (~10%) ---
        self._synonym_queries()
        self._precision_queries()
        self._implicit_queries()
        self._robustness_queries()
        
        self.rng.shuffle(self.queries)
        
        # Print distribution
        cats = Counter(q["category"] for q in self.queries)
        tiers = Counter(q["tier"] for q in self.queries)
        total = len(self.queries)
        print(f"\nQuery distribution ({total} total):")
        for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {cat:<20} {n:>4} ({n/total*100:>5.1f}%)")
        print(f"\nBy tier:")
        for t, n in sorted(tiers.items()):
            print(f"  {t:<20} {n:>4} ({n/total*100:>5.1f}%)")
        
        return self.queries
    
    # ---- SINGLE-HOP ----
    
    def _needle_queries(self):
        """Find specific facts: phone, email, employee ID, desk."""
        count = 0
        for p in self.world["people"]:
            if count > 150:
                break
            
            # Phone
            idx = self._find_msg(p["phone"])
            if idx < len(self.corpus):
                self._add(f"What is {p['full']}'s phone number?",
                         p["phone"], "needle", "medium", msg_index=idx)
                count += 1
            
            # Email
            idx = self._find_msg(p["email"])
            if idx < len(self.corpus):
                self._add(f"What is {p['full']}'s email address?",
                         p["email"], "needle", "medium", msg_index=idx)
                count += 1
            
            # Employee ID
            idx = self._find_msg(p["employee_id"])
            if idx < len(self.corpus):
                self._add(f"What is {p['full']}'s employee ID?",
                         p["employee_id"], "needle", "medium", msg_index=idx)
                count += 1
            
            # Desk
            idx = self._find_msg_both(p["full"], p["desk"])
            if idx >= 0:
                self._add(f"Where does {p['full']} sit?",
                         p["desk"], "needle", "hard", msg_index=idx)
                count += 1
        
        # Customer champion emails
        for c in self.world["customers"]:
            idx = self._find_msg(c["champion_email"])
            if idx < len(self.corpus):
                self._add(f"What is the email for {c['company']}'s main contact?",
                         c["champion_email"], "needle", "medium", msg_index=idx)
                count += 1
    
    def _personal_queries(self):
        """Personal details: hobbies, allergies, pets, kids, hometown."""
        count = 0
        for p in self.world["people"]:
            if count > 120:
                break
            
            if p.get("hobby"):
                idx = self._find_msg_both(p["full"], p["hobby"])
                if idx >= 0:
                    self._add(f"What are {p['full']}'s hobbies?",
                             p["hobby"], "personal", "medium", msg_index=idx)
                    count += 1
            
            if p.get("allergy"):
                idx = self._find_msg_both(p["full"], p["allergy"])
                if idx >= 0:
                    self._add(f"What is {p['full']} allergic to?",
                             p["allergy"], "personal", "medium", msg_index=idx)
                    count += 1
            
            if p.get("pet"):
                idx = self._find_msg_both(p["full"], p["pet"]["name"])
                if idx < 0:
                    idx = self._find_msg_both(p["first"], p["pet"]["name"])
                if idx >= 0:
                    self._add(f"What is the name of {p['full']}'s pet?",
                             p["pet"]["name"], "personal", "hard", msg_index=idx)
                    count += 1
            
            if p.get("kids"):
                idx = self._find_msg_both(p["full"], p["kids"][0])
                if idx < 0:
                    idx = self._find_msg_both(p["first"], p["kids"][0])
                if idx >= 0:
                    self._add(f"What are {p['full']}'s children's names?",
                             p["kids"][0], "personal", "medium", msg_index=idx)
                    count += 1
            
            idx = self._find_msg_both(p["full"], p["city"])
            if idx >= 0:
                self._add(f"Where is {p['full']} from?",
                         p["city"], "personal", "medium", msg_index=idx)
                count += 1
    
    # ---- MULTI-HOP ----
    
    def _multi_hop_queries(self):
        """Connect facts across messages."""
        count = 0
        
        # "What team does the person allergic to X work on?"
        for p in self.world["people"]:
            if count > 40:
                break
            if p.get("allergy"):
                idx = self._find_msg_both(p["full"], p["allergy"])
                if idx >= 0:
                    self._add(
                        f"What team does the person allergic to {p['allergy']} work on?",
                        p["team"], "multi_hop", "hard", msg_index=idx)
                    count += 1
        
        # "What is the use case for the customer whose champion is X?"
        for c in self.world["customers"]:
            if count > 60:
                break
            idx = self._find_msg(c["champion"])
            if idx < len(self.corpus):
                self._add(
                    f"What does the customer with contact {c['champion']} use our product for?",
                    c["use_case"][:30], "multi_hop", "hard", msg_index=idx)
                count += 1
    
    def _cross_ref_queries(self):
        """Cross-reference queries linking people to projects/customers."""
        count = 0
        for p in self.world["people"]:
            if count > 30:
                break
            # "What role does the person from [city] on [team] have?"
            idx = self._find_msg_both(p["full"], p["city"])
            if idx >= 0:
                self._add(
                    f"What role does the person from {p['city']} on the {p['team']} team have?",
                    p["role"], "multi_hop", "brutal", msg_index=idx)
                count += 1
    
    # ---- TEMPORAL ----
    
    def _temporal_queries(self):
        """Time-based queries."""
        count = 0
        for fact in self.world.get("facts", []):
            if count > 80:
                break
            ts = fact["timestamp"][:10]
            
            if fact["type"] == "hire":
                person = fact["data"]
                idx = self._find_msg(person["full"])
                if idx < len(self.corpus):
                    self._add(f"When did {person['full']} join the company?",
                             ts, "temporal", "medium", msg_index=idx)
                    count += 1
            
            if fact["type"] == "departure":
                person = fact["data"]
                for i, m in enumerate(self.corpus):
                    if person["full"] in m["message"] and any(w in m["message"].lower() for w in ["leaving", "notice", "moving on", "last day"]):
                        self._add(f"When did {person['full']} leave?",
                                 ts, "temporal", "medium", msg_index=i)
                        count += 1
                        break
            
            if fact["type"] == "credential_rotation":
                data = fact["data"]
                idx = self._find_msg(data["new"])
                if idx < len(self.corpus):
                    self._add(f"When was the {data['service']} key last rotated?",
                             ts, "temporal", "hard", msg_index=idx)
                    count += 1
    
    # ---- ADVERSARIAL / NEGATIVE ----
    
    def _negative_queries(self):
        """Questions that should return nothing."""
        fake_people = [
            "Zephyr Blackstone", "Orion Nightshade", "Phoenix Goldberg",
            "Nebula Sanderson", "Quasar Williams", "Tempest O'Brien",
            "Zenith Kowalski", "Nova Fitzgerald", "Blaze Thornton",
            "Storm Nakamura",
        ]
        for name in fake_people:
            self._add(f"What is {name}'s role at Nexus Dynamics?",
                     "__NONE__", "negative", "medium", tier="day")
        
        fake_facts = [
            ("Where is the Tokyo office?", "day"),
            ("What is the Bitcoin wallet address?", "day"),
            ("Who is the CEO of Google at Nexus?", "day"),
            ("What is the Mars colony project status?", "day"),
            ("What is the company's TikTok handle?", "day"),
            ("When did Nexus go public?", "month"),
            ("What is the London office phone number?", "month"),
            ("Who is the Head of Blockchain?", "month"),
            ("What is the quantum computing budget?", "year"),
            ("When did we acquire Palantir?", "year"),
        ]
        for q, tier in fake_facts:
            self._add(q, "__NONE__", "negative", "medium", tier=tier)
    
    def _adversarial_queries(self):
        """Misleading or tricky queries."""
        count = 0
        # Ask about a real person but wrong fact
        for p in self.world["people"][:15]:
            if count > 20:
                break
            idx = self._find_msg(p["full"])
            if idx < len(self.corpus):
                # Ask about allergy they don't have
                if not p.get("allergy"):
                    self._add(f"What is {p['full']} allergic to?",
                             "__NONE__", "adversarial", "hard", msg_index=idx)
                    count += 1
                # Ask about pet they don't have
                if not p.get("pet"):
                    self._add(f"What is the name of {p['full']}'s dog?",
                             "__NONE__", "adversarial", "hard", msg_index=idx)
                    count += 1
    
    # ---- CONTRADICTION ----
    
    def _contradiction_queries(self):
        """Facts that changed — month/year tiers ONLY."""
        count = 0
        for fact in self.world.get("facts", []):
            if count > 100:
                break
            
            if fact["type"] == "promotion":
                data = fact["data"]
                person = data["person"]
                idx = self._find_msg(data["new"])
                if idx >= 0 and self._tier_for_index(idx) != "day":
                    self._add(f"What is {person['full']}'s current role?",
                             data["new"], "contradiction", "hard", msg_index=idx)
                    count += 1
                    self._add(f"What was {person['full']}'s role before their last promotion?",
                             data["old"], "contradiction", "brutal", msg_index=idx)
                    count += 1
            
            if fact["type"] == "team_move":
                data = fact["data"]
                person = data["person"]
                idx = self._find_msg(data["new"])
                if idx >= 0 and self._tier_for_index(idx) != "day":
                    self._add(f"What team is {person['full']} currently on?",
                             data["new"], "contradiction", "hard", msg_index=idx)
                    count += 1
            
            if fact["type"] == "policy_change":
                data = fact["data"]
                idx = self._find_msg(data["new"])
                if idx >= 0 and self._tier_for_index(idx) != "day":
                    self._add(f"What is the current {data['name']} policy?",
                             data["new"], "contradiction", "hard", msg_index=idx)
                    count += 1
            
            if fact["type"] == "credential_rotation":
                data = fact["data"]
                idx = self._find_msg(data["new"])
                if idx >= 0 and self._tier_for_index(idx) != "day":
                    self._add(f"What is the current {data['service']} API key?",
                             data["new"], "contradiction", "hard", msg_index=idx)
                    count += 1
    
    # ---- OTHER ----
    
    def _synonym_queries(self):
        """Same question, different words."""
        count = 0
        for p in self.world["people"]:
            if count > 30:
                break
            if p.get("allergy"):
                idx = self._find_msg_both(p["full"], p["allergy"])
                if idx >= 0:
                    self._add(f"Does {p['full']} have any food sensitivities?",
                             p["allergy"], "synonym", "medium", msg_index=idx)
                    count += 1
            
            idx = self._find_msg_both(p["full"], p["city"])
            if idx >= 0:
                self._add(f"What city does {p['full']} call home?",
                         p["city"], "synonym", "medium", msg_index=idx)
                count += 1
    
    def _precision_queries(self):
        """Exact values: ARR, salaries, metrics."""
        for c in self.world["customers"]:
            idx = self._find_msg(c["company"])
            if idx < len(self.corpus):
                self._add(f"What is {c['company']}'s ARR?",
                         f"${c['arr']:,}", "precision", "medium", msg_index=idx)
                self._add(f"Who is the main contact at {c['company']}?",
                         c["champion"], "precision", "medium", msg_index=idx)
                self._add(f"What industry is {c['company']} in?",
                         c["industry"], "precision", "medium", msg_index=idx)
        
        for proj in self.world["projects"]:
            tech = proj["tech"].split(",")[0].strip()
            idx = self._find_msg_both(proj["name"], tech)
            if idx >= 0:
                self._add(f"What tech stack does the {proj['name']} project use?",
                         tech, "precision", "medium", msg_index=idx)
    
    def _implicit_queries(self):
        """Facts implied but not directly stated."""
        count = 0
        for p in self.world["people"]:
            if count > 25:
                break
            if p.get("kids"):
                idx = self._find_msg_both(p["first"], p["kids"][0])
                if idx >= 0:
                    msg = self.corpus[idx]["message"]
                    if any(w in msg.lower() for w in ["daughter", "son", "kid", "soccer", "game"]):
                        self._add(f"Is {p['full']} a parent?",
                                 "yes", "implicit", "hard", msg_index=idx)
                        count += 1
            if p.get("pet"):
                idx = self._find_msg_both(p["first"], p["pet"]["name"])
                if idx >= 0:
                    msg = self.corpus[idx]["message"]
                    if any(w in msg.lower() for w in ["vet", "brought", "office", "walk"]):
                        self._add(f"Does {p['full']} have a pet?",
                                 "yes", "implicit", "hard", msg_index=idx)
                        count += 1
    
    def _robustness_queries(self):
        """Garbled, typo'd, or unusual format queries."""
        people = self.world["people"][:10]
        for p in people:
            # Typo in name
            if len(p["full"]) > 3:
                mangled = p["full"][0] + p["full"][2:]
                idx = self._find_msg_both(p["full"], p["role"])
                if idx >= 0:
                    self._add(f"What does {mangled} do?",
                             p["role"], "robustness", "hard", msg_index=idx)
        
        self._add("WHAT IS THE COMPANY EIN NUMBER",
                 COMPANY_EIN, "robustness", "medium", tier="day")
        self._add("tell me about the 401k match",
                 self.world["policies"][1]["value"], "robustness", "medium", tier="day")
        self._add("what what is the office location",
                 "Boulder", "robustness", "medium", tier="day")
    
    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.queries, f, indent=2)
        return path


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="/tmp/ironman_corpus.json")
    parser.add_argument("--state", default="/tmp/ironman_corpus_world_state.json")
    parser.add_argument("--output", default="/tmp/ironman_queries_v2.json")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    with open(args.corpus) as f:
        corpus = json.load(f)
    with open(args.state) as f:
        world = json.load(f)
    
    gen = ConversationQueryGenerator(world, corpus, seed=args.seed)
    queries = gen.generate_all()
    gen.save(args.output)
    print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
