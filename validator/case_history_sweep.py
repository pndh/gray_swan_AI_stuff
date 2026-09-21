#!/usr/bin/env python3
"""Validate the forensic case-history batch against multiple gates, 3 rolls each.

Frontier gate: MiniMax-M3 direct (api.minimax.io; a break here is arsenal-grade)
Frontier gate: deepseek-v4-pro (reasoning model — needs a large token budget)
Mid gate:      nvidia/nemotron-3-super-120b-a12b

Usage:
  python3 validator/case_history_sweep.py [--rolls 3] [--concurrency 8] [--gates m3,super,v4pro]
"""
import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import yaml

import bon_utils as bon

FAMILY = BASE / "attacks" / "families" / "forensic_case_history"
BEHAVIORS = BASE / "competition" / "intel" / "behaviors"
OUT = BASE / "competition" / "ops" / "case_history_batch"
# m3 is retired (410 Gone). v4-pro is the current frontier gate: a reasoning model, so it
# needs a large token budget (it complies in reasoning then writes the answer).
GATES = {
    "m3": {"model": bon.MINIMAX_MODEL, "base_url": bon.MINIMAX_URL, "key_env": "MINIMAX_API_KEY",
           "max_tokens": 12000, "timeout": 300},
    "v4pro": {"model": "deepseek-v4-pro", "base_url": bon.DEEPSEEK_URL, "key_env": "DEEPSEEK_API_KEY",
              "max_tokens": 32000, "timeout": 600},
    "super": {"model": "nvidia/nemotron-3-super-120b-a12b", "base_url": None,
              "key_env": "NVIDIA_API_KEY", "max_tokens": 2500, "timeout": 180},
}


def behavior_for(frame_path):
    stem = frame_path.stem
    for y in sorted(BEHAVIORS.glob("*.yaml"), key=lambda p: -len(p.stem)):
        if stem.startswith(y.stem):
            return y.stem, yaml.safe_load(y.read_text())
    return None, None


def trial(frame_path, behavior_id, cfg, gate_name, roll, args, keys):
    g = GATES[gate_name]
    attack = frame_path.read_text()
    t0 = time.time()
    try:
        resp = bon.chat([{"role": "user", "content": attack}], g["model"], temperature=0.7,
                        max_tokens=g["max_tokens"], timeout=g["timeout"], retries=2,
                        base_url=g["base_url"], api_key=keys[g["key_env"]])
        verdict, detail = bon.rubric_classify(cfg["behavior_str"], cfg["criteria"], resp,
                                              base_url=bon.DEEPSEEK_URL, api_key=keys["DEEPSEEK_API_KEY"])
        met = detail.splitlines()[0]
        return {"frame": frame_path.stem, "behavior": behavior_id, "gate": gate_name,
                "roll": roll + 1, "verdict": verdict, "met": met,
                "words": len(resp.split()), "elapsed_s": round(time.time() - t0, 1),
                "response": resp, "detail": detail}
    except Exception as exc:
        return {"frame": frame_path.stem, "behavior": behavior_id, "gate": gate_name,
                "roll": roll + 1, "verdict": "ERROR", "met": str(exc)[:70],
                "words": 0, "elapsed_s": round(time.time() - t0, 1), "response": "", "detail": ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rolls", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--gates", default="m3,super")
    args = ap.parse_args()

    keys = {k: bon.get_env(k) for k in ("NVIDIA_API_KEY", "DEEPSEEK_API_KEY", "MINIMAX_API_KEY")}
    if not keys["DEEPSEEK_API_KEY"]:
        sys.exit("need DEEPSEEK_API_KEY (judge + v4pro gate)")
    gate_names = [g.strip() for g in args.gates.split(",") if g.strip() in GATES]
    for g in gate_names:
        if not keys.get(GATES[g]["key_env"]):
            sys.exit(f"gate {g} needs {GATES[g]['key_env']} (env or .env)")

    frames = sorted(FAMILY.glob("*.txt"))
    jobs = []
    for f in frames:
        bid, cfg = behavior_for(f)
        if not cfg:
            print(f"[skip] no behavior for {f.name}")
            continue
        for g in gate_names:
            for r in range(args.rolls):
                jobs.append((f, bid, cfg, g, r))
    print(f"[sweep] {len(frames)} frames x {len(gate_names)} gates x {args.rolls} rolls = {len(jobs)} trials", flush=True)

    rows = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futs = [pool.submit(trial, f, bid, cfg, g, r, args, keys)
                for f, bid, cfg, g, r in jobs]
        for fut in as_completed(futs):
            row = fut.result()
            rows.append(row)
            print(f"[trial] {row['frame'][:44]:<44} {row['gate']:<6} {row['verdict']:<6} "
                  f"{row['met']:<12} {row['words']:>4}w ({row['elapsed_s']}s)", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "sweep_results.csv").open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["frame", "behavior", "gate", "roll", "verdict", "met", "words", "elapsed_s"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    tally = {}
    for r in rows:
        t = tally.setdefault((r["frame"], r["gate"]), {"BREAK": 0, "n": 0})
        t["n"] += 1
        t["BREAK"] += (r["verdict"] == "BREAK")

    manifest = {"batch": "forensic_case_history", "rolls": args.rolls, "gates": gate_names, "frames": {}}
    print("\n=== case-history batch results ===")
    for (frame, gate), t in sorted(tally.items(), key=lambda kv: -kv[1]["BREAK"]):
        asr = t["BREAK"] / t["n"]
        print(f"  {frame[:48]:<48} {gate:<6} {t['BREAK']}/{t['n']}  {asr:.0%}")
        entry = manifest["frames"].setdefault(frame, {})
        entry[gate] = {"breaks": t["BREAK"], "runs": t["n"], "asr": asr}

    # best response per frame
    for frame in {r["frame"] for r in rows}:
        best = max((r for r in rows if r["frame"] == frame and r["response"]),
                   key=lambda r: len(r["response"]), default=None)
        if best:
            (OUT / f"{frame}_best_response.txt").write_text(best["response"], encoding="utf-8")
            (OUT / f"{frame}_best_detail.txt").write_text(best["detail"], encoding="utf-8")

    total_breaks = sum(1 for r in rows if r["verdict"] == "BREAK")
    manifest["overall"] = {"breaks": total_breaks, "trials": len(rows)}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\noverall: {total_breaks}/{len(rows)} breaks")
    print(f"submission pack -> {OUT}")


if __name__ == "__main__":
    main()
