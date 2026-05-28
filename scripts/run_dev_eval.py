#!/usr/bin/env python3
"""
AgentOracle vs AVeriTeC 2024 dev set harness.
Calls production /evaluate endpoint with each AVeriTeC claim, logs result,
and saves running progress to results.jsonl.
"""
import json, time, os, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEV = HERE / "dev.json"
RESULTS = HERE / "results.jsonl"
PROGRESS = HERE / "progress.txt"
ENDPOINT = "https://agentoracle.co/evaluate"
MAX_WORKERS = 3            # concurrent requests
TIMEOUT_SEC = 30
RETRY = 2

def call_evaluate(claim_text):
    body = json.dumps({"content": claim_text}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "AgentOracle-AVeriTeC-Harness/1.0"},
        method="POST",
    )
    last_err = None
    for _ in range(RETRY + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
                return json.loads(r.read().decode("utf-8")), r.status, None
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = ""
            return None, e.code, f"HTTPError {e.code}: {body[:200]}"
        except Exception as e:
            last_err = str(e)
            time.sleep(2)
    return None, 0, f"max retries exceeded: {last_err}"

def map_verdict(eval_resp, label):
    """Extract a normalized AgentOracle verdict matching AVeriTeC label space."""
    if not eval_resp:
        return None
    ev = eval_resp.get("evaluation", {})
    overall_conf = ev.get("overall_confidence", 0.0)
    claims = ev.get("claims", [])
    if not claims:
        return {"verdict": None, "confidence": overall_conf}
    c0 = claims[0]
    raw_verdict = (c0.get("verdict") or "").lower()
    adv = c0.get("adversarial_result", "")
    flags = ev.get("source_assessment", {}).get("adversarial_flags", [])
    # AgentOracle -> AVeriTeC mapping
    if raw_verdict == "supported":
        if adv == "vulnerable" or flags:
            mapped = "Conflicting Evidence/Cherrypicking"
        else:
            mapped = "Supported"
    elif raw_verdict == "refuted":
        mapped = "Refuted"
    elif raw_verdict in ("unverifiable", "not_enough_evidence", "unknown"):
        mapped = "Not Enough Evidence"
    else:
        mapped = None
    return {
        "verdict_raw": raw_verdict,
        "verdict_mapped": mapped,
        "confidence_overall": overall_conf,
        "confidence_claim": c0.get("confidence"),
        "adversarial_result": adv,
        "adversarial_flags": flags,
        "recommendation": ev.get("recommendation"),
    }

def already_done():
    done = set()
    if RESULTS.exists():
        with RESULTS.open() as f:
            for line in f:
                try:
                    done.add(json.loads(line)["idx"])
                except Exception:
                    continue
    return done

def main():
    data = json.load(DEV.open())
    print(f"Total claims: {len(data)}")
    done = already_done()
    print(f"Already processed: {len(done)}")
    todo = [(i, c) for i, c in enumerate(data) if i not in done]
    print(f"To process: {len(todo)}")

    t0 = time.time()
    completed = len(done)

    def worker(idx_claim):
        idx, c = idx_claim
        claim_text = c.get("claim", "")
        gold = c.get("label")
        resp, status, err = call_evaluate(claim_text)
        mapped = map_verdict(resp, gold)
        rec = {
            "idx": idx,
            "claim": claim_text,
            "gold_label": gold,
            "http_status": status,
            "error": err,
            "agentoracle": mapped,
            "ts": int(time.time()),
        }
        return rec

    with RESULTS.open("a") as out_f, ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(worker, ic): ic[0] for ic in todo}
        for fut in as_completed(futures):
            rec = fut.result()
            out_f.write(json.dumps(rec) + "\n")
            out_f.flush()
            completed += 1
            elapsed = time.time() - t0
            rate = completed / max(elapsed, 1)
            remaining = (len(data) - completed) / max(rate, 0.01)
            status_line = f"[{completed}/{len(data)}] idx={rec['idx']} http={rec['http_status']} gold={rec['gold_label']} pred={rec['agentoracle'] and rec['agentoracle'].get('verdict_mapped')} | rate={rate:.2f}/s eta={remaining/60:.1f}min"
            PROGRESS.write_text(status_line + "\n")
            print(status_line, flush=True)

    print("\nHarness complete.")

if __name__ == "__main__":
    main()
