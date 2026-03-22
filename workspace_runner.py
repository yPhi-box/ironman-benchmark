#!/usr/bin/env python3
"""
Workspace Benchmark Runner

Feeds realistic OC workspace files into memory systems and tests retrieval.
Uses evidence-mapped questions for objective scoring.
"""
import json
import time
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from adapters import ADAPTERS

CATEGORY_NAMES = [
    "needle", "credential", "person", "temporal", "precision",
    "decision", "technical", "multi_hop", "negative",
]


def ingest_workspace(adapter, corpus_dir, tier="month"):
    """Feed workspace files into the memory system.
    
    For day tier: only static files + last day of daily files
    For month tier: static files + ~30 days of daily files  
    For year tier: everything
    """
    corpus_path = Path(corpus_dir)
    
    # Static workspace files (always included)
    static_files = ['MEMORY.md', 'TOOLS.md', 'HEARTBEAT.md', 'IDENTITY.md', 'growth-tracker.md']
    
    # Memory files sorted by date
    memory_files = sorted([
        f.name for f in (corpus_path / 'memory').glob('*.md')
    ])
    
    # Tier slicing
    if tier == "day":
        # Last 1 day + trackers
        daily_files = memory_files[-1:] if memory_files else []
        tracker_files = [f for f in memory_files if not f.startswith('20')]
    elif tier == "month":
        # Last 30 days + trackers
        daily_files = memory_files[-30:] if memory_files else []
        tracker_files = [f for f in memory_files if not f.startswith('20')]
    else:  # year
        daily_files = memory_files
        tracker_files = []  # already included in memory_files
    
    all_files_to_ingest = []
    
    # Add static files
    for sf in static_files:
        fpath = corpus_path / sf
        if fpath.exists():
            with open(fpath) as f:
                content = f.read()
            all_files_to_ingest.append((sf, content))
    
    # Add tracker files
    for tf in tracker_files:
        fpath = corpus_path / 'memory' / tf
        if fpath.exists():
            with open(fpath) as f:
                content = f.read()
            all_files_to_ingest.append((f"memory/{tf}", content))
    
    # Add daily files
    for df in daily_files:
        fpath = corpus_path / 'memory' / df
        if fpath.exists():
            with open(fpath) as f:
                content = f.read()
            all_files_to_ingest.append((f"memory/{df}", content))
    
    print(f"  Files to ingest: {len(all_files_to_ingest)}")
    
    ok = 0
    errors = 0
    
    for filename, content in all_files_to_ingest:
        # Extract date from filename if it's a daily file
        timestamp = "2026-03-20T12:00:00"  # default
        if filename.startswith("memory/2"):
            date_part = filename.replace("memory/", "").replace(".md", "")
            timestamp = f"{date_part}T12:00:00"
        
        # Ingest as a single message (the file content)
        msg = f"[File: {filename}]\n{content}"
        result = adapter.ingest(msg, timestamp)
        if result.get('ok'):
            ok += 1
        else:
            errors += 1
    
    # Flush/index
    if hasattr(adapter, 'flush_index'):
        print("  Indexing...")
        adapter.flush_index()
    
    return {'files': len(all_files_to_ingest), 'ok': ok, 'errors': errors}


def run_questions(adapter, questions):
    """Run questions and score based on evidence retrieval."""
    results = []
    latencies = []
    cat_stats = {}
    
    for i, q in enumerate(questions):
        if (i + 1) % 50 == 0:
            p = sum(1 for r in results if r['passed'])
            pct = p / len(results) * 100 if results else 0
            print(f"    {i+1}/{len(questions)} | {pct:.1f}%")
        
        query = q['question']
        expected = q['answer']
        category = q.get('category', 'unknown')
        evidence = q.get('evidence', [])
        
        t0 = time.time()
        try:
            search_results = adapter.search(query, max_results=5)
        except:
            search_results = []
        elapsed_ms = (time.time() - t0) * 1000
        latencies.append(elapsed_ms)
        
        # Combine all retrieved text
        combined_text = " ".join(r.get('text', '') for r in search_results).lower()
        
        # Score: check if evidence text appears in retrieved chunks
        passed = False
        
        if category == "negative" and not evidence:
            # Negative question with no evidence = pass if nothing relevant found
            # Check that the answer content is NOT in results
            passed = expected.lower() not in combined_text
        elif evidence:
            # Check if any evidence text snippet appears in results
            for ev in evidence:
                ev_text = ev.get('text', '').lower()
                if ev_text and ev_text in combined_text:
                    passed = True
                    break
            
            # Also check if the answer itself appears
            if not passed:
                answer_lower = expected.lower()
                # Try exact match
                if answer_lower in combined_text:
                    passed = True
                # Try key tokens (for numbers, names, etc.)
                elif len(answer_lower) < 50:
                    tokens = answer_lower.split()
                    if len(tokens) <= 3 and all(t in combined_text for t in tokens):
                        passed = True
        else:
            # No evidence mapping — fall back to answer text matching
            if expected.lower() in combined_text:
                passed = True
        
        # Track stats
        if category not in cat_stats:
            cat_stats[category] = {'passed': 0, 'total': 0}
        cat_stats[category]['total'] += 1
        if passed:
            cat_stats[category]['passed'] += 1
        
        results.append({
            'question': query,
            'expected': expected,
            'category': category,
            'passed': passed,
            'latency_ms': round(elapsed_ms, 1),
            'result_count': len(search_results),
        })
    
    # Calculate overall
    total = len(results)
    passed_count = sum(1 for r in results if r['passed'])
    accuracy = passed_count / total * 100 if total else 0
    
    latencies.sort()
    n = len(latencies)
    
    return {
        'total': total,
        'passed': passed_count,
        'accuracy': round(accuracy, 1),
        'categories': {
            name: {
                'passed': s['passed'],
                'total': s['total'],
                'accuracy': round(s['passed'] / s['total'] * 100, 1) if s['total'] else 0,
            }
            for name, s in sorted(cat_stats.items())
        },
        'latency': {
            'avg_ms': round(sum(latencies) / n, 1) if n else 0,
            'p50_ms': round(latencies[n // 2], 1) if n else 0,
            'p95_ms': round(latencies[int(n * 0.95)], 1) if n else 0,
        },
        'details': results,
    }


def grade(accuracy):
    if accuracy >= 70: return 'S'
    if accuracy >= 55: return 'A'
    if accuracy >= 40: return 'B'
    if accuracy >= 30: return 'C'
    if accuracy >= 20: return 'D'
    return 'F'


def main():
    parser = argparse.ArgumentParser(description="Workspace Benchmark Runner")
    parser.add_argument("--adapter", choices=list(ADAPTERS.keys()), required=True)
    parser.add_argument("--corpus", default="/tmp/ironman_workspace_corpus")
    parser.add_argument("--queries", default="/tmp/ironman_workspace_queries.json")
    parser.add_argument("--output", default="/tmp/workspace_results.json")
    parser.add_argument("--tier", choices=["day", "month", "year"], default="month")
    
    # Adapter args
    parser.add_argument("--url", default="http://localhost:8765")
    parser.add_argument("--gateway", default="http://localhost:18789")
    parser.add_argument("--token", help="OC gateway token")
    parser.add_argument("--workspace", help="Data directory")
    
    args = parser.parse_args()
    
    # Build adapter
    if args.adapter == "hms":
        adapter = ADAPTERS["hms"](url=args.url, workspace=args.workspace)
    elif args.adapter == "oc":
        adapter = ADAPTERS["oc"](workspace=args.workspace)
    elif args.adapter == "grep":
        adapter = ADAPTERS["grep"](workspace=args.workspace or "/tmp/workspace-grep")
    
    if not adapter.health():
        print(f"FAIL: {adapter.name} not healthy")
        return 1
    print(f"System: {adapter.name} — healthy")
    
    # Load queries
    with open(args.queries) as f:
        all_queries = json.load(f)
    
    # Filter by tier
    if args.tier == "day":
        queries = [q for q in all_queries if q.get('tier') == 'day']
    elif args.tier == "month":
        queries = [q for q in all_queries if q.get('tier') in ('day', 'month')]
    else:
        queries = all_queries
    
    print(f"Tier: {args.tier} | Queries: {len(queries)}")
    
    # Reset and ingest
    print("Resetting...")
    adapter.reset()
    
    print("Ingesting workspace...")
    ingest_result = ingest_workspace(adapter, args.corpus, tier=args.tier)
    print(f"  Ingested: {ingest_result['ok']}/{ingest_result['files']}")
    
    stats = adapter.stats()
    if stats:
        print(f"  Stats: {stats}")
    
    # Run questions
    print(f"Running {len(queries)} questions...")
    results = run_questions(adapter, queries)
    
    summary = {
        'system': adapter.name,
        'benchmark': 'IRONMAN-Workspace',
        'tier': args.tier,
        'ingest': ingest_result,
        'stats': stats,
        'results': results,
        'grade': grade(results['accuracy']),
    }
    
    print(f"\n{'=' * 60}")
    print(f"  IRONMAN-Workspace — {adapter.name} — Tier: {args.tier}")
    print(f"{'=' * 60}")
    print(f"  Accuracy: {results['accuracy']}% ({results['passed']}/{results['total']})")
    print(f"  Grade: {summary['grade']}")
    for cat, data in results['categories'].items():
        print(f"    {cat}: {data['accuracy']}% ({data['passed']}/{data['total']})")
    print(f"  Latency: {results['latency']['avg_ms']}ms avg | {results['latency']['p50_ms']}ms P50 | {results['latency']['p95_ms']}ms P95")
    
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n  Saved: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
