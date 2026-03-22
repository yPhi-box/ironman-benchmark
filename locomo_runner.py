#!/usr/bin/env python3
"""
LoCoMo Benchmark Runner
Feeds LoCoMo conversations into memory systems and evaluates retrieval.

Uses the official LoCoMo dataset (10 conversations, 1,986 questions).
Scoring: checks if expected answer text appears in top-5 search results.

Categories:
  1 = Single-hop (find a stated fact)
  2 = Temporal (when did something happen)
  3 = Multi-hop (connect facts across turns)
  4 = Open-domain (general knowledge from conversation)
  5 = Adversarial (trick questions, unanswerable)
"""
import json
import time
import sys
import os
import re
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from adapters import ADAPTERS

CATEGORY_NAMES = {
    1: "single_hop",
    2: "temporal",
    3: "multi_hop",
    4: "open_domain",
    5: "adversarial",
}


def load_locomo(path="/tmp/locomo10.json"):
    with open(path) as f:
        return json.load(f)


def extract_turns(conversation):
    """Extract all turns from a LoCoMo conversation in order."""
    turns = []
    # Find all sessions in order
    session_nums = set()
    for k in conversation.keys():
        m = re.match(r'session_(\d+)$', k)
        if m:
            session_nums.add(int(m.group(1)))
    
    for sn in sorted(session_nums):
        session_key = f'session_{sn}'
        date_key = f'session_{sn}_date_time'
        session_date = conversation.get(date_key, '')
        session_turns = conversation.get(session_key, [])
        
        if isinstance(session_turns, list):
            for turn in session_turns:
                turns.append({
                    'speaker': turn.get('speaker', ''),
                    'text': turn.get('text', ''),
                    'dia_id': turn.get('dia_id', ''),
                    'session': sn,
                    'date': session_date,
                })
    
    return turns


def ingest_conversation(adapter, conversation):
    """Feed a LoCoMo conversation into the memory system."""
    speaker_a = conversation.get('speaker_a', 'Speaker A')
    speaker_b = conversation.get('speaker_b', 'Speaker B')
    turns = extract_turns(conversation)
    
    print(f"    Speakers: {speaker_a} & {speaker_b}")
    print(f"    Turns: {len(turns)}")
    
    ok = 0
    errors = 0
    
    for i, turn in enumerate(turns):
        # Format as natural conversation message with context
        msg = f"{turn['speaker']}: {turn['text']}"
        if turn.get('date'):
            timestamp = turn['date']
        else:
            # Generate a timestamp if none exists
            timestamp = f"2025-01-{(turn['session']):02d}T{10 + (i % 8)}:00:00"
        
        result = adapter.ingest(msg, timestamp)
        if result.get('ok'):
            ok += 1
        else:
            errors += 1
    
    # Flush/index after all turns ingested
    if hasattr(adapter, 'flush_index'):
        print("    Indexing...")
        adapter.flush_index()
    
    return {'turns': len(turns), 'ok': ok, 'errors': errors}


def build_evidence_map(conversation):
    """Build a map from dia_id (e.g., 'D1:3') to the actual text of that turn."""
    emap = {}
    session_nums = set()
    for k in conversation.keys():
        m = re.match(r'session_(\d+)$', k)
        if m:
            session_nums.add(int(m.group(1)))
    
    for sn in sorted(session_nums):
        session_turns = conversation.get(f'session_{sn}', [])
        if isinstance(session_turns, list):
            for turn in session_turns:
                dia_id = turn.get('dia_id', '')
                if dia_id:
                    emap[dia_id] = turn.get('text', '')
    return emap


def run_questions(adapter, questions, evidence_map=None):
    """Run LoCoMo questions against the memory system.
    
    Scoring: For each question, check if the retrieved chunks contain
    the text from the evidence turns. This is retrieval recall —
    did the system find the right source material?
    """
    results = []
    latencies = []
    cat_stats = {}  # category -> {passed, total}
    
    for i, q in enumerate(questions):
        if (i + 1) % 50 == 0:
            p = sum(1 for r in results if r['passed'])
            pct = p / len(results) * 100 if results else 0
            print(f"    {i+1}/{len(questions)} | {pct:.1f}%")
        
        query = q['question']
        expected = str(q.get('answer', q.get('adversarial_answer', '')))
        category = q.get('category', 0)
        cat_name = CATEGORY_NAMES.get(category, f'cat_{category}')
        evidence_ids = q.get('evidence', [])
        
        t0 = time.time()
        try:
            search_results = adapter.search(query, max_results=5)
        except:
            search_results = []
        elapsed_ms = (time.time() - t0) * 1000
        latencies.append(elapsed_ms)
        
        # Combine all retrieved text
        combined_text = " ".join(r.get('text', '') for r in search_results).lower()
        
        # For adversarial (cat 5): these are trick questions where the answer
        # is NOT in the conversation. Pass if system returns no relevant results
        # (empty results or results don't contain the adversarial answer's evidence)
        if category == 5:
            # Adversarial questions have evidence pointing to turns that DON'T
            # actually answer the question. If the system retrieves those turns,
            # it might trick the LLM into hallucinating an answer.
            # For retrieval: pass if no results returned (system correctly abstains)
            # OR if results don't contain misleading evidence.
            # Simple version: adversarial is hard to measure in retrieval-only mode.
            # Skip from scoring — same as Backboard and MemoryModel.
            passed = None  # Will be excluded from scoring
        elif evidence_map and evidence_ids:
            # Check if any evidence turn's text appears in retrieved chunks
            passed = False
            for eid in evidence_ids:
                ev_text = evidence_map.get(eid, '')
                if ev_text:
                    # Check if a significant portion of the evidence text is in results
                    # Use key phrases (first 40 chars lowercase) as the match signal
                    ev_lower = ev_text.lower().strip()
                    # Check for substantial overlap — at least the first meaningful sentence
                    ev_words = ev_lower.split()[:8]  # first 8 words
                    ev_phrase = ' '.join(ev_words)
                    if ev_phrase in combined_text:
                        passed = True
                        break
                    # Fallback: check if any 5+ consecutive word sequence from evidence
                    # appears in results
                    if len(ev_words) >= 5:
                        for start in range(len(ev_words) - 4):
                            sub = ' '.join(ev_words[start:start+5])
                            if sub in combined_text:
                                passed = True
                                break
                    if passed:
                        break
        else:
            # Fallback: exact answer string matching (old method)
            passed = expected.lower().strip() in combined_text
        
        # Track per-category (skip adversarial)
        if passed is not None:
            if cat_name not in cat_stats:
                cat_stats[cat_name] = {'passed': 0, 'total': 0}
            cat_stats[cat_name]['total'] += 1
            if passed:
                cat_stats[cat_name]['passed'] += 1
        
        results.append({
            'question': query,
            'expected': expected,
            'category': cat_name,
            'evidence': evidence_ids,
            'passed': passed,
            'latency_ms': round(elapsed_ms, 1),
            'result_count': len(search_results),
        })
    
    # Calculate overall (excluding adversarial / None)
    scored = [r for r in results if r['passed'] is not None]
    total = len(scored)
    passed = sum(1 for r in scored if r['passed'])
    accuracy = passed / total * 100 if total else 0
    
    # Latency stats (all queries including adversarial)
    latencies.sort()
    n = len(latencies)
    latency = {
        'avg_ms': round(sum(latencies) / n, 1) if n else 0,
        'p50_ms': round(latencies[n // 2], 1) if n else 0,
        'p95_ms': round(latencies[int(n * 0.95)], 1) if n else 0,
    }
    
    return {
        'total': total,
        'passed': passed,
        'accuracy': round(accuracy, 1),
        'total_with_adversarial': len(results),
        'adversarial_skipped': len(results) - total,
        'categories': {
            name: {
                'passed': s['passed'],
                'total': s['total'],
                'accuracy': round(s['passed'] / s['total'] * 100, 1) if s['total'] else 0,
            }
            for name, s in sorted(cat_stats.items())
        },
        'latency': latency,
        'details': results,
    }


def grade(accuracy):
    if accuracy >= 70: return 'S'
    if accuracy >= 55: return 'A'
    if accuracy >= 40: return 'B'
    if accuracy >= 30: return 'C'
    if accuracy >= 20: return 'D'
    return 'F'


def run_locomo(adapter, dataset, conv_indices=None, output_path=None):
    """Run the full LoCoMo benchmark."""
    if conv_indices is None:
        conv_indices = range(len(dataset))
    
    all_results = []
    
    for idx in conv_indices:
        conv_data = dataset[idx]
        conv_id = conv_data.get('sample_id', f'conv-{idx}')
        conversation = conv_data['conversation']
        questions = conv_data['qa']
        
        print(f"\n{'=' * 60}")
        print(f"  Conversation: {conv_id}")
        print(f"  Questions: {len(questions)}")
        print(f"{'=' * 60}")
        
        # Reset and ingest
        print("  Resetting...")
        adapter.reset()
        
        print("  Ingesting...")
        ingest_result = ingest_conversation(adapter, conversation)
        print(f"    Ingested: {ingest_result['ok']}/{ingest_result['turns']}")
        
        # Stats
        stats = adapter.stats()
        if stats:
            print(f"    Stats: {stats}")
        
        # Build evidence map for retrieval recall scoring
        evidence_map = build_evidence_map(conversation)
        print(f"    Evidence turns mapped: {len(evidence_map)}")
        
        # Run questions
        print("  Running questions...")
        q_result = run_questions(adapter, questions, evidence_map=evidence_map)
        
        print(f"\n  RESULT: {q_result['accuracy']}% ({q_result['passed']}/{q_result['total']}) — Grade {grade(q_result['accuracy'])}")
        for cat_name, cat_data in q_result['categories'].items():
            print(f"    {cat_name}: {cat_data['passed']}/{cat_data['total']} ({cat_data['accuracy']}%)")
        print(f"  Latency: {q_result['latency']['avg_ms']}ms avg")
        
        all_results.append({
            'conversation_id': conv_id,
            'ingest': ingest_result,
            'stats': stats,
            'results': q_result,
        })
    
    # Overall summary
    total_q = sum(r['results']['total'] for r in all_results)
    total_p = sum(r['results']['passed'] for r in all_results)
    overall_acc = total_p / total_q * 100 if total_q else 0
    
    # Per-category across all conversations
    overall_cats = {}
    for r in all_results:
        for cat, data in r['results']['categories'].items():
            if cat not in overall_cats:
                overall_cats[cat] = {'passed': 0, 'total': 0}
            overall_cats[cat]['passed'] += data['passed']
            overall_cats[cat]['total'] += data['total']
    
    # Latency across all
    all_lats = []
    for r in all_results:
        for d in r['results']['details']:
            all_lats.append(d['latency_ms'])
    all_lats.sort()
    n = len(all_lats)
    
    summary = {
        'system': adapter.name,
        'benchmark': 'LoCoMo',
        'conversations': len(all_results),
        'total_questions': total_q,
        'total_passed': total_p,
        'accuracy': round(overall_acc, 1),
        'grade': grade(overall_acc),
        'categories': {
            name: {
                'passed': d['passed'],
                'total': d['total'],
                'accuracy': round(d['passed'] / d['total'] * 100, 1) if d['total'] else 0,
            }
            for name, d in sorted(overall_cats.items())
        },
        'latency': {
            'avg_ms': round(sum(all_lats) / n, 1) if n else 0,
            'p50_ms': round(all_lats[n // 2], 1) if n else 0,
            'p95_ms': round(all_lats[int(n * 0.95)], 1) if n else 0,
        },
        'per_conversation': all_results,
    }
    
    print(f"\n{'=' * 60}")
    print(f"  LoCoMo OVERALL — {adapter.name}")
    print(f"{'=' * 60}")
    print(f"  Accuracy: {summary['accuracy']}% ({total_p}/{total_q})")
    print(f"  Grade: {summary['grade']}")
    for cat, data in summary['categories'].items():
        print(f"    {cat}: {data['accuracy']}% ({data['passed']}/{data['total']})")
    print(f"  Latency: {summary['latency']['avg_ms']}ms avg | {summary['latency']['p50_ms']}ms P50 | {summary['latency']['p95_ms']}ms P95")
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n  Saved: {output_path}")
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="LoCoMo Benchmark Runner")
    parser.add_argument("--adapter", choices=list(ADAPTERS.keys()), required=True)
    parser.add_argument("--dataset", default="/tmp/locomo10.json")
    parser.add_argument("--output", default="/tmp/locomo_results.json")
    parser.add_argument("--conversations", type=str, default="all",
                        help="Which conversations: 'all', '0', '0,1,2', '0-4'")
    
    # Adapter args
    parser.add_argument("--url", default="http://localhost:8765")
    parser.add_argument("--gateway", default="http://localhost:18789")
    parser.add_argument("--token", help="OC gateway token")
    parser.add_argument("--model", default="anthropic/claude-haiku-4-5")
    parser.add_argument("--workspace", help="Data directory")
    
    args = parser.parse_args()
    
    # Build adapter
    if args.adapter == "hms":
        adapter = ADAPTERS["hms"](url=args.url, workspace=args.workspace)
    elif args.adapter == "oc":
        adapter = ADAPTERS["oc"](workspace=args.workspace)
    elif args.adapter == "grep":
        adapter = ADAPTERS["grep"](workspace=args.workspace or "/tmp/locomo-grep")
    
    if not adapter.health():
        print(f"FAIL: {adapter.name} not healthy")
        return 1
    print(f"System: {adapter.name} — healthy")
    
    dataset = load_locomo(args.dataset)
    print(f"LoCoMo: {len(dataset)} conversations, {sum(len(c['qa']) for c in dataset)} questions")
    
    # Parse conversation indices
    if args.conversations == 'all':
        indices = list(range(len(dataset)))
    elif '-' in args.conversations:
        start, end = args.conversations.split('-')
        indices = list(range(int(start), int(end) + 1))
    else:
        indices = [int(x) for x in args.conversations.split(',')]
    
    run_locomo(adapter, dataset, conv_indices=indices, output_path=args.output)


if __name__ == "__main__":
    sys.exit(main() or 0)
