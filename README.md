# IRONMAN v1.0 — Universal Memory System Benchmark

**A benchmark so hard no system on earth scores 90%.**

---

IRONMAN tests what actually matters in AI memory systems: finding buried facts, understanding time, resolving contradictions, chaining multi-hop reasoning, and resisting adversarial queries. It ships with canonical test data — no generation needed — and scores systems with binary pass/fail precision.

If your memory system scores 70%+, it's exceptional. If it scores 90%, you built something that doesn't exist yet.

**Production-safe:** All benchmark data is written to isolated `/tmp/` directories. Your workspace, database, and memory files are never touched.

---

## Quick Start

### 1. Clone and Enter

```bash
git clone https://github.com/yPhi-box/ironman-benchmark.git
cd ironman-benchmark
pip install requests  # Only dependency (for HTTP adapters)
```

### 2. Run the Benchmark

Canonical test data is included in `data/`. No generation needed.

```bash
# Test HMS (Hybrid Memory Server):
python3 ironman.py --adapter hms --corpus data/corpus.json --queries data/queries.json --tier day

# Test OpenClaw native memory:
python3 ironman.py --adapter oc --corpus data/corpus.json --queries data/queries.json --tier day

# Grep baseline (sanity check):
python3 ironman.py --adapter grep --corpus data/corpus.json --queries data/queries.json --tier day

# All tiers at once:
python3 ironman.py --adapter hms --corpus data/corpus.json --queries data/queries.json --tier all
```

### 3. Read Your Results

```
   IRONMAN BENCHMARK v1.0
   System:  HMS v2.4 (all-MiniLM-L6-v2 + cross-encoder, local)
   Queries: 82

   Category          Pass  Total  Score
   ─────────────────────────────────────
   precision           22     23  95.7%
   personal            11     11 100.0%
   needle              12     13  92.3%
   synonym              5      7  71.4%
   temporal             5      5 100.0%
   contradiction        3      5  60.0%
   multi_hop            1      3  33.3%
   ─────────────────────────────────────
   OVERALL             59     82  72.0%
   Grade: S (Exceptional)

   Latency: 466ms avg
```

Results are saved to `/tmp/ironman_results.json`.

---

## Tiers

| Tier | Messages | Queries | What It Tests |
|------|----------|---------|---------------|
| `day` | 50 | 82 | Basic recall, precision — start here |
| `month` | 1,200 | 535 | Scale, temporal reasoning, contradictions |
| `year` | 14,300 | 710 | Everything at breaking point |

Start with `day`. If your system can't handle 50 messages, it won't handle 1,200.

---

## How It Works

1. **Seed** — IRONMAN writes test messages into your system via the adapter's `ingest()` method. All data goes to isolated `/tmp/` directories.
2. **Query** — Runs all queries for the selected tier and captures results.
3. **Score** — Binary pass/fail: expected answer text must appear in top-5 results.
4. **Cleanup** — Benchmark data is removed. Original state restored.

### Safety

- **HMS adapter**: Writes to `/tmp/ironman-hms-data/`, re-indexes your original workspace on cleanup.
- **OC adapter**: Writes to `/tmp/ironman-oc-workspace/`. Does NOT touch `~/.openclaw/workspace/`.
- **Grep adapter**: In-memory only. Never writes to disk.
- **Custom `--workspace`**: Must contain `/tmp/` or `ironman` in the path — rejected otherwise.

Your production data is never modified. The benchmark runs in complete isolation.

---

## Query Categories

IRONMAN tests 11 categories. Each one targets a specific failure mode:

| Category | What It Tests | Why It's Hard |
|----------|--------------|---------------|
| **precision** | Exact fact retrieval | Must return the right number, not a similar one |
| **personal** | People, relationships, ages | Names are ambiguous, relationships span files |
| **needle** | One fact buried in thousands | Classic needle-in-haystack at scale |
| **synonym** | Query uses different words than source | "kids" vs "children", "SSH" vs "remote access" |
| **temporal** | Time-aware queries | "What was the IP *last month*?" when it changed |
| **contradiction** | Conflicting info across documents | Old doc says X, new doc says Y — which wins? |
| **multi_hop** | Answer requires chaining 2+ facts | "Budget of the project led by the person who reports to X" |
| **robustness** | Typos, weird formatting, edge cases | Real users don't type perfect queries |
| **implicit** | Answer requires inference, not just retrieval | "Is X qualified for the role?" (must check requirements vs resume) |
| **negative** | Question has no answer in corpus | Must return nothing, not hallucinate |
| **adversarial** | Trick questions designed to mislead | "What's John's salary?" when no salary exists |

---

## Scoring

**Binary pass/fail.** No partial credit, no LLM-as-judge, no subjective scoring.

For each query:
1. System returns up to 5 results
2. All results are concatenated
3. Expected answer is checked via case-insensitive substring match
4. **Pass** = found. **Fail** = not found.

**Overall score** = total passed / total queries × 100%

| Grade | Score | Meaning |
|-------|-------|---------|
| **S** | 70%+ | Exceptional |
| **A** | 55–69% | Outstanding |
| **B** | 40–54% | Strong |
| **C** | 30–39% | Competitive |
| **D** | 20–29% | Below average |
| **F** | <20% | Failing |

See [SCORING.md](SCORING.md) for the full scoring rules.

---

## Canonical Test Data

The `data/` directory contains pre-generated test data to ensure all benchmarks are comparable:

| File | Contents |
|------|----------|
| `data/corpus.json` | 14,300 messages (seed 42) — fictional company "Nexus Dynamics" |
| `data/queries.json` | 710 queries across 11 categories and 3 tiers |
| `data/world_state.json` | Ground truth state for query validation |

All data is fictional. No real people, companies, or credentials. Generated deterministically with seed 42.

**Use the canonical data for published benchmarks.** If you regenerate the corpus, your results won't be directly comparable to others.

---

## Writing a Custom Adapter

To benchmark your own memory system, create an adapter in `adapters/`:

```python
from adapters.base import MemoryAdapter

class MySystemAdapter(MemoryAdapter):
    name = "My System v1.0"
    
    def __init__(self, workspace: str = None, **kwargs):
        self.workspace = workspace or "/tmp/ironman-mysystem-data"
    
    def ingest(self, message: str, timestamp: str = None):
        """Feed a single message into your system."""
        # Write to your system's ingestion API
        return {"ok": True}

    def search(self, query: str, max_results: int = 5) -> list:
        """Search and return up to max_results text chunks."""
        # Query your system and return list of dicts with 'text' key
        return [{"text": "result text", "score": 0.95}]
    
    def reset(self):
        """Clear benchmark data. Called before each tier."""
        # Clean up your /tmp/ benchmark directory
        pass
```

Register it in `adapters/__init__.py`:
```python
from .my_system import MySystemAdapter
ADAPTERS["my_system"] = MySystemAdapter
```

Then run:
```bash
python3 ironman.py --adapter my_system --corpus data/corpus.json --queries data/queries.json --tier day
```

The adapter interface is intentionally simple — `ingest()`, `search()`, and `reset()`. If your system has a REST API, it's about 20 lines of code.

---

## Published Results

Systems benchmarked with IRONMAN using canonical data:

### Day Tier (50 messages, 82 queries)
| System | Score | Grade | Latency |
|--------|-------|-------|---------|
| HMS v2.4 | 72.0% | S | 466ms |
| Hindsight | 50.0% | B | 3,080ms |
| Mem0 | 25.6% | D | 197ms |

### Month Tier (1,200 messages, 535 queries)
| System | Score | Grade | Latency |
|--------|-------|-------|---------|
| HMS v2.4 | 74.8% | S | 466ms |
| Hindsight | 72.0% | S | 4,764ms |
| Mem0 | 23.4% | D | 270ms |

### Year Tier (14,300 messages, 710 queries)
| System | Score | Grade | Latency |
|--------|-------|-------|---------|
| HMS v2.4 | 61.1% | A | ~470ms |

*Want to add your system? Run the benchmark with canonical data and submit a PR with your results.*

---

## Regenerating Test Data

If you need to regenerate (e.g., to add categories or fix queries):

```bash
# Generate conversation corpus (seed 42 for reproducibility)
python3 generate_conversations.py --days 365 --seed 42 --output data/corpus.json

# Generate queries from corpus
python3 generate_conversation_queries.py --corpus data/corpus.json --state data/world_state.json --output data/queries.json
```

**Warning:** The generators use both seeded and unseeded random calls, so output may vary slightly across Python versions. Always use the canonical `data/` files for published benchmarks.

---

## Alternative: Workspace Mode

IRONMAN also includes a workspace-style corpus generator that creates realistic `.md` files (team profiles, meeting notes, incident reports, etc.) instead of conversation messages:

```bash
python3 generate_corpus.py --scale medium --output ./corpus
python3 generate_queries.py --tier day --output queries/
python3 runner.py --adapter hms --corpus ./corpus --queries queries/day.json
```

This mode uses `runner.py` instead of `ironman.py` and works with directory-based corpora. The conversation mode (`ironman.py` + `data/`) is the primary benchmark used for published results.

---

## Requirements

- Python 3.10+
- `requests` (for HTTP-based adapters)

```bash
pip install requests
```

---

## License

MIT — benchmark anything you want.

---

*Built to prove that memory systems can be measured, not marketed.*
