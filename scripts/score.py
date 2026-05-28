#!/usr/bin/env python3
"""Apply V2 mapping and compute accuracy + per-label breakdown."""
import json, sys
from collections import defaultdict

def remap_v2(ao):
    if not ao: return None
    raw = (ao.get('verdict_raw') or '').lower()
    adv = ao.get('adversarial_result', '')
    if raw == 'supported':
        return 'Conflicting Evidence/Cherrypicking' if adv == 'vulnerable' else 'Supported'
    if raw == 'refuted':
        return 'Refuted'
    if raw in ('unverifiable', 'not_enough_evidence', 'unknown'):
        return 'Not Enough Evidence'
    return None

records = []
path = sys.argv[1] if len(sys.argv) > 1 else 'results.jsonl'
with open(path) as f:
    for line in f:
        r = json.loads(line)
        if r.get('error'): continue
        r['_pred'] = remap_v2(r.get('agentoracle'))
        records.append(r)
records.sort(key=lambda x: x['idx'])

def score(group, name):
    per = defaultdict(lambda: {"correct": 0, "total": 0})
    total = correct = 0
    for r in group:
        gold = r['gold_label']; pred = r['_pred']
        total += 1; per[gold]['total'] += 1
        if pred == gold:
            correct += 1; per[gold]['correct'] += 1
    print(f"\n=== {name} (n={total}) ===")
    print(f"Overall: {correct/total*100:.1f}% ({correct}/{total})")
    for label, s in sorted(per.items()):
        pct = s['correct']/s['total']*100 if s['total'] else 0
        print(f"  {label:40s} {s['correct']}/{s['total']} = {pct:.1f}%")

score(records, "FULL SET")
score(records[:250], "CALIBRATION (first 250)")
score(records[250:], "HELD-OUT (last 250)")
