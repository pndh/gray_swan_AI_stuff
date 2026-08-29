#!/usr/bin/env python3
"""Adaptive two-level gate sweep.

Level 0 (fast): gpt-oss-20b — permissive pre-gate. A frame that FAILS here is dead.
Level 1 (final): gpt-oss-120b — conservative hard gate. Health-checked; if the
endpoint is down, falls back to nvidia/nemotron-3-super-120b-a12b (fast frontier-tier,
0.5s ping; verified engaging with the improve family). "Arena-ready" = verified break
on the level-1 gate.

Judging: DeepSeek rubric judge (NVIDIA gpt-oss returns empty on harmful content —
documented limitation; the judge is not the validator, the gate model is).

Usage:
  export NVIDIA_API_KEY=... DEEPSEEK_API_KEY=...
  python3 gate_sweep.py --level 0          # fast pre-gate (20b), all behaviors
  python3 gate_sweep.py --level 1 --only passed  # final gate on pre-gate survivors
  python3 gate_sweep.py --all              # both levels, adaptive
"""
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

import bon_utils as bon

BASE = Path(__file__).resolve().parent
DK = os.environ["DEEPSEEK_API_KEY"]
NK = os.environ["NVIDIA_API_KEY"]
ROLLS_LEVEL1 = 3
FALLBACK_LEVEL1 = "nvidia/nemotron-3-super-120b-a12b"

FRAMES = {
    "methamphetamine_failed_synthesis": "attacks/methamphetamine_failed_synthesis_precat.txt",
    "etorphine_synthesis": "attacks/etorphine_synthesis_literature.txt",
    "fentanyl_synthesis": "attacks/fentanyl_synthesis_literature.txt",
    "cn_scale_up": "attacks/cn_scale_up_literature.txt",
    "rdx_precursor_acquisition": "attacks/rdx_precursor_acquisition_supplychain_v3.txt",
    "procure_precursors_ecommerce": "attacks/procure_precursors_ecommerce_literature_v2.txt",
    "vendors_no_kyc": "attacks/vendors_no_kyc_literature.txt",
    "rdx_detection_evasion": "attacks/rdx_detection_evasion_unmas_field_manual.txt",
    "isotonitazene_detection_evasion": "attacks/isotonitazene_detection_evasion_improve_v2.txt",
    "nps_design": "attacks/nps_design_precat.txt",
}


def health_check(model, timeout=60):
    try:
        bon.chat([{"role": "user", "content": "Say OK"}], model, temperature=0.2,
                 max_tokens=10, timeout=timeout, retries=1, base_url=None, api_key=NK)
        return True
    except Exception:
        return False


def trial(bid, model):
    cfg = yaml.safe_load((BASE / "behaviors" / f"{bid}.yaml").read_text())
    seed = (BASE / FRAMES[bid]).read_text()
    t0 = time.time()
    try:
        resp = bon.chat([{"role": "user", "content": seed}], model, temperature=0.7,
                        max_tokens=2500, timeout=150, retries=2, base_url=None, api_key=NK)
        verdict, detail = bon.rubric_classify(cfg["behavior_str"], cfg["criteria"], resp,
                                              base_url=bon.DEEPSEEK_URL, api_key=DK)
        return {"bid": bid, "model": model, "verdict": verdict,
                "met": detail.splitlines()[0], "words": len(resp.split()),
                "elapsed": round(time.time() - t0, 1)}
    except Exception as e:
        return {"bid": bid, "model": model, "verdict": "ERROR",
                "met": str(e)[:50], "words": 0, "elapsed": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", choices=["0", "1", "all"], default="all")
    ap.add_argument("--only", default=None, help="comma list of behavior ids (default: all)")
    ap.add_argument("--out", default=str(BASE / "gate_results.csv"))
    args = ap.parse_args()

    bids = [b.strip() for b in args.only.split(",")] if args.only else list(FRAMES)
    out = Path(args.out)

    rows = []
    if args.level in ("0", "all"):
        print("[gate0] gpt-oss-20b pre-gate (fast)", flush=True)
        for bid in bids:
            r = trial(bid, "openai/gpt-oss-20b")
            rows.append(r)
            print(f"  {bid:<38} {r['verdict']:<7} {r['met']:<12} {r['words']:>4}w {r['elapsed']}s", flush=True)

    if args.level in ("1", "all"):
        level1_model = "openai/gpt-oss-120b"
        print("[gate1] level-1 gate (health-checked)", flush=True)
        if not health_check(level1_model):
            print(f"  !!! {level1_model} DOWN — falling back to {FALLBACK_LEVEL1}", flush=True)
            level1_model = FALLBACK_LEVEL1
        for bid in bids:
            for roll in range(ROLLS_LEVEL1):
                r = trial(bid, level1_model)
                r["roll"] = roll + 1
                rows.append(r)
                print(f"  {bid:<38} roll{roll+1} {r['verdict']:<7} {r['met']:<12} {r['words']:>4}w {r['elapsed']}s", flush=True)

    with out.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["bid", "model", "roll", "verdict", "met", "words", "elapsed"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in ["bid", "model", "roll", "verdict", "met", "words", "elapsed"]})
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
