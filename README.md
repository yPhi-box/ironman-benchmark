# IRONMAN — Universal Memory System Benchmark

**A benchmark so hard no system on earth scores 90%.**

---

IRONMAN tests what actually matters in AI memory systems: finding buried facts, understanding time, resolving contradictions, chaining multi-hop reasoning, and resisting adversarial queries. It generates synthetic but realistic data — no PII, no real conversations — and scores systems with binary pass/fail precision.

If your memory system scores 70%+, it's exceptional. If it scores 90%, you built something that doesn't exist yet.

---

## Quick Start

### 1. Generate a Test Corpus

```bash
python3 generate_corpus.py --tier day --output corpus/
```

**Tiers:**
| Tier | Messages | Queries | What It Tests |
|------|----------|---------|---------------|
| `day` | 50 | 82 | Basic recall, precision |
| `month` | 1,200 | 535 | Scale, temporal, contradiction |
| `year` | 3,600 | 710 | Everything at breaking point |

Start with `day`. If your system can't handle 50 messages, it won't handle 1,200.

### 2. Generate Queries

```bash
python3 generate_queries.py --tier day --output queries/
```

### 3. Ingest the Corpus Into Your System

Point your memory system at the generated corpus files. How you do this depends on your system:

- **HMS:** `curl -X POST http://localhost:8765/index -H 'Content-Type: application/json' -d '{"directory": "corpus/", "force": true}'`
- **OpenClaw native:** Copy files to `~/.openclaw/workspace/memory/`
- **Custom system:** Use the adapter interface (see below)

### 4. Run the Benchmark

```bash
python3 runner.py --adapter hms --tier day --corpus corpus/ --queries queries/
```

**Built-in adapters:**
- `hms` — HMS (Hybrid Memory Server) via HTTP API
- `oc` — OpenClaw native memory via gateway
- `grep` — Baseline grep search (sanity check)

### 5. Read Your Results

```
   IRONMAN BENCHMARK
   Tier: day | Queries: 82

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

## Writing a Custom Adapter

To benchmark your own memory system, create an adapter in `adapters/`:

```python
from adapters.base import BaseAdapter

class MySystemAdapter(BaseAdapter):
    def ingest(self, file_path: str, content: str):
        """Ingest a single document into your system."""
        # Send content to your system's ingestion API
        pass

    def search(self, query: str, max_results: int = 5) -> list[str]:
        """Search and return up to max_results text chunks."""
        # Query your system and return list of result strings
        return ["result 1 text", "result 2 text"]
```

Then run:
```bash
python3 runner.py --adapter my_system --tier day
```

The adapter interface is intentionally simple — `ingest()` and `search()`. If your system has a REST API, it's about 20 lines of code.

---

## Corpus Design

The generated corpus simulates a realistic OpenClaw workspace for a fictional company (**Nexus Dynamics**). It includes:

- **Team profiles** — names, roles, ages, relationships, backgrounds
- **Meeting notes** — decisions, action items, attendees
- **Infrastructure docs** — IPs, credentials, configs, architecture
- **Incident reports** — timelines, root causes, remediation
- **Policy documents** — benefits, PTO, security policies
- **Daily journals** — timestamped personal notes
- **Archived docs** — outdated versions that contradict current ones

All data is fictional. No real people, companies, or credentials.

See [DESIGN.md](DESIGN.md) for the full benchmark philosophy and category specifications.

---

## Published Results

Systems benchmarked with IRONMAN:

### Day Tier (50 messages, 82 queries)
| System | Score | Grade | Latency |
|--------|-------|-------|---------|
| HMS v2.4 | 72.0% | S | 466ms |
| Hindsight | 50.0% | B | 3,080ms |
| Mem0 | 25.6% | D | 197ms |
| OpenClaw native | 63.6% | A | 2,408ms |

### Month Tier (1,200 messages, 535 queries)
| System | Score | Grade | Latency |
|--------|-------|-------|---------|
| HMS v2.4 | 74.8% | S | 466ms |
| Hindsight | 72.0% | S | 4,764ms |
| Mem0 | 23.4% | D | 270ms |

### Year Tier (3,600 messages, 710 queries)
| System | Score | Grade | Latency |
|--------|-------|-------|---------|
| HMS v2.4 | 61.1% | A | ~470ms |

*Want to add your system? Run the benchmark and submit a PR with your results.*

---

## Requirements

- Python 3.10+
- No external dependencies for corpus generation and scoring
- Adapters may require `requests` for HTTP-based systems

```bash
pip install requests  # Only if using HTTP adapters
```

---

## License

MIT — benchmark anything you want.

---

*Built to prove that memory systems can be measured, not marketed.*
