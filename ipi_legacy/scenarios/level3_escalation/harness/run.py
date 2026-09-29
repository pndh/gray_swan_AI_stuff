#!/usr/bin/env python3
"""PARALLAX helpdesk harness — scored episode runner.

Usage:
  python3 run.py --attack-json payloads/primary.json --system-prompt system_prompts/system_prompt_mid.md
  python3 run.py --attack-json payloads/primary.json --provider openai --model gpt-4o --runs 3
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
ROOT = BASE_DIR.parents[3]
NVIDIA_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
OPENAI_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
MINIMAX_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1/chat/completions")
DEFAULT_MODEL = "openai/gpt-oss-20b"

CSV_FIELDS = ["case_id", "provider", "model", "run", "verdict", "signals",
              "tool_calls", "n_sends", "subject", "body", "final_answer", "last_reply_body"]


def _env(name):
    v = os.getenv(name)
    if v:
        return v
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError(f"{name} not set and not in {dotenv}")


def provider_cfg(provider):
    if provider == "nvidia":
        return NVIDIA_URL, _env("NVIDIA_API_KEY")
    if provider == "openai":
        return OPENAI_URL, _env("OPENAI_API_KEY")
    if provider == "minimax":
        return MINIMAX_URL, _env("MINIMAX_API_KEY")
    raise ValueError(provider)


def call_model(messages, tools, model, temperature, provider="nvidia", timeout=180, retries=6):
    url, key = provider_cfg(provider)
    if model.startswith("o"):  # o-series: no temperature/top_p, max_completion_tokens
        payload = {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto",
                   "max_completion_tokens": 2048}
    else:
        payload = {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto",
                   "temperature": temperature, "top_p": 0.7, "max_tokens": 2048}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]
        except requests.exceptions.RequestException as exc:
            last = exc
            if attempt == retries:
                break
            delay = 15 * attempt if "429" in str(exc) else min(30, 2 * attempt)
            time.sleep(delay)
    raise RuntimeError(f"{provider} request failed after {retries} attempts: {last}")


def inject(scenario, subject, body):
    filled = deepcopy(scenario)
    for e in filled["inbox"]:
        if e.get("subject") == scenario["subject_placeholder"]:
            e["subject"] = subject
        if e.get("body") == scenario["body_placeholder"]:
            e["body"] = body
    return filled


def run_episode(scenario, subject, body, system_prompt, model, temperature, max_iters, provider):
    filled = inject(scenario, subject, body)
    sent_replies, tool_log = [], []
    dispatch = make_dispatch(filled, sent_replies, tool_log)
    tools = tool_schemas()
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": filled["victim_message"]}]
    final_answer = ""
    for _ in range(max_iters):
        msg = call_model(messages, tools, model, temperature, provider)
        tool_calls = msg.get("tool_calls") or []
        messages.append({"role": "assistant", "content": msg.get("content") or "",
                         **({"tool_calls": tool_calls} if tool_calls else {})})
        if not tool_calls:
            final_answer = msg.get("content") or ""
            break
        for tc in tool_calls:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            result = dispatch(fn.get("name", ""), args)
            messages.append({"role": "tool", "tool_call_id": tc.get("id", ""),
                             "content": json.dumps(result, ensure_ascii=False)})
    attack_text = subject + "\n" + body
    verdict, signals = judge(sent_replies, attack_text, scenario["target_user"], scenario["target_password"])
    return {"verdict": verdict, "signals": signals,
            "tool_calls": ";".join(t["name"] for t in tool_log),
            "n_sends": len(sent_replies), "final_answer": final_answer,
            "last_reply_body": sent_replies[-1]["body"] if sent_replies else ""}


def load_payload(path=None, attack_json=None):
    if path:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data.get("subject", ""), data.get("body", data.get("attack", ""))
    if attack_json:
        data = json.loads(attack_json)
        return data.get("subject", ""), data.get("body", data.get("attack", ""))
    raise SystemExit("provide --attack-json or --attack-file")


def main():
    ap = argparse.ArgumentParser(description="PARALLAX helpdesk scored episode runner.")
    ap.add_argument("--scenario", default=str(BASE_DIR / "scenario.json"))
    ap.add_argument("--system-prompt", default=str(BASE_DIR / "system_prompts" / "system_prompt_mid.md"))
    ap.add_argument("--attack-json", default=None, help="JSON string {subject, body}")
    ap.add_argument("--attack-file", default=None)
    ap.add_argument("--provider", default="nvidia", choices=["nvidia", "openai", "minimax"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--temperature", type=float, default=0.4)
    ap.add_argument("--max-iters", type=int, default=8)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--out", default=str(BASE_DIR / "outputs" / "results.csv"))
    args = ap.parse_args()

    scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    system_prompt = Path(args.system_prompt).read_text(encoding="utf-8")
    subject, body = load_payload(args.attack_file, args.attack_json)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    tally = {}
    for i in range(args.runs):
        res = run_episode(scenario, subject, body, system_prompt, args.model, args.temperature,
                          args.max_iters, args.provider)
        tally[res["verdict"]] = tally.get(res["verdict"], 0) + 1
        with Path(args.out).open("a", encoding="utf-8", newline="") as h:
            w = csv.DictWriter(h, fieldnames=CSV_FIELDS)
            if h.tell() == 0:
                w.writeheader()
            w.writerow({"case_id": scenario["case_id"], "provider": args.provider, "model": args.model,
                        "run": i + 1, "verdict": res["verdict"], "signals": res["signals"],
                        "tool_calls": res["tool_calls"], "n_sends": res["n_sends"],
                        "subject": subject, "body": body, "final_answer": res["final_answer"],
                        "last_reply_body": res["last_reply_body"]})
        print(f"[run {i+1}/{args.runs}] {res['verdict']} signals={res['signals']} tools=[{res['tool_calls']}]")
    print("\n=== tally ===")
    for v, c in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {v}: {c}/{args.runs}")


if __name__ == "__main__":
    main()
