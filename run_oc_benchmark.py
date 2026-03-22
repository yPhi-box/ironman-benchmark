#!/usr/bin/env python3
"""Quick Ironman accuracy run against OpenClaw native memory."""
import json
import time
import sys
from oc_adapter import OCMemoryAdapter
from scorer import IronmanScorer

def main():
    adapter = OCMemoryAdapter(ssh_target="atlas@192.168.1.41")
    
    print("Checking OC health...")
    if not adapter.health():
        print("OC not healthy!")
        return 1
    
    stats = adapter.stats()
    print(f"OC Memory: {stats['files']} files, {stats['total_chunks']} chunks")
    
    # Load queries
    with open("/tmp/ironman-queries.json") as f:
        queries = json.load(f)
    
    print(f"\nRunning {len(queries)} queries against OpenClaw native memory...")
    print("(This will be slow — each query is an SSH + CLI call)\n")
    
    scorer = IronmanScorer()
    latencies = []
    errors = 0
    
    for i, q in enumerate(queries):
        if (i + 1) % 25 == 0:
            passed = sum(1 for r in scorer.results if r["pass"])
            total = len(scorer.results)
            pct = (passed / total * 100) if total > 0 else 0
            print(f"  Progress: {i + 1}/{len(queries)} | Running accuracy: {pct:.1f}% ({passed}/{total})")
        
        t0 = time.time()
        try:
            results = adapter.search(q["query"], max_results=5)
        except Exception as e:
            results = []
            errors += 1
        
        latency = (time.time() - t0) * 1000
        latencies.append(latency)
        scorer.score_query(q, results)
    
    # Print report
    summary = scorer.summary()
    scorer.print_report(summary)
    
    if latencies:
        latencies.sort()
        n = len(latencies)
        print(f"\n  LATENCY (includes SSH overhead)")
        print(f"  Avg: {sum(latencies)/n:.0f}ms, P50: {latencies[n//2]:.0f}ms, P95: {latencies[int(n*0.95)]:.0f}ms")
        print(f"  Errors: {errors}")
    
    # Save
    output = {
        "system": adapter.name,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scores": summary,
        "query_count": len(queries),
        "index_stats": stats,
    }
    with open("/tmp/ironman_oc_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n  Results saved to /tmp/ironman_oc_results.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
