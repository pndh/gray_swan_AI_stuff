#!/usr/bin/env python3
"""Watchdog for the overnight campaign.

Every 5 minutes:
  - ensure each gateway (8787/8788/8789) answers /health, restarting it if not
  - ensure each auto2.py worker is alive, restarting it with the right ARENA_GW
Stops at the deadline.
"""
import os, time, json, subprocess, urllib.request, sys
from datetime import datetime, timedelta

REPO = "/home/pndhpndh/CoT_Viettel/gray_swan_AI"
STATE = os.path.join(REPO, "arena", "state")
LOG = os.path.join(STATE, "watchdog.log")
DEADLINE = sys.argv[1] if len(sys.argv) > 1 else "0800"

WORKERS = [("TSE", 8787), ("BHJ", 8788), ("RHI", 8789)]
PROFILE = {8787: "profile", 8788: "profile-8788", 8789: "profile-8789"}


def log(m):
    line = "%s %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")


def health(port):
    try:
        r = urllib.request.urlopen("http://127.0.0.1:%d/health" % port, timeout=4)
        return json.load(r).get("ok") is True
    except Exception:
        return False


def start_gateway(port):
    env = dict(os.environ, ARENA_PORT=str(port),
               ARENA_PROFILE=os.path.join(STATE, PROFILE[port]))
    subprocess.Popen(["bash", "arena/run.sh"], cwd=REPO, env=env,
                     stdout=open("/tmp/opencode/gw_%d.log" % port, "a"),
                     stderr=subprocess.STDOUT, start_new_session=True, stdin=subprocess.DEVNULL)


def start_worker(tag, port):
    env = dict(os.environ, ARENA_GW="http://127.0.0.1:%d" % port)
    subprocess.Popen([sys.executable, "arena/campaigns/auto2.py", tag, DEADLINE],
                     cwd=REPO, env=env,
                     stdout=open("/tmp/opencode/a2_%s.log" % tag.lower(), "a"),
                     stderr=subprocess.STDOUT, start_new_session=True, stdin=subprocess.DEVNULL)


def worker_alive(tag):
    try:
        out = subprocess.check_output(["pgrep", "-f", "auto2.py %s" % tag]).decode()
        return bool(out.strip())
    except subprocess.CalledProcessError:
        return False


end = datetime.now().replace(hour=int(DEADLINE[:2]), minute=int(DEADLINE[2:]),
                             second=0, microsecond=0)
if end < datetime.now():
    end += timedelta(days=1)
log("=== watchdog start | deadline %s ===" % end.strftime("%H:%M"))
while datetime.now() < end:
    for tag, port in WORKERS:
        if not health(port):
            log("gateway %d DOWN -> restart" % port)
            start_gateway(port)
            time.sleep(20)
        if not worker_alive(tag):
            log("worker %s dead -> restart on %d" % (tag, port))
            start_worker(tag, port)
            time.sleep(3)
    time.sleep(300)
log("=== watchdog done ===")
