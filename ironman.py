#!/usr/bin/env python3
"""
IRONMAN Memory Benchmark v2
Universal benchmark for any memory system.

Usage:
    # Test OC against Atlas gateway:
    python3 ironman.py --adapter oc --gateway http://localhost:18789 --token xxx --corpus corpus.json --tier month

    # Test HMS:
    python3 ironman.py --adapter hms --url http://localhost:8765 --corpus corpus.json --tier year

    # Grep baseline:
    python3 ironman.py --adapter grep --corpus corpus.json --tier day

    # All three tiers at once:
    python3 ironman.py --adapter hms --url http://localhost:8765 --corpus corpus.json --tier all
"""
import argparse
import json
import time
import sys
import os

from adapters import ADAPTERS, MemoryAdapter
from scorer import IronmanScorer


TIER_SLICES = {
    "day": (0, 50),       # ~1 day of rich conversations
    "month": (0, 1200),   # ~30 days of rich conversations
    "year": (0, None),    # all messages (~14,300)
}


def seed_system(adapter: MemoryAdapter, messages: list) -> dict:
    """Feed messages into the system."""
    print(f"\n  Seeding {len(messages)} messages...")
    
    ok = 0
    errors = 0
    t0 = time.time()
    
    for i, msg in enumerate(messages):
        if (i + 1) % 25 == 0:
            print(f"    {i+1}/{len(messages)} ingested...")
        
        result = adapter.ingest(msg["message"], msg.get("timestamp"))
        if result.get("ok"):
            ok += 1
        else:
            errors += 1
    
    elapsed = time.time() - t0
    
    # For HMS: trigger indexing after all messages are written
    if hasattr(adapter, "flush_index"):
        print("  Indexing...")
        idx_t0 = time.time()
        adapter.flush_index()
        idx_time = time.time() - idx_t0
        print(f"  Indexed in {idx_time:.1f}s")
    
    # For OC: trigger reindex
    if hasattr(adapter, '_reindex'):
        adapter._reindex()
    
    return {
        "messages": len(messages),
        "ok": ok,
        "errors": errors,
        "time_sec": round(elapsed, 1),
    }


def run_queries(adapter: MemoryAdapter, queries: list) -> dict:
    """Run queries and score results."""
    scorer = IronmanScorer()
    latencies = []
    
    print(f"\n  Running {len(queries)} queries...")
    
    for i, q in enumerate(queries):
        if (i + 1) % 50 == 0:
            p = sum(1 for r in scorer.results if r["pass"])
            t = len(scorer.results)
            pct = (p / t * 100) if t > 0 else 0
            print(f"    {i+1}/{len(queries)} | {pct:.1f}% ({p}/{t})")
        
        t0 = time.time()
        try:
            results = adapter.search(q["query"], max_results=5)
        except Exception as e:
            results = []
        
        latencies.append((time.time() - t0) * 1000)
        scorer.score_query(q, results)
    
    summary = scorer.summary()
    scorer.print_report(summary)
    
    if latencies:
        latencies.sort()
        n = len(latencies)
        lat = {
            "avg_ms": round(sum(latencies) / n, 1),
            "p50_ms": round(latencies[n // 2], 1),
            "p95_ms": round(latencies[int(n * 0.95)], 1),
            "p99_ms": round(latencies[int(n * 0.99)], 1),
        }
        print(f"\n  LATENCY: {lat['avg_ms']:.0f}ms avg | {lat['p50_ms']:.0f}ms P50 | {lat['p95_ms']:.0f}ms P95")
    else:
        lat = {}
    
    return {"scores": summary, "latency": lat}


def run_tier(adapter: MemoryAdapter, corpus: list, queries: list,
             tier: str) -> dict:
    """Run a single tier (day/month/year)."""
    start, end = TIER_SLICES[tier]
    tier_messages = corpus[start:end]
    
    # Filter queries: include queries from this tier and all smaller tiers
    tier_order = {"day": 0, "month": 1, "year": 2}
    tier_level = tier_order.get(tier, 2)
    tier_queries = [q for q in queries if tier_order.get(q.get("tier", "year"), 2) <= tier_level]
    if not tier_queries:
        tier_queries = queries
    
    print(f"\n{'=' * 60}")
    print(f"  TIER: {tier.upper()}")
    print(f"  Messages: {len(tier_messages)}")
    print(f"  Queries:  {len(tier_queries)}")
    print(f"{'=' * 60}")
    
    # Reset and seed
    print("  Resetting...")
    adapter.reset()
    
    seed_result = seed_system(adapter, tier_messages)
    print(f"  Seeded: {seed_result['ok']}/{seed_result['messages']} ok in {seed_result['time_sec']}s")
    
    # Stats
    stats = adapter.stats()
    if stats:
        print(f"  Stats: {stats}")
    
    # Run queries
    query_result = run_queries(adapter, tier_queries)
    
    return {
        "tier": tier,
        "seed": seed_result,
        "stats": stats,
        **query_result,
    }


def main():
    parser = argparse.ArgumentParser(description="IRONMAN Memory Benchmark v2")
    parser.add_argument("--adapter", choices=list(ADAPTERS.keys()), required=True)
    parser.add_argument("--corpus", required=True, help="Corpus JSON (array of messages)")
    parser.add_argument("--queries", required=True, help="Queries JSON file")
    parser.add_argument("--tier", choices=["day", "month", "year", "all"], default="all")
    parser.add_argument("--output", default="/tmp/ironman_results.json")
    
    # Adapter-specific args
    parser.add_argument("--url", default="http://localhost:8765", help="HMS URL")
    parser.add_argument("--gateway", default="http://localhost:18789", help="OC gateway URL")
    parser.add_argument("--token", help="OC gateway token")
    parser.add_argument("--model", default="anthropic/claude-haiku-4-5", help="OC model")
    parser.add_argument("--workspace", help="Data directory for HMS/grep")
    parser.add_argument("--skip-concurrency", action="store_true",
                        help="Skip concurrency test")
    
    args = parser.parse_args()
    
    # Build adapter
    if args.adapter == "hms":
        adapter = ADAPTERS["hms"](url=args.url, workspace=args.workspace)
    elif args.adapter == "oc":
        adapter = ADAPTERS["oc"](
            gateway_url=args.gateway, token=args.token, model=args.model
        )
    elif args.adapter == "grep":
        adapter = ADAPTERS["grep"](
            workspace=args.workspace or "/tmp/ironman-grep-data"
        )
    
    # Health check
    if not adapter.health():
        print(f"FAIL: {adapter.name} not healthy")
        return 1
    print(f"System: {adapter.name} — healthy")
    
    # Load data
    with open(args.corpus) as f:
        corpus = json.load(f)
    with open(args.queries) as f:
        queries = json.load(f)
    
    print(f"Corpus: {len(corpus)} messages")
    print(f"Queries: {len(queries)}")
    
    # Run tiers
    tiers = ["day", "month", "year"] if args.tier == "all" else [args.tier]
    all_results = {}
    
    for tier in tiers:
        start, end = TIER_SLICES[tier]
        if end is None:
            end = len(corpus)
        if len(corpus) < end:
            print(f"\n  Skipping {tier} — corpus only has {len(corpus)} messages (need {end})")
            continue
        result = run_tier(adapter, corpus, queries, tier)
        all_results[tier] = result
    
    # Save
    output = {
        "system": adapter.name,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tiers": all_results,
    }
    
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Saved: {args.output}")
    
    # Print comparison matrix if multiple tiers
    if len(all_results) > 1:
        print(f"\n{'=' * 60}")
        print(f"  TIER COMPARISON — {adapter.name}")
        print(f"{'=' * 60}")
        print(f"  {'Tier':<10} {'Accuracy':>10} {'Weighted':>10} {'Latency':>10}")
        print(f"  {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10}")
        for tier, r in all_results.items():
            o = r["scores"]["overall"]
            lat = r.get("latency", {}).get("avg_ms", 0)
            print(f"  {tier:<10} {o['accuracy']:>9.1f}% {o.get('weighted_score', 0):>9.1f}% {lat:>9.0f}ms")


if __name__ == "__main__":
    sys.exit(main() or 0)
