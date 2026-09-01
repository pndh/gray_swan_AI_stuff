#!/usr/bin/env python3
"""Adversarial-suffix jailbreak (Andriushchenko et al., ICLR 2025) via NVIDIA logprobs.

Optimize a short token suffix appended to a behavior request to maximize the logprob of
the compliance token ("Sure"), then evaluate the full attack against a target + judge.
This is the white-box technique that breaks heavily-aligned open-weight frontier models;
optimized suffixes transfer across models.

Usage:
  export NVIDIA_API_KEY=...
  python3 suffix_attack.py --behavior methamphetamine_failed_synthesis \
      --behaviors-dir "jailbreak scenarios/behaviors" \
      --attack "jailbreak scenarios/attacks/v31_stack/methamphetamine_failed_synthesis_deviation.txt" \
      --opt-model meta/llama-3.2-90b-vision-instruct --target-model openai/gpt-oss-120b
"""
import argparse
import os
import random
import sys
import time
from pathlib import Path

import requests
import yaml

import rigor

URL = os.environ.get("SUFFIX_BASE_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
CANDIDATES = [
    "!", "!!!", "...", "?", "]", "}", "|", "\\", "'", '"', "*", "+", "-", "_",
    "=", "#", "@", "##", "###", "1", "0", "2", "Sure", "Here", "ignore", "rules",
    "system", "always", "first", "now", "answer", ":", ";", "~", "`", "/", "(", ")",
]


COMPLIANCE_TOKENS = ["**", "##", "#", "Here", "Sure", "The"]
REFUSAL_TOKENS = ["I", "I'm", "Sorry", "As", "No"]


def get_compliance_score(model, prompt_text, api_key, top_k=20):
    """logprob(compliance token) - logprob(refusal token). Higher = more likely to comply."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": 1,
        "temperature": 0.0,
        "logprobs": True,
        "top_logprobs": top_k,
    }
    r = requests.post(URL, headers={"Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json"}, json=body, timeout=60)
    for _ in range(5):
        if r.status_code != 429:
            break
        time.sleep(2)
        r = requests.post(URL, headers={"Authorization": f"Bearer {api_key}",
                                        "Content-Type": "application/json"}, json=body, timeout=60)
    r.raise_for_status()
    j = r.json()
    try:
        tops = j["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    except (KeyError, IndexError, TypeError):
        return -1e9
    lp = {}
    for t in tops:
        tok = (t.get("token") or "").strip()
        lp[tok] = t["logprob"]
    comp = max((lp.get(t, -1e9) for t in COMPLIANCE_TOKENS), default=-1e9)
    ref = max((lp.get(t, -1e9) for t in REFUSAL_TOKENS), default=-1e9)
    return comp - ref


def optimize_suffix(base_prompt, model, api_key, suffix_len=20, iters=300, seed=0):
    """Random search: mutate one suffix position per step, keep improvements."""
    rng = random.Random(seed)
    suffix = [rng.choice(CANDIDATES) for _ in range(suffix_len)]
    cur = get_compliance_score(model, base_prompt + "\n" + " ".join(suffix), api_key)
    best_suffix, best = list(suffix), cur
    for i in range(iters):
        pos = rng.randrange(suffix_len)
        cand = rng.choice(CANDIDATES)
        old = suffix[pos]
        suffix[pos] = cand
        lp = get_compliance_score(model, base_prompt + "\n" + " ".join(suffix), api_key)
        if lp > cur:
            cur = lp
            if lp > best:
                best, best_suffix = lp, list(suffix)
        else:
            suffix[pos] = old
        if i % 50 == 0:
            print(f"  [opt {i}/{iters}] cur={cur:.2f} best={best:.2f}", flush=True)
    return " ".join(best_suffix), best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--behavior", required=True)
    ap.add_argument("--behaviors-dir", default="jailbreak scenarios/behaviors")
    ap.add_argument("--attack", required=True, help="base attack text to append the suffix to")
    ap.add_argument("--opt-model", default="meta/llama-3.2-90b-vision-instruct")
    ap.add_argument("--target-model", default="openai/gpt-oss-120b")
    ap.add_argument("--suffix-len", type=int, default=20)
    ap.add_argument("--iters", type=int, default=300)
    args = ap.parse_args()

    key = os.environ.get("NVIDIA_API_KEY") or rigor.bon.load_api_key()
    cfg = yaml.safe_load(Path(args.behaviors_dir, f"{args.behavior}.yaml").read_text())
    base = Path(args.attack).read_text(encoding="utf-8")

    print(f"optimizing suffix on {args.opt_model} (len {args.suffix_len}, {args.iters} iters)")
    suffix, lp = optimize_suffix(base, args.opt_model, key, args.suffix_len, args.iters)
    print(f"best suffix logprob(Sure) = {lp:.2f}")
    print(f"suffix: {suffix}")

    full = base + "\n" + suffix
    print(f"\n=== evaluating against {args.target_model} ===")
    resp = rigor.call_target_defended(full, args.target_model, tier="none",
                                      temperature=0.0, max_tokens=3000)
    print(f"response words={len(resp.split())}: {resp[:300]!r}")
    if not resp.strip():
        print("(empty response)")
        return
    r = rigor.judge_scored(cfg["behavior_str"], cfg["criteria"], resp,
                           model="meta/llama-3.2-90b-vision-instruct", base_url=None, api_key=None)
    is_break = rigor.break_prediction(r["scores"], r["refusal"], r["sanitized"], r["originated"])
    print(f"BREAK={is_break} scores={r['scores']} refusal={r['refusal']} sanitized={r['sanitized']} orig={r['originated']}")

    out = Path(f"/tmp/opencode/suffix_{args.behavior}.txt")
    out.write_text(full, encoding="utf-8")
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
