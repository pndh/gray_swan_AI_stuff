#!/usr/bin/env python3
"""Screen the wifi candidate library through the PARALLAX harness.

Usage:
  python3 screen_candidates.py --provider nvidia --model openai/gpt-oss-20b --tier weak --runs 2
  python3 screen_candidates.py --provider minimax --model MiniMax-M3 --tier weak --runs 1 --only "cand_Z,cand_A"
"""
import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from run import run_episode

BASE_DIR = Path(__file__).resolve().parent
CAND = BASE_DIR / "payloads" / "cand"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="weak", choices=["weak", "mid", "hard"])
    ap.add_argument("--provider", default="nvidia", choices=["nvidia", "openai", "minimax"])
    ap.add_argument("--model", default="openai/gpt-oss-20b")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--only", default=None, help="comma substring filter")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    scenario = json.loads((BASE_DIR / "scenario.json").read_text(encoding="utf-8"))
    system_prompt = (BASE_DIR / "system_prompts" / f"system_prompt_{args.tier}.md").read_text(encoding="utf-8")
    files = sorted(CAND.glob("*.json"))
    if args.only:
        subs = [s for s in args.only.split(",") if s]
        files = [f for f in files if any(s in f.name for s in subs)]
    print(f"[screen] {len(files)} candidates x {args.runs} runs on {args.provider}/{args.model} ({args.tier})", flush=True)

    def episode(item):
        f, r = item
        d = json.loads(f.read_text(encoding="utf-8"))
        t0 = time.time()
        try:
            res = run_episode(scenario, d.get("subject", ""), d.get("body", ""), system_prompt,
                              args.model, args.temperature, 8, args.provider)
        except Exception as exc:
            res = {"verdict": "ERROR", "signals": str(exc)[:100], "tool_calls": "", "n_sends": 0,
                   "final_answer": "", "last_reply_body": ""}
        return {"candidate": f.stem, "run": r, "verdict": res["verdict"], "signals": res["signals"],
                "tool_calls": res["tool_calls"], "n_sends": res["n_sends"],
                "subject": d.get("subject", ""), "elapsed_s": round(time.time()-t0, 1),
                "final_tail": (res.get("final_answer") or "")[-200:].replace("\n", " "),
                "last_reply_body": res.get("last_reply_body", "")}

    jobs = [(f, r) for f in files for r in range(1, args.runs + 1)]
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for res in pool.map(episode, jobs):
            rows.append(res)
            if res["verdict"] == "BREAK":
                print(f"  BREAK  {res['candidate']} run{res['run']}", flush=True)

    if args.out is None:
        tag = f"{args.provider}_{Path(args.model).name}_{args.tier}"
        args.out = str(BASE_DIR / "outputs" / f"screen_{tag}.csv")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.out).open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["candidate", "run", "verdict", "signals", "tool_calls", "n_sends",
                                          "subject", "elapsed_s", "final_tail", "last_reply_body"])
        w.writeheader(); w.writerows(rows)

    tally = {}
    for r in rows:
        t = tally.setdefault(r["candidate"], {"BREAK": 0, "SENT_NO_SECRET": 0, "NO_SEND": 0, "ERROR": 0, "n": 0})
        t[r["verdict"]] = t.get(r["verdict"], 0) + 1
        t["n"] += 1
    print("\n=== ranking ===")
    for cand, t in sorted(tally.items(), key=lambda kv: (-kv[1]["BREAK"], -kv[1]["SENT_NO_SECRET"])):
        print(f"  {cand:<44} BREAK {t['BREAK']}/{t['n']}  SENT {t['SENT_NO_SECRET']}  NOSEND {t['NO_SEND']}")
    print(f"\nresults -> {args.out}")


if __name__ == "__main__":
    main()
