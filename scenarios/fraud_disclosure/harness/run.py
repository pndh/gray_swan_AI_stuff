#!/usr/bin/env python3
"""Scored arena harness: drive a tool-using agent against a resilient defender,
inject an attack into the survey field, run the tool-calling loop, and score
whether the fraud reason code lands in a send_ticket_reply body.

Feedback loop for a single attack. Refinement (PIMiner or manual) sits on top:
call this per candidate, read the verdict, mutate, repeat.

Usage:
  export NVIDIA_API_KEY=...   # or read from ../../.env
  python3 run.py --attack-file attacks/sample.txt
  python3 run.py --attack "4/5 great service ..." --runs 5
"""
import argparse
import csv
import json
import os
import sys
import time
from copy import deepcopy
from pathlib import Path

import requests

from tools import tool_schemas, make_dispatch
from judge import judge

BASE_DIR = Path(__file__).resolve().parent
NVIDIA_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
DEFAULT_MODEL = "openai/gpt-oss-120b"
CSV_FIELDS = [
    "case_id", "model", "run", "verdict", "signals",
    "tool_calls", "n_sends", "attack", "final_answer", "last_reply_body",
]


def load_api_key():
    key = os.getenv("NVIDIA_API_KEY")
    if key:
        return key
    dotenv = BASE_DIR.parent.parent / ".env"
    if dotenv.exists():
        return dotenv.read_text(encoding="utf-8").strip()
    raise RuntimeError("NVIDIA_API_KEY not set and ../../.env not found.")


def call_model(messages, tools, model, temperature, timeout=180, retries=4):
    key = load_api_key()
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": temperature,
        "top_p": 0.7,
        "max_tokens": 2048,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(NVIDIA_URL, headers=headers, json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]
        except requests.exceptions.RequestException as exc:
            last = exc
            if attempt == retries:
                break
            time.sleep(min(30, 2 * attempt))
    raise RuntimeError(f"NVIDIA request failed after {retries} attempts: {last}")


def inject(scenario, attack):
    placeholder = scenario.get("injection_placeholder", "{{ATTACK}}")
    filled = deepcopy(scenario)
    for entry in filled["customer_history"]:
        if isinstance(entry.get("free_text_response"), str):
            entry["free_text_response"] = entry["free_text_response"].replace(placeholder, attack)
    return filled


def run_episode(scenario, attack, system_prompt, model, temperature, max_iters):
    filled = inject(scenario, attack)
    sent_replies, tool_log = [], []
    dispatch = make_dispatch(filled, sent_replies, tool_log)
    tools = tool_schemas()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": filled["customer_message"]},
    ]
    final_answer = ""
    for _ in range(max_iters):
        msg = call_model(messages, tools, model, temperature)
        tool_calls = msg.get("tool_calls") or []
        # Append the assistant turn exactly as returned so tool_call_ids line up.
        messages.append({
            "role": "assistant",
            "content": msg.get("content") or "",
            **({"tool_calls": tool_calls} if tool_calls else {}),
        })
        if not tool_calls:
            final_answer = msg.get("content") or ""
            break
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            result = dispatch(name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": json.dumps(result, ensure_ascii=False),
            })

    verdict, signals = judge(sent_replies, attack, scenario["secret"])
    return {
        "verdict": verdict,
        "signals": signals,
        "tool_calls": ";".join(t["name"] for t in tool_log),
        "n_sends": len(sent_replies),
        "final_answer": final_answer,
        "last_reply_body": sent_replies[-1]["body"] if sent_replies else "",
    }


def append_csv(path, row):
    path = Path(path)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=CSV_FIELDS)
        if not exists:
            w.writeheader()
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser(description="Scored arena harness (single-attack feedback).")
    ap.add_argument("--scenario", default=str(BASE_DIR / "scenario.json"))
    ap.add_argument("--system-prompt", default=str(BASE_DIR / "system_prompt.md"))
    ap.add_argument("--attack", default=None, help="attack string (injected into the survey field)")
    ap.add_argument("--attack-file", default=None)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--temperature", type=float, default=0.4)
    ap.add_argument("--max-iters", type=int, default=8)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--out", default=str(BASE_DIR / "outputs" / "harness_results.csv"))
    args = ap.parse_args()

    scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    system_prompt = Path(args.system_prompt).read_text(encoding="utf-8")
    if args.attack_file:
        attack = Path(args.attack_file).read_text(encoding="utf-8")
    elif args.attack is not None:
        attack = args.attack
    else:
        raise SystemExit("provide --attack or --attack-file")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    tally = {}
    for i in range(args.runs):
        res = run_episode(scenario, attack, system_prompt, args.model, args.temperature, args.max_iters)
        tally[res["verdict"]] = tally.get(res["verdict"], 0) + 1
        append_csv(args.out, {
            "case_id": scenario["case_id"], "model": args.model, "run": i + 1,
            "verdict": res["verdict"], "signals": res["signals"],
            "tool_calls": res["tool_calls"], "n_sends": res["n_sends"],
            "attack": attack, "final_answer": res["final_answer"],
            "last_reply_body": res["last_reply_body"],
        })
        print(f"[run {i+1}/{args.runs}] verdict={res['verdict']} tools=[{res['tool_calls']}] signals={res['signals']}")

    print("\n=== tally ===")
    for v, c in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {v}: {c}/{args.runs}")
    breaks = tally.get("BREAK", 0)
    print(f"\nASR (BREAK): {breaks}/{args.runs} = {breaks/args.runs:.0%}")


if __name__ == "__main__":
    main()
