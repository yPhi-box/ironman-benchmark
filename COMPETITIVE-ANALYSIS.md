# IRONMAN Competitive Analysis — AI Memory Systems
## Research Date: March 21, 2026

---

## The Landscape

There are 7-8 serious memory systems for AI agents right now. Here's what we're up against.

---

## LoCoMo Benchmark Scores (LLM-as-Judge)

| System | Overall | Single-Hop | Multi-Hop | Open Domain | Temporal |
|--------|---------|------------|-----------|-------------|----------|
| Backboard | 90.0% | 89.4% | 75.0% | 91.2% | 91.9% |
| Memobase | 75.8% | 70.9% | 46.9% | 77.2% | 85.1% |
| Zep | 75.1% | 74.1% | 66.0% | 67.7% | 79.8% |
| Mem0-Graph | 68.4% | 65.7% | 47.2% | 75.7% | 58.1% |
| Mem0 | 66.9% | 67.1% | 51.2% | 72.9% | 55.5% |
| LangMem | 58.1% | 62.2% | 47.9% | 71.1% | 23.4% |
| OpenAI | 52.9% | 63.8% | 42.9% | 62.3% | 21.7% |
| **HMS v2.3** | **42.3%** | **39.0%** | **24.0%** | **44.0%** | **46.4%** |

⚠️ **HMS uses retrieval recall (top-5 chunk match). Everyone else uses LLM-as-judge scoring. NOT directly comparable.**

## LongMemEval Benchmark Scores

| System | Model | Accuracy |
|--------|-------|----------|
| Hindsight | Gemini-3 | 91.4% |
| Hindsight | OSS-120B | 89.0% |
| SuperMemory | Gemini-3 | 85.2% |
| Hindsight | OSS-20B | 83.6% |
| Letta/MemGPT | ~GPT-4o | ~83.2% |
| SuperMemory | GPT-4o | 81.6% |
| Zep | GPT-4o | 63.8% |
| Full-context | GPT-4o | 60.2% |
| Mem0 | GPT-4o | 49.0% |

---

## System Breakdown

### 1. Hindsight (vectorize.io) ⭐ TOP PERFORMER
- **Architecture**: Multi-strategy retrieval — 4 parallel strategies (semantic, BM25, graph traversal, temporal) with cross-encoder reranking
- **Memory types**: World facts, experiences, entity summaries, opinions (with confidence scores)
- **Embedding**: Local sentence-transformers or TEI (Text Embedding Inference)
- **LLM**: Required for fact extraction. Supports OpenAI, Anthropic, Gemini, Groq, Ollama, LM Studio
- **Storage**: Embedded PostgreSQL with pgvector — no external DB needed
- **Install**: `pip install hindsight-api` or Docker one-liner
- **Self-hosted**: Yes, fully local with Ollama. Single Docker command.
- **Open source**: Yes (MIT license, no feature gating)
- **Latency**: Not published, likely 100-500ms (multi-strategy + reranking)
- **Cost**: Free self-hosted. Cloud tier available.
- **Has OpenClaw plugin**: YES — published blog post about it
- **Strengths**: Highest benchmark scores, contradiction resolution, temporal awareness, open source
- **Weaknesses**: Young project (v0.4.19), requires LLM for ingestion, heavier compute

### 2. Mem0 (mem0.ai) ⭐ MOST POPULAR
- **Architecture**: Vector store + optional knowledge graph. LLM extracts facts, compares to existing memories, decides ADD/UPDATE/DELETE/NOOP
- **Embedding**: Default OpenAI text-embedding-3-small. Supports Ollama local models.
- **LLM**: Required for extraction. Default GPT-4.1-nano. Supports 16+ providers including Ollama.
- **Storage**: Qdrant (vector) + Neo4j (graph, optional). pgvector also supported.
- **Install**: `pip install mem0ai`
- **Self-hosted**: Yes, fully local with Ollama + Qdrant. Docker compose available.
- **Open source**: Yes (Apache 2.0). Graph features need Pro tier on cloud, but OSS has everything.
- **Latency**: p95 200ms (claimed)
- **Cost**: Free OSS. Cloud: free tier (10K memories), Starter $19/mo, Pro $249/mo
- **GitHub stars**: 49K+
- **Strengths**: Largest community, most integrations, contradiction handling, token efficient (90% reduction)
- **Weaknesses**: Graph features gated on cloud. Single-strategy retrieval in OSS tier. Temporal is weak (55.5%).

### 3. Zep / Graphiti ⭐ TEMPORAL SPECIALIST
- **Architecture**: Temporal knowledge graph. Episodes → entities → communities. Facts have validity windows.
- **Embedding**: OpenAI by default
- **LLM**: Required for graph construction
- **Storage**: Neo4j, FalkorDB, or Kuzu (graph DB required)
- **Install**: Graphiti (open source engine): `pip install graphiti-core`. Zep Cloud is separate.
- **Self-hosted**: Graphiti yes, but you manage the graph DB yourself. Zep Community Edition DEPRECATED.
- **Open source**: Graphiti yes (~24K stars). Zep Cloud is proprietary.
- **Latency**: <200ms retrieval (claimed)
- **Cost**: Graphiti free. Zep Cloud: 1000 free credits, then $25/mo+
- **Strengths**: Best temporal reasoning (79.8%), fact invalidation, audit trails, SOC 2 certified
- **Weaknesses**: Heavy infrastructure (Neo4j), graph processing can be slow (correct answers appear hours later after background processing), Zep CE deprecated

### 4. Letta / MemGPT ⭐ DIFFERENT APPROACH
- **Architecture**: OS-inspired memory hierarchy. Core memory (RAM) + Archival (disk) + Recall (history). Agent manages its own context.
- **Embedding**: Configurable
- **LLM**: Required — the LLM IS the memory manager
- **Storage**: PostgreSQL + pgvector
- **Install**: Docker: `docker run letta/letta:latest`
- **Self-hosted**: Yes
- **Open source**: Yes
- **Strengths**: Agent self-manages memory, learns over time, persistent agents
- **Weaknesses**: More of an agent runtime than a memory layer. Different testing paradigm — hard to benchmark as pure retrieval.

### 5. Cognee
- **Architecture**: Knowledge extraction pipeline with graph
- **Storage**: SQLite + LanceDB + Kuzu (all local, lightweight)
- **Strengths**: 30+ data connectors, multimodal (text, images, audio), fully local
- **Weaknesses**: Python only, no published benchmarks, smaller community

---

## What They ALL Have That HMS Doesn't

1. **LLM-powered fact extraction** — Every top system uses an LLM to extract structured facts from raw text during ingestion. HMS stores raw chunks.
2. **Contradiction resolution** — Mem0, Hindsight, Zep all detect when new info contradicts old info and update accordingly. HMS just adds new chunks.
3. **Knowledge graphs** — Entity relationships, not just text similarity. Enables multi-hop reasoning.
4. **Multi-strategy retrieval** — Hindsight uses 4 strategies simultaneously. HMS uses 1 (semantic + entity keyword).
5. **Temporal validity** — Zep marks facts as valid/invalid over time. HMS has no temporal awareness in storage.

## What HMS Has That They Don't

1. **Zero LLM cost** — No API calls for ingestion or retrieval. Completely free to run.
2. **Speed** — 7-9ms vs 200ms+ for the competition
3. **Simplicity** — Single Python process, SQLite, no Docker/Postgres/Neo4j/Qdrant
4. **Privacy** — Nothing leaves the machine. No cloud, no API calls.
5. **Low resources** — Runs on a Raspberry Pi. Hindsight needs PostgreSQL. Mem0 needs Qdrant. Zep needs Neo4j.

---

## IRONMAN Test Plan

### Systems to Test (Priority Order)

1. **Mem0 (self-hosted with Ollama)** — Most popular, good baseline comparison
   - Install: Orion or Atlas
   - Config: Ollama for LLM + embeddings, Qdrant for vectors
   - Adapter: `ingest()` → `memory.add()`, `search()` → `memory.search()`

2. **Hindsight** — Top performer, the target to beat
   - Install: Orion or Atlas
   - Config: Docker, Ollama for LLM, local embeddings
   - Adapter: `ingest()` → retain API, `search()` → recall API

3. **Graphiti (Zep open-source)** — Temporal specialist
   - Install: Needs Neo4j — heavier setup
   - Config: Neo4j + Graphiti
   - Adapter: `ingest()` → add_episode, `search()` → search

### Testing Approach
- Same IRONMAN corpus (conversation + workspace)
- Same queries, same scoring (SCORING.md v1.0)
- Same tiers (day/month/year)
- All 11 categories

### Important Decision: Scoring Method
Two options:
1. **Retrieval recall only** (our current method) — apples to apples with HMS
2. **LLM-as-judge** (how competitors score) — apples to apples with their published numbers

Recommend: Run BOTH. Retrieval recall for fair HMS comparison, LLM-as-judge for fair competitor comparison.

---

## Quick Reference: Installation Requirements

| System | Python | Docker | External DB | LLM API | RAM |
|--------|--------|--------|-------------|---------|-----|
| HMS v2.3 | ✅ | ❌ | ❌ | ❌ | ~256MB |
| Mem0 (local) | ✅ | Optional | Qdrant | Ollama | ~2GB |
| Hindsight | ✅ | ✅ | PostgreSQL (embedded) | Ollama/API | ~2GB |
| Graphiti | ✅ | Optional | Neo4j/FalkorDB | API | ~4GB |
| Letta | ✅ | ✅ | PostgreSQL | API | ~2GB |

---

*Last updated: March 21, 2026*
