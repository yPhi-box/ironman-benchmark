#!/usr/bin/env python3
"""
IRONMAN Scoring Engine v2
Universal scorer for ANY memory system.

Rules:
- Each result must have 'text' (content) and optionally 'score', 'file_path'
- Pass/fail checks expect string in ALL returned text (not just first 100 chars)
- Systems that return whole files vs chunks are treated equally
- Negative queries pass when no results or low confidence
"""
import math
from typing import List, Dict, Optional


class IronmanScorer:
    """Scores search results against ground truth."""
    
    CATEGORY_WEIGHTS = {
        "needle": 0.08,
        "temporal": 0.08,
        "contradiction": 0.08,
        "multi_hop": 0.10,
        "disambiguation": 0.07,
        "fragmentation": 0.06,
        "synonym": 0.05,
        "adversarial": 0.07,
        "precision": 0.06,
        "quantitative": 0.05,
        "negative": 0.05,
        "implicit": 0.05,
        "long_range": 0.05,
        "recency": 0.05,
        "robustness": 0.03,
        "cross_document": 0.05,
        "personal": 0.05,
        "credential": 0.03,
    }
    
    def __init__(self):
        self.results = []
        self.by_category = {}
        self.by_difficulty = {}
    
    def score_query(self, query: dict, search_results: List[dict], k: int = 5) -> dict:
        """
        Score a single query.
        
        search_results: list of dicts, each MUST have 'text' (full content returned).
                       Optionally 'score' and 'file_path'.
        """
        expect = query["expect"]
        category = query["category"]
        difficulty = query.get("difficulty", "medium")
        expect_absent = query.get("expect_absent", False)
        
        # Get text from each result - use FULL text, never truncate for matching
        texts = [r.get("text", "") for r in search_results[:k]]
        
        result = {
            "query": query["query"],
            "expect": expect,
            "category": category,
            "difficulty": difficulty,
        }
        
        # --- Negative / special queries ---
        if expect in ("__NONE__", "__COMPLEX__", "__AMBIGUOUS__") or expect_absent:
            if expect in ("__COMPLEX__", "__AMBIGUOUS__"):
                result["pass"] = True
                result["rank"] = None
                result["mrr"] = 0
            elif expect == "__NONE__":
                if not search_results:
                    result["pass"] = True
                else:
                    top_score = search_results[0].get("score", 1.0)
                    result["pass"] = top_score < 0.5
                result["rank"] = None
                result["mrr"] = 1.0 if result["pass"] else 0.0
            
            result["acc_at_1"] = 1 if result.get("pass") else 0
            result["acc_at_3"] = result["acc_at_1"]
            result["acc_at_5"] = result["acc_at_1"]
            result["dcg"] = 0.0
            result["ndcg"] = 0.0
            self._record(result)
            return result
        
        # --- Standard queries: find expected text in results ---
        found_rank = None
        expect_lower = expect.lower()
        
        for i, text in enumerate(texts):
            # Check FULL text of each result, not truncated
            if expect_lower in text.lower():
                found_rank = i + 1
                break
        
        result["pass"] = found_rank is not None
        result["rank"] = found_rank
        result["mrr"] = (1.0 / found_rank) if found_rank else 0.0
        result["acc_at_1"] = 1 if found_rank == 1 else 0
        result["acc_at_3"] = 1 if found_rank and found_rank <= 3 else 0
        result["acc_at_5"] = 1 if found_rank and found_rank <= 5 else 0
        result["dcg"] = (1.0 / math.log2(found_rank + 1)) if found_rank else 0.0
        result["ndcg"] = result["dcg"]
        
        if not result["pass"]:
            # Show what we got (truncated for display only, NOT for matching)
            if texts:
                result["got"] = texts[0][:200]
            else:
                result["got"] = "(no results)"
        
        self._record(result)
        return result
    
    def _record(self, result: dict):
        self.results.append(result)
        cat = result["category"]
        diff = result["difficulty"]
        self.by_category.setdefault(cat, []).append(result)
        self.by_difficulty.setdefault(diff, []).append(result)
    
    def summary(self) -> dict:
        total = len(self.results)
        if total == 0:
            return {"error": "No results scored"}
        
        passed = sum(1 for r in self.results if r["pass"])
        
        overall = {
            "total_queries": total,
            "passed": passed,
            "failed": total - passed,
            "accuracy": round(passed / total * 100, 1),
            "mrr": round(sum(r["mrr"] for r in self.results) / total, 4),
            "avg_ndcg": round(sum(r.get("ndcg", 0) for r in self.results) / total, 4),
            "acc_at_1": round(sum(r.get("acc_at_1", 0) for r in self.results) / total * 100, 1),
            "acc_at_3": round(sum(r.get("acc_at_3", 0) for r in self.results) / total * 100, 1),
            "acc_at_5": round(sum(r.get("acc_at_5", 0) for r in self.results) / total * 100, 1),
        }
        
        categories = {}
        for cat, results in sorted(self.by_category.items()):
            n = len(results)
            p = sum(1 for r in results if r["pass"])
            categories[cat] = {
                "total": n,
                "passed": p,
                "failed": n - p,
                "accuracy": round(p / n * 100, 1) if n > 0 else 0,
                "mrr": round(sum(r["mrr"] for r in results) / n, 4) if n > 0 else 0,
                "ndcg": round(sum(r.get("ndcg", 0) for r in results) / n, 4) if n > 0 else 0,
                "weight": self.CATEGORY_WEIGHTS.get(cat, 0.03),
            }
        
        weighted_score = 0
        total_weight = 0
        for cat, scores in categories.items():
            w = scores["weight"]
            weighted_score += scores["accuracy"] * w
            total_weight += w
        if total_weight > 0:
            overall["weighted_score"] = round(weighted_score / total_weight, 1)
        
        difficulties = {}
        for diff, results in sorted(self.by_difficulty.items()):
            n = len(results)
            p = sum(1 for r in results if r["pass"])
            difficulties[diff] = {
                "total": n,
                "passed": p,
                "accuracy": round(p / n * 100, 1) if n > 0 else 0,
            }
        
        failures = [r for r in self.results if not r["pass"]]
        
        return {
            "overall": overall,
            "categories": categories,
            "difficulties": difficulties,
            "failure_count": len(failures),
            "failure_sample": failures[:20],
        }
    
    def grade(self, score: float) -> str:
        if score >= 95: return "S"
        if score >= 90: return "A"
        if score >= 80: return "B"
        if score >= 70: return "C"
        if score >= 60: return "D"
        if score >= 40: return "E"
        return "F"
    
    def grade_label(self, score: float) -> str:
        labels = {
            "S": "Exceptional", "A": "Outstanding", "B": "Strong",
            "C": "Adequate", "D": "Below average", "E": "Weak", "F": "Failing"
        }
        g = self.grade(score)
        return f"{g} — {labels[g]}"
    
    def print_report(self, summary: dict = None):
        if summary is None:
            summary = self.summary()
        
        o = summary["overall"]
        score = o.get("weighted_score", o["accuracy"])
        
        print(f"\n{'=' * 70}")
        print(f"   IRONMAN MEMORY BENCHMARK — RESULTS")
        print(f"{'=' * 70}")
        
        print(f"""
  Queries:  {o['total_queries']}
  Passed:   {o['passed']}
  Failed:   {o['failed']}
  
  ┌──────────────────────────────────────────┐
  │  ACCURACY:      {o['accuracy']:>5.1f}%                 │
  │  WEIGHTED:      {score:>5.1f}%                 │
  │  MRR:           {o['mrr']:>6.4f}                │
  │  NDCG@5:        {o['avg_ndcg']:>6.4f}                │
  │  Acc@1:         {o['acc_at_1']:>5.1f}%                 │
  │  Acc@3:         {o['acc_at_3']:>5.1f}%                 │
  │  Acc@5:         {o['acc_at_5']:>5.1f}%                 │
  │  GRADE:         {self.grade_label(score):<25}│
  └──────────────────────────────────────────┘
""")
        
        print(f"  {'Category':<18} {'Pass':>5} {'Fail':>5} {'Acc%':>7}")
        print(f"  {'─' * 18} {'─' * 5} {'─' * 5} {'─' * 7}")
        for cat in sorted(summary["categories"].keys()):
            c = summary["categories"][cat]
            mark = "✓" if c["accuracy"] >= 90 else ("~" if c["accuracy"] >= 70 else "✗")
            print(f"  {cat:<18} {c['passed']:>5} {c['failed']:>5} {c['accuracy']:>6.1f}% {mark}")
        
        print(f"\n  {'Difficulty':<18} {'Pass/Total':>10} {'Acc%':>7}")
        print(f"  {'─' * 18} {'─' * 10} {'─' * 7}")
        for diff in ["medium", "hard", "brutal"]:
            if diff in summary["difficulties"]:
                d = summary["difficulties"][diff]
                print(f"  {diff:<18} {d['passed']:>4}/{d['total']:<5} {d['accuracy']:>6.1f}%")
        
        if summary.get("failure_sample"):
            print(f"\n  FAILURES ({summary['failure_count']} total, showing 10)")
            for f in summary["failure_sample"][:10]:
                print(f"    [{f['category']}/{f['difficulty']}] {f['query'][:60]}")
                print(f"      Want: {f['expect'][:60]}")
                if f.get("got"):
                    print(f"      Got:  {f['got'][:60]}")
