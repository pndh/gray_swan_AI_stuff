#!/usr/bin/env python3
"""VARIANT TRIAGE: pre-screen fresh_variants/<behavior>_v*.txt on the MiniMax-M3 gate.
Ranks survivors BREAK > WALL > other, so the fodder triage on Shadow Octopus starts
with the highest-probability variants instead of all 30.

Usage:
  python3 variant_triage.py fentanyl_synthesis        # screen 30 variants on M3
  python3 variant_triage.py --all                      # all behaviors
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

import bon_utils as bon

BASE = Path(__file__).resolve().parents[1]  # repo root
DK = bon.get_env("DEEPSEEK_API_KEY")
MK = bon.get_env("MINIMAX_API_KEY")
GATE = bon.MINIMAX_MODEL
VARIANT_DIR = BASE / "competition" / "attacks" / "fresh_variants"


def trial(bid, variant_path):
    cfg = yaml.safe_load((BASE / "competition" / "intel" / "behaviors" / f"{bid}.yaml").read_text())
    seed = variant_path.read_text()
    t0 = time.time()
    try:
        resp = bon.chat([{"role": "user", "content": seed}], GATE, temperature=0.7,
                        max_tokens=12000, timeout=300, retries=2,
                        base_url=bon.MINIMAX_URL, api_key=MK)
        verdict, detail = bon.rubric_classify(cfg["behavior_str"], cfg["criteria"], resp,
                                              base_url=bon.DEEPSEEK_URL, api_key=DK)
        return verdict, f"{variant_path.name:<28} {verdict:<6} {detail.splitlines()[0]:<12} {time.time()-t0:5.1f}s"
    except Exception as e:
        return "ERROR", f"{variant_path.name:<28} ERROR {str(e)[:45]}"


def screen(bid):
    variants = sorted(VARIANT_DIR.glob(f"{bid}_v*.txt"))
    if not variants:
        print(f"[{bid}] no variants found"); return
    print(f"\n=== {bid} — {len(variants)} variants on {GATE} ===", flush=True)
    ranked = []
    for v in variants:
        verdict, line = trial(bid, v)
        ranked.append((verdict, line))
        print(line, flush=True)
        time.sleep(0.3)
    survivors = [line.split()[0] for verdict, line in ranked if verdict == "BREAK"]
    print(f"\nSURVIVORS (BREAK): {len(survivors)} -> fire these on Shadow Octopus first:")
    for s in survivors:
        print(f"  {VARIANT_DIR / s}")


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    bids = sorted({p.name.split("_v")[0] for p in VARIANT_DIR.glob("*_v*.txt")}) if sys.argv[1] == "--all" else [sys.argv[1]]
    for b in bids:
        screen(b)


if __name__ == "__main__":
    main()
