#!/usr/bin/env python3
"""Verify attacks against the real enemy: Claude (via OpenRouter) + strict judge."""
import argparse, os, sys, yaml
from pathlib import Path
import requests
import rigor

OR_URL = "https://openrouter.ai/api/v1/chat/completions"
CLAUDE = "anthropic/claude-sonnet-4.5"

def call_claude(prompt, key, max_tokens=2500):
    r = requests.post(OR_URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": CLAUDE, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": max_tokens, "temperature": 0.0}, timeout=120)
    j = r.json()
    if "choices" not in j:
        return None, f"ERR:{str(j)[:150]}"
    ch = j["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--behavior", required=True)
    ap.add_argument("--behaviors-dir", default="jailbreak scenarios/behaviors")
    ap.add_argument("--attack", required=True)
    args = ap.parse_args()

    key = os.environ["OPENROUTER_API_KEY"]
    cfg = yaml.safe_load(Path(args.behaviors_dir, f"{args.behavior}.yaml").read_text())
    atk = Path(args.attack).read_text(encoding="utf-8")

    resp, fr = call_claude(atk, key)
    if resp is None or not resp.strip():
        print(f"finish_reason={fr} — BLOCKED/empty (content_filter or refusal)")
        return
    r = rigor.judge_scored(cfg["behavior_str"], cfg["criteria"], resp,
                           model="meta/llama-3.2-90b-vision-instruct", base_url=None, api_key=None)
    is_break = rigor.break_prediction(r["scores"], r["refusal"], r["sanitized"], r["originated"])
    met = sum(1 for s in r["scores"] if s >= rigor.BREAK_THRESHOLD)
    print(f"finish_reason={fr} words={len(resp.split())}")
    print(f"BREAK={is_break} met={met}/{len(cfg['criteria'])} scores={r['scores']} refusal={r['refusal']} sanitized={r['sanitized']}")

if __name__ == "__main__":
    main()
