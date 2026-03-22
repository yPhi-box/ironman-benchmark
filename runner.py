#!/usr/bin/env python3
"""
IRONMAN Benchmark Runner v2
Universal runner — works with HMS, OpenClaw, grep, or any adapter.

Usage:
    python3 runner.py --adapter hms --url http://localhost:8765
    python3 runner.py --adapter oc
    python3 runner.py --adapter grep --corpus /tmp/ironman-corpus
"""
import argparse
import json
import time
import sys
import os
import subprocess
import re
import concurrent.futures
import random
from pathlib import Path
from typing import List, Dict

from scorer import IronmanScorer


# ============================================================================
# ADAPTERS
# ============================================================================

class MemoryAdapter:
    """Base adapter. Subclass and implement search()."""
    name = "base"
    
    def index(self, directory: str, **kwargs) -> dict:
        return {}
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """Must return list of dicts with 'text' (FULL content)."""
        raise NotImplementedError
    
    def clear(self) -> None:
        pass
    
    def stats(self) -> dict:
        return {}
    
    def health(self) -> bool:
        return True


class HMSAdapter(MemoryAdapter):
    """HMS via HTTP API."""
    name = "HMS (all-MiniLM-L6-v2, local)"
    
    def __init__(self, url: str = "http://localhost:8765"):
        import requests
        self.url = url.rstrip("/")
        self.session = requests.Session()
    
    def index(self, directory: str, **kwargs) -> dict:
        r = self.session.post(f"{self.url}/index", json={
            "directory": directory, "pattern": "**/*.md", "force": True
        }, timeout=300)
        return r.json()
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        r = self.session.post(f"{self.url}/search", json={
            "query": query, "max_results": max_results
        }, timeout=30)
        if r.status_code == 200:
            return r.json().get("results", [])
        return []
    
    def clear(self) -> None:
        # Delete DB files, restart service
        hms_dir = os.path.expanduser("~/hms")
        for f in ["memory.db", "memory.hnsw", "memory.hnsw2"]:
            p = os.path.join(hms_dir, f)
            if os.path.exists(p):
                os.remove(p)
    
    def stats(self) -> dict:
        r = self.session.get(f"{self.url}/stats", timeout=10)
        return r.json()
    
    def health(self) -> bool:
        try:
            r = self.session.get(f"{self.url}/health", timeout=5)
            return r.status_code == 200
        except:
            return False


class OCAdapter(MemoryAdapter):
    """OpenClaw native memory via CLI. Run ON the OC machine (no SSH)."""
    name = "OpenClaw Native (text-embedding-3-small)"
    
    def __init__(self):
        pass
    
    def index(self, directory: str, **kwargs) -> dict:
        r = subprocess.run("openclaw memory index --force",
                          shell=True, capture_output=True, text=True, timeout=300)
        return {"output": r.stdout}
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        safe = query.replace("'", "'\\''")
        cmd = f"openclaw memory search --max-results {max_results} '{safe}'"
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            output = r.stdout + r.stderr
        except:
            return []
        
        if "No matches" in output:
            return []
        
        results = []
        blocks = re.split(r'\n(?=\d+\.\d+ )', output.strip())
        for block in blocks:
            m = re.match(r'(\d+\.\d+)\s+(\S+):(\d+)-(\d+)\n(.*)', block, re.DOTALL)
            if m:
                results.append({
                    "text": m.group(5).strip(),  # Full text returned by OC
                    "score": float(m.group(1)),
                    "file_path": m.group(2),
                })
        return results[:max_results]
    
    def stats(self) -> dict:
        r = subprocess.run("openclaw memory status",
                          shell=True, capture_output=True, text=True, timeout=10)
        chunks = files = 0
        for line in r.stdout.split('\n'):
            m = re.search(r'(\d+)/(\d+) files.*?(\d+) chunks', line)
            if m:
                files = int(m.group(2))
                chunks = int(m.group(3))
        return {"files": files, "total_chunks": chunks}
    
    def health(self) -> bool:
        r = subprocess.run("openclaw memory status",
                          shell=True, capture_output=True, text=True, timeout=10)
        return "ready" in r.stdout.lower()


class GrepAdapter(MemoryAdapter):
    """Grep baseline. Returns full file content for fair comparison."""
    name = "grep (baseline)"
    
    def __init__(self):
        self.files = {}
    
    def index(self, directory: str, **kwargs) -> dict:
        self.files = {}
        for p in Path(directory).rglob("*.md"):
            self.files[str(p)] = p.read_text(errors="ignore")
        return {"files": len(self.files)}
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        if not query.strip():
            return []
        words = query.lower().split()
        results = []
        for path, text in self.files.items():
            text_lower = text.lower()
            score = sum(1 for w in words if w in text_lower) / max(len(words), 1)
            if score > 0:
                results.append({
                    "text": text,  # Full file content — same as what OC/HMS return
                    "score": score,
                    "file_path": path,
                })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:max_results]
    
    def health(self) -> bool:
        return True


ADAPTERS = {"hms": HMSAdapter, "oc": OCAdapter, "grep": GrepAdapter}


# ============================================================================
# RUNNER
# ============================================================================

class IronmanRunner:
    
    def __init__(self, adapter: MemoryAdapter, queries: List[dict],
                 corpus_dir: str = None):
        self.adapter = adapter
        self.queries = queries
        self.corpus_dir = corpus_dir
        self.scorer = IronmanScorer()
        self.latencies = []
    
    def run(self, skip_index: bool = False, skip_concurrency: bool = False) -> dict:
        print(f"\n{'=' * 60}")
        print(f"  IRONMAN BENCHMARK")
        print(f"  System:  {self.adapter.name}")
        print(f"  Queries: {len(self.queries)}")
        if self.corpus_dir:
            print(f"  Corpus:  {self.corpus_dir}")
        print(f"{'=' * 60}")
        
        results = {}
        
        # Health
        if not self.adapter.health():
            print("  FAIL: System not healthy")
            return {"error": "not healthy"}
        
        # Index
        if not skip_index and self.corpus_dir:
            print(f"\n  Indexing...")
            t0 = time.time()
            idx = self.adapter.index(self.corpus_dir)
            results["index_time_sec"] = round(time.time() - t0, 1)
            print(f"  Indexed in {results['index_time_sec']}s")
        
        # Stats
        stats = self.adapter.stats()
        results["stats"] = stats
        if stats:
            print(f"  Stats: {stats}")
        
        # Run queries
        print(f"\n  Running {len(self.queries)} queries...")
        for i, q in enumerate(self.queries):
            if (i + 1) % 50 == 0:
                p = sum(1 for r in self.scorer.results if r["pass"])
                t = len(self.scorer.results)
                pct = (p / t * 100) if t > 0 else 0
                print(f"    {i+1}/{len(self.queries)} | {pct:.1f}% ({p}/{t})")
            
            t0 = time.time()
            try:
                sr = self.adapter.search(q["query"], max_results=5)
            except Exception as e:
                sr = []
            self.latencies.append((time.time() - t0) * 1000)
            self.scorer.score_query(q, sr)
        
        # Latency
        if self.latencies:
            self.latencies.sort()
            n = len(self.latencies)
            results["latency"] = {
                "avg_ms": round(sum(self.latencies) / n, 1),
                "p50_ms": round(self.latencies[n // 2], 1),
                "p95_ms": round(self.latencies[int(n * 0.95)], 1),
                "p99_ms": round(self.latencies[int(n * 0.99)], 1),
            }
        
        # Concurrency (skip for CLI-based adapters)
        if not skip_concurrency:
            print(f"\n  Concurrency test...")
            results["concurrency"] = self._concurrency(10, 50)
        
        # Report
        summary = self.scorer.summary()
        results["scores"] = summary
        self.scorer.print_report(summary)
        
        lat = results.get("latency", {})
        print(f"\n  LATENCY: {lat.get('avg_ms',0):.0f}ms avg | {lat.get('p50_ms',0):.0f}ms P50 | {lat.get('p95_ms',0):.0f}ms P95")
        
        if "concurrency" in results:
            c = results["concurrency"]
            print(f"  CONCURRENCY: {c.get('qps',0):.0f} QPS | {c.get('errors',0)} errors")
        
        return results
    
    def _concurrency(self, threads: int = 10, per_thread: int = 50) -> dict:
        sample = [q["query"] for q in self.queries[:100]]
        all_lats = []
        errors = [0]
        
        def worker(_):
            lats = []
            for _ in range(per_thread):
                try:
                    t0 = time.time()
                    self.adapter.search(random.choice(sample), max_results=5)
                    lats.append((time.time() - t0) * 1000)
                except:
                    errors[0] += 1
            return lats
        
        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as pool:
            for lats in pool.map(worker, range(threads)):
                all_lats.extend(lats)
        wall = time.time() - t0
        
        total = threads * per_thread
        return {
            "threads": threads,
            "total_queries": total,
            "wall_sec": round(wall, 1),
            "qps": round(total / wall, 0) if wall > 0 else 0,
            "errors": errors[0],
        }


def main():
    parser = argparse.ArgumentParser(description="IRONMAN Memory Benchmark")
    parser.add_argument("--adapter", choices=list(ADAPTERS.keys()), required=True)
    parser.add_argument("--url", default="http://localhost:8765", help="HMS URL")
    parser.add_argument("--corpus", help="Corpus directory (for indexing)")
    parser.add_argument("--queries", required=True, help="Queries JSON file")
    parser.add_argument("--output", default="/tmp/ironman_results.json")
    parser.add_argument("--skip-index", action="store_true")
    parser.add_argument("--skip-concurrency", action="store_true",
                        help="Skip concurrency test (use for CLI adapters)")
    args = parser.parse_args()
    
    # Build adapter
    if args.adapter == "hms":
        adapter = HMSAdapter(args.url)
    elif args.adapter == "oc":
        adapter = OCAdapter()
    elif args.adapter == "grep":
        adapter = GrepAdapter()
    
    with open(args.queries) as f:
        queries = json.load(f)
    
    runner = IronmanRunner(adapter, queries, corpus_dir=args.corpus)
    results = runner.run(
        skip_index=args.skip_index,
        skip_concurrency=args.skip_concurrency
    )
    
    results["system"] = adapter.name
    results["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Saved: {args.output}")


if __name__ == "__main__":
    main()
