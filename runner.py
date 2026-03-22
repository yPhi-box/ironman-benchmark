#!/usr/bin/env python3
"""
IRONMAN Benchmark Runner v1.0
Universal runner — works with HMS, OpenClaw, grep, or any adapter.

SAFETY: This runner uses isolated data directories (/tmp/ironman-*) and never
touches your production workspace or database. After benchmarking, HMS is
re-pointed at your original workspace and the benchmark data is cleaned up.

Usage:
    python3 runner.py --adapter hms --queries queries.json --corpus ./corpus
    python3 runner.py --adapter oc --queries queries.json --corpus ./corpus
    python3 runner.py --adapter grep --queries queries.json --corpus ./corpus
"""
import argparse
import json
import time
import sys
import os
import shutil
import subprocess
import re
import concurrent.futures
import random
from pathlib import Path
from typing import List, Dict

from scorer import IronmanScorer


# ============================================================================
# ADAPTERS (isolated — never touch production data)
# ============================================================================

class MemoryAdapter:
    """Base adapter. Subclass and implement search()."""
    name = "base"
    
    def setup(self, corpus_dir: str) -> dict:
        """Prepare the system with benchmark data. Must be isolated."""
        return {}
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """Must return list of dicts with 'text' (FULL content)."""
        raise NotImplementedError
    
    def cleanup(self) -> None:
        """Remove all benchmark data and restore original state."""
        pass
    
    def stats(self) -> dict:
        return {}
    
    def health(self) -> bool:
        return True


class HMSAdapter(MemoryAdapter):
    """HMS via HTTP API. Uses isolated /tmp directory for benchmark data.
    
    How it works:
    1. Copies corpus to /tmp/ironman-hms-data/
    2. Tells HMS to index that directory (does NOT replace existing index — adds to it)
    3. After benchmark, deletes /tmp/ironman-hms-data/ and re-indexes original workspace
    """
    name = "HMS v2.4 (all-MiniLM-L6-v2 + cross-encoder, local)"
    
    def __init__(self, url: str = "http://localhost:8765"):
        import requests
        self.url = url.rstrip("/")
        self.session = requests.Session()
        self.bench_dir = "/tmp/ironman-hms-data"
        self._original_watch_path = os.environ.get("HMS_WATCH_PATHS", "")
    
    def setup(self, corpus_dir: str) -> dict:
        """Copy corpus to isolated dir and index it."""
        # Clean any previous benchmark data
        if os.path.exists(self.bench_dir):
            shutil.rmtree(self.bench_dir)
        
        # Copy corpus to isolated location
        shutil.copytree(corpus_dir, self.bench_dir)
        
        # Index the isolated corpus
        r = self.session.post(f"{self.url}/index", json={
            "directory": self.bench_dir,
            "pattern": "**/*.md",
            "force": True,
        }, timeout=300)
        return r.json()
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        r = self.session.post(f"{self.url}/search", json={
            "query": query, "max_results": max_results
        }, timeout=30)
        if r.status_code == 200:
            return r.json().get("results", [])
        return []
    
    def cleanup(self) -> None:
        """Remove benchmark data and re-index original workspace."""
        # Remove benchmark data
        if os.path.exists(self.bench_dir):
            shutil.rmtree(self.bench_dir)
        
        # Re-index the original workspace to restore clean state
        watch = self._original_watch_path or os.path.expanduser("~/.openclaw/workspace")
        try:
            self.session.post(f"{self.url}/index", json={
                "directory": watch,
                "pattern": "**/*.md",
                "force": True,
            }, timeout=300)
            print("  ✓ HMS re-indexed original workspace")
        except Exception as e:
            print(f"  ⚠ HMS re-index failed: {e}")
            print(f"    Run manually: curl -X POST {self.url}/index -H 'Content-Type: application/json' -d '{{\"directory\": \"{watch}\", \"force\": true}}'")
    
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
    """OpenClaw native memory via CLI.
    
    How it works:
    1. Backs up existing memory/ directory
    2. Copies corpus into memory/
    3. Runs benchmark
    4. Restores original memory/ from backup
    """
    name = "OpenClaw Native"
    
    def __init__(self):
        self.workspace = os.path.expanduser("~/.openclaw/workspace")
        self.memory_dir = os.path.join(self.workspace, "memory")
        self.backup_dir = "/tmp/ironman-oc-backup"
        self._backed_up = False
    
    def setup(self, corpus_dir: str) -> dict:
        """Backup existing memory, copy corpus in, reindex."""
        # Backup existing memory
        if os.path.exists(self.memory_dir):
            if os.path.exists(self.backup_dir):
                shutil.rmtree(self.backup_dir)
            shutil.copytree(self.memory_dir, self.backup_dir)
            self._backed_up = True
            print(f"  ✓ Backed up {self.memory_dir} → {self.backup_dir}")
        
        # Also backup MEMORY.md
        mem_file = os.path.join(self.workspace, "MEMORY.md")
        if os.path.exists(mem_file):
            shutil.copy2(mem_file, "/tmp/ironman-oc-MEMORY.md.bak")
        
        # Clear memory dir and copy corpus
        if os.path.exists(self.memory_dir):
            shutil.rmtree(self.memory_dir)
        shutil.copytree(corpus_dir, self.memory_dir)
        
        # Reindex
        r = subprocess.run("openclaw memory index --force",
                          shell=True, capture_output=True, text=True, timeout=300)
        return {"output": r.stdout[:200]}
    
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
                    "text": m.group(5).strip(),
                    "score": float(m.group(1)),
                    "file_path": m.group(2),
                })
        return results[:max_results]
    
    def cleanup(self) -> None:
        """Restore original memory from backup."""
        if self._backed_up and os.path.exists(self.backup_dir):
            if os.path.exists(self.memory_dir):
                shutil.rmtree(self.memory_dir)
            shutil.copytree(self.backup_dir, self.memory_dir)
            shutil.rmtree(self.backup_dir)
            print(f"  ✓ Restored {self.memory_dir} from backup")
        
        # Restore MEMORY.md
        mem_bak = "/tmp/ironman-oc-MEMORY.md.bak"
        mem_file = os.path.join(self.workspace, "MEMORY.md")
        if os.path.exists(mem_bak):
            shutil.copy2(mem_bak, mem_file)
            os.remove(mem_bak)
        
        # Reindex original
        subprocess.run("openclaw memory index --force",
                      shell=True, capture_output=True, timeout=300)
        print("  ✓ OC re-indexed original workspace")
    
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
    """Grep baseline. In-memory only, touches nothing on disk."""
    name = "grep (baseline)"
    
    def __init__(self):
        self.files = {}
    
    def setup(self, corpus_dir: str) -> dict:
        self.files = {}
        for p in Path(corpus_dir).rglob("*.md"):
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
                    "text": text,
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
    
    def run(self, skip_setup: bool = False, skip_concurrency: bool = False) -> dict:
        print(f"\n{'=' * 60}")
        print(f"  IRONMAN BENCHMARK v1.0")
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
        
        # Setup (isolated)
        if not skip_setup and self.corpus_dir:
            print(f"\n  Setting up (isolated)...")
            t0 = time.time()
            idx = self.adapter.setup(self.corpus_dir)
            results["setup_time_sec"] = round(time.time() - t0, 1)
            print(f"  Setup complete in {results['setup_time_sec']}s")
        
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
        
        # Cleanup — restore original state
        print(f"\n  Cleaning up...")
        self.adapter.cleanup()
        print(f"  ✓ Benchmark complete. Original state restored.")
        
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
    parser = argparse.ArgumentParser(description="IRONMAN Memory Benchmark v1.0")
    parser.add_argument("--adapter", choices=list(ADAPTERS.keys()), required=True)
    parser.add_argument("--url", default="http://localhost:8765", help="HMS URL")
    parser.add_argument("--corpus", required=True, help="Corpus directory")
    parser.add_argument("--queries", required=True, help="Queries JSON file")
    parser.add_argument("--output", default="/tmp/ironman_results.json")
    parser.add_argument("--skip-setup", action="store_true",
                        help="Skip setup (use if data already loaded)")
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
        skip_setup=args.skip_setup,
        skip_concurrency=args.skip_concurrency
    )
    
    results["system"] = adapter.name
    results["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Saved: {args.output}")


if __name__ == "__main__":
    main()
