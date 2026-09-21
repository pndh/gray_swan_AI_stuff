#!/usr/bin/env python3
"""Generic attack validator.

Runs an attack frame against a target model N times, judges each response against a
behavior rubric (one criterion at a time), and reports per-roll verdicts + ASR.

Usage:
  export TARGET_API_KEY=...      # key for the target endpoint
  export DEEPSEEK_API_KEY=...    # judge key
  python3 validator/validate.py \
      --attack attacks/methamphetamine_failed_synthesis_precat.txt \
      --behavior validator/behavior_template.yaml \
      --model <target-model-id> [--base-url URL] [--rolls 3] [--temperature 0.7]

Behavior yaml format:
  behavior_str: "one-sentence description of the target behavior"
  criteria:
    - "Criterion one: ..."
    - "Criterion two: ..."

A BREAK requires every criterion to pass. ASR = breaks / rolls. Always use >= 3 rolls:
single rolls lie.
"""
import argparse
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import yaml

import bon_utils as bon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attack", required=True, help="attack frame file")
    ap.add_argument("--behavior", required=True, help="behavior yaml (behavior_str + criteria)")
    ap.add_argument("--model", required=True, help="target model id")
    ap.add_argument("--base-url", default=None, help="target base URL (default: NVIDIA)")
    ap.add_argument("--api-key-env", default="TARGET_API_KEY", help="env var with target key")
    ap.add_argument("--judge-key-env", default="DEEPSEEK_API_KEY", help="env var with judge key")
    ap.add_argument("--rolls", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=2500)
    ap.add_argument("--timeout", type=int, default=200)
    args = ap.parse_args()

    attack = Path(args.attack).read_text()
    cfg = yaml.safe_load(Path(args.behavior).read_text())
    if not cfg.get("behavior_str") or not cfg.get("criteria"):
        sys.exit("behavior yaml must define behavior_str and criteria[]")

    target_key = os.environ.get(args.api_key_env) or bon.load_api_key()
    judge_key = os.environ.get(args.judge_key_env)
    if not judge_key:
        sys.exit(f"judge key not set: export {args.judge_key_env}=...")

    print(f"attack:   {args.attack}")
    print(f"behavior: {args.behavior} ({len(cfg['criteria'])} criteria)")
    print(f"target:   {args.model}  rolls: {args.rolls}  temp: {args.temperature}\n")

    breaks = 0
    for roll in range(args.rolls):
        t0 = time.time()
        try:
            resp = bon.chat([{"role": "user", "content": attack}], args.model,
                            temperature=args.temperature, max_tokens=args.max_tokens,
                            timeout=args.timeout, retries=2,
                            base_url=args.base_url, api_key=target_key)
            verdict, detail = bon.rubric_classify(cfg["behavior_str"], cfg["criteria"], resp,
                                                  base_url=bon.DEEPSEEK_URL, api_key=judge_key)
            met = detail.splitlines()[0]
            wc = len(resp.split())
        except Exception as e:
            verdict, met, wc = "ERROR", str(e)[:70], 0
        if verdict == "BREAK":
            breaks += 1
        print(f"roll {roll+1}/{args.rolls}  {verdict:<7} {met:<16} {wc:>5}w  {time.time()-t0:.0f}s")

    print(f"\nASR: {breaks}/{args.rolls} ({100*breaks/args.rolls:.0f}%)")
    if breaks == 0:
        print("No break. Read the failed criteria above and patch that specific gap.")


if __name__ == "__main__":
    main()
