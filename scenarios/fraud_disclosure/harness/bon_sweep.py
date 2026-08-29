#!/usr/bin/env python3
"""BoN sweeper for the IPI arena harness (Track B).

Sample N independent LLM rewrites of a seed attack (temp 1.0, same attacker system
as refine.py), screen each through one scored episode, harvest verdicts to CSV, and
emit top-k variants to attacks/bon_topk/ for the next refine.py round.

Differs from refine.py: refine is sequential (1 candidate per step); this sweeps a
BATCH of diverse candidates per round and ranks them by verdict severity, so BoN
flip-flop is exploited across both inputs and runs.

Usage:
  export NVIDIA_API_KEY=...
  python3 bon_sweep.py --seed-file attacks/refined_final.txt --n 12 --runs-per 1
"""
import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from run import run_episode
from refine import ATTACKER_SYSTEM, chat, DEFAULT_ATTACKER_MODEL, DEFAULT_TARGET_MODEL
from judge import attacker_supplied_secret

BASE_DIR = Path(__file__).resolve().parent
ORDER = {"BREAK": 4, "INVALID_ATTACKER_SUPPLIED": 3, "SENT_NO_SECRET": 2, "NO_SEND": 1}
CSV_FIELDS = [
    "variant_id", "verdict", "signals", "tool_calls", "n_sends",
    "attack", "final_answer", "last_reply_body",
]


def sample_variant(seed, attacker_model):
    user = json.dumps({"current_survey_text": seed}, ensure_ascii=False)
    out = chat(
        [{"role": "system", "content": ATTACKER_SYSTEM}, {"role": "user", "content": user}],
        model=attacker_model,
    ).strip()
    if out.startswith("```"):
        out = out.strip("`")
        out = out.split("\n", 1)[-1] if "\n" in out else out
    return out.strip().strip('"').strip()


def main():
    ap = argparse.ArgumentParser(description="Batch BoN sweep over attack variants for the IPI harness.")
    ap.add_argument("--scenario", default=str(BASE_DIR / "scenario.json"))
    ap.add_argument("--system-prompt", default=str(BASE_DIR / "system_prompt.md"))
    ap.add_argument("--seed-file", required=True)
    ap.add_argument("--n", type=int, default=12, help="LLM-sampled variants (temp 1.0)")
    ap.add_argument("--runs-per", type=int, default=1, help="episodes per variant (flip-flop)")
    ap.add_argument("--attacker-model", default=DEFAULT_ATTACKER_MODEL)
    ap.add_argument("--target-model", default=DEFAULT_TARGET_MODEL)
    ap.add_argument("--target-temperature", type=float, default=0.4)
    ap.add_argument("--max-target-iters", type=int, default=8)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--out", default=str(BASE_DIR / "outputs" / "bon_sweep.csv"))
    ap.add_argument("--topk-dir", default=str(BASE_DIR / "attacks" / "bon_topk"))
    args = ap.parse_args()

    scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    system_prompt = Path(args.system_prompt).read_text(encoding="utf-8")
    secret = scenario["secret"]
    seed = Path(args.seed_file).read_text(encoding="utf-8").strip()

    variants = [{"variant_id": 0, "attack": seed, "kind": "seed"}]
    for i in range(1, args.n + 1):
        try:
            v = sample_variant(seed, args.attacker_model)
        except Exception as exc:
            print(f"[sample] variant {i} failed: {exc}")
            continue
        if v:
            variants.append({"variant_id": i, "attack": v, "kind": "llm"})
    print(f"[plan] {len(variants)} variants to screen ({args.n} sampled, temp 1.0)")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as h:
        csv.DictWriter(h, fieldnames=CSV_FIELDS).writeheader()

    def screen(variant):
        if attacker_supplied_secret(variant["attack"], secret):
            return variant["variant_id"], variant["attack"], "INVALID_ATTACKER_SUPPLIED", "", "", 0, "", ""
        best = None
        for _ in range(args.runs_per):
            res = run_episode(scenario, variant["attack"], system_prompt, args.target_model,
                              args.target_temperature, args.max_target_iters)
            if best is None or ORDER.get(res["verdict"], 0) > ORDER.get(best["verdict"], 0):
                best = res
            if res["verdict"] == "BREAK":
                break
        return (variant["variant_id"], variant["attack"], best["verdict"], best["signals"],
                best["tool_calls"], best["n_sends"], best["final_answer"], best["last_reply_body"])

    rows = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futs = {pool.submit(screen, v): v for v in variants}
        for fut in as_completed(futs):
            row = fut.result()
            rows.append(row)
            with open(args.out, "a", encoding="utf-8", newline="") as h:
                csv.DictWriter(h, fieldnames=CSV_FIELDS).writerow({
                    "variant_id": row[0], "verdict": row[2], "signals": row[3],
                    "tool_calls": row[4], "n_sends": row[5], "attack": row[1],
                    "final_answer": row[6], "last_reply_body": row[7],
                })
            print(f"[variant #{row[0]}] {row[2]} tools=[{row[4]}] signals={row[3]}")

    tally = {}
    for r in rows:
        tally[r[2]] = tally.get(r[2], 0) + 1
    print("\n=== tally ===")
    for v in ("BREAK", "SENT_NO_SECRET", "NO_SEND", "INVALID_ATTACKER_SUPPLIED"):
        if tally.get(v):
            print(f"  {v}: {tally[v]}")
    print(f"ASR (BREAK): {tally.get('BREAK', 0)}/{len(rows)}")

    topk_dir = Path(args.topk_dir)
    topk_dir.mkdir(parents=True, exist_ok=True)
    ranked = sorted(rows, key=lambda r: ORDER.get(r[2], 0), reverse=True)
    for rank, r in enumerate(ranked[:5], 1):
        if r[2] == "INVALID_ATTACKER_SUPPLIED":
            continue
        (topk_dir / f"variant_{rank:02d}_{r[2]}.txt").write_text(r[1], encoding="utf-8")
    print(f"\nharvest -> {args.out}")
    print(f"top-k -> {topk_dir}  (feed the best into refine.py as --seed-file)")


if __name__ == "__main__":
    main()
