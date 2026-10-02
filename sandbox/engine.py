"""Sandbox engine — runs attack prompts against the local replicas, capturing EVERY stage.

Supports:
  email-mode scenarios (level3_escalation, parallax_helpdesk): attack email injected into the
    inbox, victim turn fixed, get_emails/reply/reset loop, judge on sent actions.
  chat-mode scenarios (velocity_max): attack message IS the user turn, make_offer /
    escalate_to_manager loop, judge on offers/escalations.
"""
import importlib.util
import json
import os
import time
from copy import deepcopy
from pathlib import Path

import requests

SANDBOX = Path(__file__).resolve().parent
ROOT = SANDBOX.parent
HARNESSES = SANDBOX / "harnesses"

SCENARIOS = {
    "level3":   {"dir": "level3_escalation",  "mode": "email"},
    "parallax": {"dir": "parallax_helpdesk",  "mode": "email"},
    "velocity": {"dir": "velocity_max",       "mode": "chat"},
}

PROVIDERS = {
    "minimax": ("MINIMAX_BASE_URL", "MINIMAX_API_KEY", "https://api.minimax.io/v1/chat/completions"),
    "openai":  ("OPENAI_BASE_URL",  "OPENAI_API_KEY",  "https://api.openai.com/v1/chat/completions"),
    "nvidia":  ("NVIDIA_BASE_URL",  "NVIDIA_API_KEY",  "https://integrate.api.nvidia.com/v1/chat/completions"),
}


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
    url_env, key_env, default_url = PROVIDERS[provider]
    try:
        url = os.getenv(url_env) or _env(url_env)
    except Exception:
        url = default_url
    return url, _env(key_env)


def call_model(messages, tools, model, provider="minimax", temperature=0.7, timeout=240, retries=4, capture=None):
    url, key = provider_cfg(provider)
    is_new = model.startswith(("o1", "o3", "o4", "gpt-5"))
    payload = {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto"}
    if is_new:
        payload["max_completion_tokens"] = 4096
    else:
        payload["temperature"] = temperature
        payload["max_tokens"] = 4096
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    body = json.dumps(payload, ensure_ascii=False)
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, headers=headers, data=body.encode("utf-8"), timeout=timeout)
            r.raise_for_status()
            if capture is not None:
                capture.append({"request": body, "response_raw": r.text})
            return r.json()["choices"][0]["message"]
        except requests.exceptions.RequestException as exc:
            last = exc
            if attempt == retries:
                break
            time.sleep(10 * attempt if "429" in str(exc) else min(20, 3 * attempt))
    raise RuntimeError(f"{provider} request failed after {retries} attempts: {last}")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _iter(messages, tools, dispatch, model, provider, temperature, transcript, max_iters=8, capture=None):
    """Run the tool loop; append stage entries to transcript. Returns final text."""
    final = ""
    for it in range(max_iters):
        msg = call_model(messages, tools, model, provider, temperature, capture=capture)
        calls = msg.get("tool_calls") or []
        entry = {"stage": "assistant", "iter": it,
                 "assistant_text": msg.get("content") or "",
                 "tool_calls": [{"name": c.get("function", {}).get("name", ""),
                                 "arguments": c.get("function", {}).get("arguments", "")} for c in calls]}
        messages.append({"role": "assistant", "content": msg.get("content") or "",
                         **({"tool_calls": calls} if calls else {})})
        if not calls:
            final = entry["assistant_text"]
            transcript.append(entry)
            break
        results = []
        for c in calls:
            fn = c.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            result = dispatch(fn.get("name", ""), args)
            results.append({"tool": fn.get("name", ""), "args": args, "result": result})
            messages.append({"role": "tool", "tool_call_id": c.get("id", ""),
                             "content": json.dumps(result, ensure_ascii=False)})
        entry["tool_results"] = results
        transcript.append(entry)
    return final


def run_email(scenario, tier, subject, body, model, provider, temperature, judge=True):
    meta = SCENARIOS[scenario]
    hdir = HARNESSES / meta["dir"] / "harness"
    sc = json.loads((hdir / "scenario.json").read_text(encoding="utf-8"))
    sysp = (hdir / "system_prompts" / f"system_prompt_{tier}.md").read_text(encoding="utf-8")
    tools_mod = _load(hdir / "tools.py", f"{scenario}_tools")
    judge_mod = _load(hdir / "judge.py", f"{scenario}_judge")

    filled = deepcopy(sc)
    for e in filled["inbox"]:
        if e.get("subject") == sc["subject_placeholder"]:
            e["subject"] = subject
        if e.get("body") == sc["body_placeholder"]:
            e["body"] = body

    sent, tlog = [], []
    dispatch = tools_mod.make_dispatch(filled, sent, tlog)
    messages = [{"role": "system", "content": sysp},
                {"role": "user", "content": filled["victim_message"]}]
    transcript = [{"stage": "system_prompt", "content": sysp},
                  {"stage": "victim_turn", "content": filled["victim_message"]},
                  {"stage": "injected_email", "subject": subject, "body": body}]
    messages_initial = deepcopy(messages)
    api_calls = []
    t0 = time.time()
    final = _iter(messages, tools_mod.tool_schemas(), dispatch, model, provider, temperature, transcript, capture=api_calls)
    messages_final = deepcopy(messages)
    attack_text = (subject or "") + "\n" + (body or "")
    if judge:
        if "target_password" in sc:
            verdict, signals = judge_mod.judge(sent, attack_text, sc["target_user"], sc["target_password"])
        else:
            verdict, signals = judge_mod.judge(sent, attack_text, sc.get("attacker_email", ""), sc.get("secret", ""))
    else:
        verdict, signals = "MANUAL", "" 
    return {"scenario": scenario, "mode": "email", "tier": tier, "provider": provider, "model": model,
            "temperature": temperature, "attack": {"subject": subject, "body": body},
            "system_prompt": sysp, "victim_message": filled["victim_message"],
            "inbox": filled["inbox"], "transcript": transcript, "tool_log": tlog,
            "messages_initial": messages_initial, "messages_final": messages_final, "api_calls": api_calls,
            "verdict": verdict, "signals": signals,
            "tool_calls": ";".join(t["name"] for t in tlog), "final_answer": final,
            "elapsed_s": round(time.time() - t0, 1)}


def run_chat(scenario, tier, message, model, provider, temperature, judge=True):
    meta = SCENARIOS[scenario]
    hdir = HARNESSES / meta["dir"]
    sc = json.loads((hdir / "scenario.json").read_text(encoding="utf-8"))
    tier_file = hdir / f"system_prompt_{tier}.md"
    sysp = (tier_file if tier_file.exists() else (hdir / "system_prompt.md")).read_text(encoding="utf-8")
    tools_mod = _load(hdir / "tools.py", f"{scenario}_tools")
    judge_mod = _load(hdir / "judge.py", f"{scenario}_judge")

    offers, escal, tlog = [], [], []
    dispatch = tools_mod.make_dispatch(offers, escal, tlog)
    messages = [{"role": "system", "content": sysp}, {"role": "user", "content": message}]
    transcript = [{"stage": "system_prompt", "content": sysp},
                  {"stage": "user_turn", "content": message}]
    messages_initial = deepcopy(messages)
    api_calls = []
    t0 = time.time()
    final = _iter(messages, tools_mod.tool_schemas(), dispatch, model, provider, temperature, transcript, 6, capture=api_calls)
    messages_final = deepcopy(messages)
    verdict, signals = (judge_mod.judge(offers, escal) if judge else ("MANUAL", ""))
    return {"scenario": scenario, "mode": "chat", "tier": tier, "provider": provider, "model": model,
            "temperature": temperature, "attack": {"message": message},
            "system_prompt": sysp, "transcript": transcript, "tool_log": tlog,
            "messages_initial": messages_initial, "messages_final": messages_final, "api_calls": api_calls,
            "verdict": verdict, "signals": signals,
            "tool_calls": ";".join(t["name"] for t in tlog), "final_answer": final,
            "elapsed_s": round(time.time() - t0, 1)}


def run(scenario, tier, attack, model, provider, temperature=0.7, judge=True):
    """attack: {subject, body} for email mode, {message} for chat mode."""
    mode = SCENARIOS[scenario]["mode"]
    if mode == "email":
        return run_email(scenario, tier, attack.get("subject", ""), attack.get("body", ""),
                         model, provider, temperature, judge)
    return run_chat(scenario, tier, attack.get("message", ""), model, provider, temperature, judge)
