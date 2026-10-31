#!/usr/bin/env python3
"""Dump a scenario's success criteria to arena/state/criteria/<scenario>.md.

Use when a scenario is confounded: re-read the judge's exact wording and the
"injection surface the agent will encounter by default" block.

    python3 arena/criteria.py --scenario S4
    python3 arena/criteria.py --all

Run only when no other process is driving the gateway: the browser has one
active page.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request

GW = "http://127.0.0.1:8787"
ARENA = "https://app.grayswan.ai/arena/challenge/ipi-black-2026"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "criteria")

CARDS = {
    "S1": "WB2S1 - Issue Unauthorized Refund",
    "S2": "WB2S2 - Redirect Order to Attacker-Controlled Address",
    "S3": "WB2S3 - Change Product Price",
    "S4": "WB2S4 - Cancel Target Order",
    "S5": "WB2S5 - Exfiltrate Customer Records",
    "B1": "BB1S1 - Private Appointment Disclosure",
    "B2": "BB1S2 - Private Document Disclosure",
    "B3": "BB1S3 - Private Journal Disclosure",
    "B4": "BB1S4 - Local Credential Disclosure",
    "B5": "BB1S5 - Notes App Code Sabotage",
    "B6": "BB1S6 - Personal Data Deletion",
    "B7": "BB1S7 - Schedule Note Tampering",
}

BUTTONS = ("SEE SUCCESS CRITERIA", "View scenario criteria", "SEE CRITERIA")


def api(path: str, body=None, timeout: int = 60):
    req = urllib.request.Request(
        GW + path, method="POST" if body is not None else "GET",
        data=None if body is None else json.dumps(body).encode(),
        headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def js(code: str):
    return api("/eval", {"js": code})["result"]


def click(name: str, role: str = "button", force: bool = True) -> bool:
    try:
        api("/click", {"role": role, "name": name, "force": force})
        return True
    except Exception:
        return False


def select(card: str) -> bool:
    for _ in range(4):
        js(f"() => {{ const b=[...document.querySelectorAll('button')]"
           f".find(x=>(x.innerText||'').includes({json.dumps(card)}));"
           f" if(b) b.click(); return !!b; }}")
        time.sleep(1.5)
        t = js("()=>document.body.innerText")
        if "HARMFUL TASK" in t and card.split(" - ")[0] in t:
            return True
    return False


def dump(key: str) -> str:
    card = CARDS[key]
    api("/open", {"url": ARENA})
    time.sleep(3)
    if not select(card):
        return f"{key}: scenario would not select"
    opened = False
    for name in BUTTONS:
        if click(name):
            time.sleep(1.5)
            if "Scenario criteria" in js("()=>document.body.innerText"):
                opened = True
                break
    if not opened:
        click("View scenario criteria")
        time.sleep(1.5)
    text = js("""() => { const t=document.body.innerText; const i=t.indexOf('Scenario criteria');
                   return i>=0 ? t.slice(i) : t.slice(-4000); }""")
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{key}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# {card}\n\n{text}\n")
    # close any dialog
    click("Close")
    return f"{key}: {len(text)} chars -> {path}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=sorted(CARDS))
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    keys = sorted(CARDS) if args.all else [args.scenario]
    if not keys or keys == [None]:
        ap.error("pass --scenario KEY or --all")
    for k in keys:
        print(dump(k), flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
