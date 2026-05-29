#!/usr/bin/env python3
"""Apply V2 verdict mapping and compute accuracy + per-label breakdown.

Canonical input shape (runner.py output, one row per claim):
  {
    "claim_id": int,        # alias: "idx" (legacy)
    "claim": str,
    "gold_label": str,      # AVeriTeC ground truth
    "predicted_label": str, # runner's pre-computed AVeriTeC mapping (may be re-derived)
    "agentoracle": {
        "verdict_raw": str,            # supported|refuted|unverifiable|unknown
        "verdict_mapped": str,
        "recommendation": str,         # act|verify|reject|abstain
        "confidence_overall": float,
        "confidence_claim": float,
        "adversarial_result": str,     # vulnerable|resilient|not_checked
        "adversarial_flags": [str]
    },
    "error": str | null,
    ...
  }

Canonical verdict source: `agentoracle.verdict_raw` (truth label). The
`recommendation` field is the binary act/halt gate and is preserved as receipt
metadata; it is NOT used for label-level accuracy. This separation keeps the
harness reproducible across spec revisions to the halt threshold.
"""
import json, sys
from collections import defaultdict


def remap_v2(ao):
    """AVeriTeC label from raw verdict + adversarial signal. Single source of truth."""
    if not ao:
        return None
    raw = (ao.get('verdict_raw') or '').lower()
    adv = (ao.get('adversarial_result') or '').lower()
    if raw == 'supported':
        return 'Conflicting Evidence/Cherrypicking' if adv == 'vulnerable' else 'Supported'
    if raw == 'refuted':
        return 'Refuted'
    if raw in ('unverifiable', 'not_enough_evidence', 'unknown', ''):
        return 'Not Enough Evidence'
    return None


def _row_id(r):
    """Accept either canonical claim_id or legacy idx."""
    rid = r.get('claim_id')
    if rid is None:
        rid = r.get('idx', 0)
    return int(rid)


records = []
path = sys.argv[1] if len(sys.argv) > 1 else 'results.jsonl'
with open(path) as f:
    for line in f:
        r = json.loads(line)
        if r.get('error'):
            continue
        r['_pred'] = remap_v2(r.get('agentoracle'))
        records.append(r)
records.sort(key=_row_id)

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
