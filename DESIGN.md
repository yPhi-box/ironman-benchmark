# IRONMAN — Universal Memory System Benchmark

## Philosophy
A memory system benchmark so hard that no system on earth currently scores 90% on any single category or overall. Not through trick questions — through testing things that genuinely matter and that current systems genuinely fail at.

When someone eventually breaks 90%, it means they built something truly exceptional.

## Scoring System

### Metrics
1. **Accuracy@K** — Is the answer in the top K results? (K=1, K=3, K=5)
2. **MRR (Mean Reciprocal Rank)** — How high does the right answer rank? (1/rank, averaged)
3. **NDCG@5** — Normalized Discounted Cumulative Gain — penalizes correct answers buried low
4. **Latency** — P50, P95, P99 at each scale tier
5. **Consistency** — Same query, same results every time?

### Category Scores
Each category scored independently (0-100%). Overall score = weighted average.
A system must score ≥90% in a category AND overall to "pass" that tier.

### Scale Tiers
- **Small**: 100 files / ~500 chunks — baseline sanity
- **Medium**: 1,000 files / ~5,000 chunks — real workspace
- **Large**: 10,000 files / ~50,000 chunks — enterprise scale
- **Stress**: 50,000+ files / ~250,000 chunks — break everything

## Test Categories (18 categories)

### 1. NEEDLE (weight: 8%)
Find one specific fact buried in massive corpus.
- Single fact in 50,000 chunks
- Fact placed at random depth
- Query uses different wording than source

### 2. TEMPORAL (weight: 8%)
Understand time — what was true when?
- "What was X's role in January 2024?" (they changed roles in March)
- "When did the policy change?"
- Files have dates, facts evolve across dated documents

### 3. CONTRADICTION (weight: 8%)
Same topic, conflicting information across documents/time.
- "What is the server IP?" when it was changed and both docs exist
- Must return CURRENT/LATEST, not just any match
- Explicit version tracking: v1 says A, v2 says B

### 4. MULTI-HOP (weight: 10%)
Answer requires chaining 2-4 facts across different files.
- "What is the budget of the project led by the person who reports to X?"
- "Which team member's child attends the same school as Y's kid?"
- Each hop is in a DIFFERENT file

### 5. DISAMBIGUATION (weight: 7%)
Same name, different entities.
- Multiple "John Chen" across the corpus (different people, different departments)
- "David Kim the engineer" vs "David Kim the customer"
- Context clues must disambiguate

### 6. FRAGMENTATION (weight: 6%)
Answer split across chunk boundaries.
- Fact starts in one chunk, completes in the next
- Question + answer in different sections of same document
- Headers in one chunk, data in another

### 7. SYNONYMS (weight: 5%)
Completely different words, same meaning.
- "remuneration" → salary → pay → compensation → comp
- "terminated" → fired → let go → departed → separated
- Domain-specific jargon vs plain language

### 8. ADVERSARIAL (weight: 7%)
Queries designed to confuse.
- Negation: "Who is NOT on the security team?"
- Misdirection: "What is Maya's dog's name?" (Maya has cats, not dogs)
- Presupposition: "When did they move to London?" (they didn't)

### 9. PRECISION (weight: 6%)
Return the RIGHT results, not just RELATED ones.
- "Q4 2024 revenue" should not return Q3 2024 revenue
- "Server 7 config" should not return Server 8 config
- Must distinguish between similar but distinct facts

### 10. QUANTITATIVE (weight: 5%)
Requires comparing numerical values.
- "Which project has the largest budget?"
- "Who has the most experience?"
- "What was the highest-severity incident?"

### 11. NEGATIVE (weight: 5%)
Correctly identify when information does NOT exist.
- "What is the stock ticker?" (private company)
- "When is the IPO?" (never mentioned)
- Should return low-confidence results or empty

### 12. IMPLICIT (weight: 5%)
Information not stated directly, must be inferred.
- "Is X married?" (file says "X's wife Y..." but never says "married")
- "Does the company offer health insurance?" (benefits doc lists Aetna PPO)
- Derived from context, not keyword match

### 13. LONG-RANGE (weight: 5%)
Answer requires context from distant parts of a long document.
- 5,000-word document, answer at top, qualifier at bottom
- "What was the decision?" requires reading both the proposal AND conclusion
- Cross-section references within single large files

### 14. RECENCY (weight: 5%)
Recent information should rank higher than old.
- Same topic discussed in 2023, 2024, 2025 — latest should win
- Recently modified files vs stale ones
- Breaking news vs historical record

### 15. ROBUSTNESS (weight: 3%)
Handles garbage input gracefully.
- Typos, misspellings, Unicode, emoji, SQL injection, XSS
- Empty queries, null bytes, 10KB queries
- Doesn't crash, doesn't return nonsense

### 16. CONSISTENCY (weight: 2%)
Same query → same results, every time.
- Run same 100 queries 3 times, compare results
- Reindex → same results
- No random drift

### 17. THROUGHPUT (weight: 3%)
Raw performance under load.
- Single-thread latency distribution
- 10/50/100 concurrent threads
- QPS at each scale tier

### 18. CROSS-DOCUMENT (weight: 5%)
Facts that span multiple files must be synthesized.
- Person file + project file + meeting file = full picture
- "What projects is X working on?" requires checking project files, not just person file
- Timeline reconstruction from multiple daily notes

## Data Corpus

### Structure
Simulates a realistic multi-year corporate workspace:

```
workspace/
├── company/           — About, policies, benefits, org chart
├── team/              — Individual profiles (200+ people)
├── projects/          — 50+ projects with timelines, updates
├── meetings/          — 500+ meeting notes
├── incidents/         — 100+ incident reports
├── docs/              — Technical documentation
├── memory/            — Daily notes (365+ days)
├── creative/          — Fiction, blog posts, personal writing
├── customers/         — 100+ customer profiles
├── infrastructure/    — Server configs, credentials, runbooks
├── finance/           — Budgets, forecasts, reports
├── hiring/            — Job postings, interview notes
├── legal/             — Contracts, compliance, policies
└── archive/           — Old versions of changed documents
```

### Scale
- Target: 1,000-10,000 files
- 50,000-250,000 chunks
- Temporal span: 3 years of history
- 200+ named entities (people, companies, projects)
- Deliberate contradictions between archive/ and current files
- Multiple people with similar/identical names

### Key Properties
1. **No real personal data** — everything synthetic
2. **Internally consistent** — cross-references work
3. **Temporally coherent** — events flow logically through time
4. **Deliberately hard** — designed to expose every weakness

## Adapter Interface

```python
class MemorySystemAdapter:
    """Interface for testing any memory system."""
    
    def index(self, directory: str, **kwargs) -> dict:
        """Index a directory of files. Returns stats."""
        raise NotImplementedError
    
    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Search and return results with text and scores."""
        raise NotImplementedError
    
    def clear(self) -> None:
        """Clear all indexed data."""
        raise NotImplementedError
    
    def stats(self) -> dict:
        """Return index statistics."""
        raise NotImplementedError
```

Built-in adapters:
- HMS (HTTP API)
- OpenAI embeddings + pgvector
- Raw file search (baseline)
- (extensible for Pinecone, Weaviate, etc.)

## Output

JSON report with:
- Per-category scores (accuracy, MRR, NDCG)
- Per-query pass/fail with expected vs actual
- Latency distribution
- Scale tier results
- Overall weighted score
- Comparison table if multiple adapters tested
