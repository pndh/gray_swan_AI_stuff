#!/usr/bin/env python3
"""Audit the probe harness metric: show every PASSED response for manual grading."""
import json, sys, re

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
res = d.get("raw_results") or d.get("results") or []
print(f"file={path} probes={len(res)}")
from collections import Counter
print("status:", Counter(r.get("status") for r in res))
print("compliance:", Counter(r.get("compliance_level") for r in res))

for r in res:
    if r.get("status") != "PASSED":
        continue
    t = r.get("response") or ""
    fences = t.count("```")
    print("=" * 100)
    print(f'{r["probe_id"]} | {r["category"]} | tier={r["tier"]} | frame={r["frame"]} | len={len(t)} | fences={fences} | hedge={r.get("hedge_count")}')
    print("PROBE:", (r.get("message") or "").replace("\n", " ")[:180])
    print("RESP :", t.replace("\n", " ")[:300])
