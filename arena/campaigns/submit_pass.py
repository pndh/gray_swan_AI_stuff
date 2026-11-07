#!/usr/bin/env python3
"""Rescue pass: click SUBMIT BREAK on our runs that never reached the judge.

Needs no energy. Runs on its own gateway so it never blocks a campaign worker.
Loops until the deadline, one pass every PASS_EVERY seconds.
"""
import os, sys, time, json
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import run, opt

STATE = os.path.join(os.path.dirname(HERE), "state")
LOG = os.path.join(STATE, "submitpass.log")
OUT = os.path.join(STATE, "submitpass.jsonl")
DONE = os.path.join(STATE, "submitpass_done.json")
DEADLINE = sys.argv[1] if len(sys.argv) > 1 else "0800"
PASS_EVERY = 600
MAX = 25


def log(m):
    line = "%s %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")


end = datetime.now().replace(hour=int(DEADLINE[:2]), minute=int(DEADLINE[2:]),
                             second=0, microsecond=0)
if end < datetime.now():
    end += timedelta(days=1)
log("=== submit-pass start | deadline %s | gw=%s ===" % (end.strftime("%H:%M"), run.GW))
run.ensure_gateway()

while datetime.now() < end:
    rows = [json.loads(l) for l in open(os.path.join(STATE, "runs.jsonl")) if l.strip()]
    try:
        already = set(json.load(open(DONE)))
    except Exception:
        already = set()
    todo, seen = [], set()
    for r in rows:
        tag = str(r.get("tag", ""))
        if not tag.startswith(("TSE2.", "BHJ2.", "RHI2.", "TSE2", "AOD", "FIRE.", "SEM.", "W2.")):
            continue
        c = r.get("chat")
        if not c or c in seen or c in already:
            continue
        seen.add(c)
        if opt.fast_poll(c) in ("ACCEPTED", "REJECTED", "HUNG", "RUNFAIL"):
            continue
        todo.append(r)
    log("unjudged: %d" % len(todo))
    n = 0
    for r in todo[:MAX]:
        c = r["chat"]
        try:
            run.open_("https://app.grayswan.ai/arena/challenge/ipi-black-2026?chatId=" + c, 60)
            time.sleep(7)
            b = run.js("""()=>{const x=[...document.querySelectorAll('button')].find(e=>/SUBMIT BREAK/i.test(e.innerText||''));return x?{dis:x.disabled}:null}""")
            act = "disabled" if (b and b["dis"]) else ("absent" if not b else None)
            if b and not b["dis"]:
                act = run.js("""()=>{const x=[...document.querySelectorAll('button')].find(e=>/SUBMIT BREAK/i.test(e.innerText||''));if(!x||x.disabled)return 'gone';x.click();return 'submitted'}""")
                if act == "submitted":
                    n += 1
            if act in ("submitted", "gone"):
                already.add(c)
                json.dump(sorted(already), open(DONE, "w"))
            open(OUT, "a").write(json.dumps({"tag": r.get("tag"), "chat": c, "action": act}) + "\n")
            if act == "submitted":
                log("SUBMITTED %s %s" % (r.get("tag"), c[:10]))
        except Exception as e:
            pass
        time.sleep(1.5)
    log("pass done: submitted %d" % n)
    time.sleep(PASS_EVERY)
log("=== submit-pass done ===")
