#!/usr/bin/env python3
"""Wait-for-energy supervisor, runs until the deadline.

Every cycle:
  1. make sure each gateway answers /health (start it if not)
  2. read /state -> energy on every port, log it
  3. if a port has enough energy (>=40) and its worker is not running, start it
  4. when a worker finishes and energy remains, restart it
  5. until deadline

This replaces the earlier "stop when I saw 5 energy" behaviour: it keeps watching
for regeneration and resumes automatically the moment launches are possible.
"""
import os, sys, time, json, subprocess, urllib.request
from datetime import datetime, timedelta

REPO = "/home/pndhpndh/CoT_Viettel/gray_swan_AI"
STATE = os.path.join(REPO, "arena", "state")
LOG = os.path.join(STATE, "regen.log")
DEADLINE = sys.argv[1] if len(sys.argv) > 1 else "0800"
COST = 20
MIN_TO_START = 40          # enough for at least two launches
CYCLE = 180

WORKERS = [("TSE", 8787), ("BHJ", 8788), ("RHI", 8789)]
PROFILE = {8787: "profile", 8788: "profile-8788", 8789: "profile-8789"}


def log(m):
    line = "%s %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")


def get(port, path, timeout=6):
    r = urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=timeout)
    return json.load(r)


def start_gateway(port):
    env = dict(os.environ, ARENA_PORT=str(port),
               ARENA_PROFILE=os.path.join(STATE, PROFILE[port]))
    subprocess.Popen(["bash", "arena/run.sh"], cwd=REPO, env=env,
                     stdout=open("/tmp/opencode/gw_%d.log" % port, "a"),
                     stderr=subprocess.STDOUT, start_new_session=True,
                     stdin=subprocess.DEVNULL)


def start_worker(tag, port):
    env = dict(os.environ, ARENA_GW="http://127.0.0.1:%d" % port)
    subprocess.Popen([sys.executable, "arena/campaigns/auto2.py", tag, DEADLINE],
                     cwd=REPO, env=env,
                     stdout=open("/tmp/opencode/a2_%s.log" % tag.lower(), "a"),
                     stderr=subprocess.STDOUT, start_new_session=True,
                     stdin=subprocess.DEVNULL)


def alive(tag):
    try:
        return bool(subprocess.check_output(["pgrep", "-f", "auto2.py %s" % tag]).strip())
    except subprocess.CalledProcessError:
        return False


end = datetime.now().replace(hour=int(DEADLINE[:2]), minute=int(DEADLINE[2:]),
                             second=0, microsecond=0)
if end < datetime.now():
    end += timedelta(days=1)

log("=== regen supervisor start | deadline %s | need >=%d energy to launch ===" % (end.strftime("%H:%M"), MIN_TO_START))
last = {}
while datetime.now() < end:
    line = []
    for tag, port in WORKERS:
        energy = None
        try:
            st = get(port, "/state")
            energy = (st.get("energy") or {}).get("now")
        except Exception:
            start_gateway(port)
            time.sleep(15)
            try:
                st = get(port, "/state")
                energy = (st.get("energy") or {}).get("now")
            except Exception:
                pass
        line.append("%s:%s" % (tag, energy))
        if energy is not None and energy >= MIN_TO_START and not alive(tag):
            log("%s energy=%s -> starting worker on %d" % (tag, energy, port))
            start_worker(tag, port)
            time.sleep(3)
    log("energy " + "  ".join(line) + "  | workers: %s" % ",".join(t for t, _ in WORKERS if alive(t)))
    time.sleep(CYCLE)
log("=== regen supervisor done ===")
