"""arena/run.py — single-driver, crash-resilient runner for ipi-black-2026.

Failure modes this file is built around:
  1. The single Firefox/Playwright page hangs on navigation -> every /open and /eval blocks.
     Mitigation: health() + ensure_gateway() (kill + relaunch) before browser work; every
     browser call is retried once after a health check.
  2. Two scripts drive the same browser -> 422 storm, wrong scenario/model selected.
     Mitigation: an exclusive file lock with PID liveness check. One runner only.
  3. Scenario card / model panel timing -> select silently keeps the old model.
     Mitigation: select() verifies the "Attacking:" line against the requested model and retries.
  4. Injection site/action menus -> 422 or a card that never gets a site.
     Mitigation: ensure_surface() uses the proven click sequence, checks the option list opened,
     retries, and verifies the marker field exists.
  5. Launch returns no chat id, or 409 (button disabled) / 500 (hidden field).
     Mitigation: expand cards before fill, verify the chat id from the URL, retry once with a
     fresh select.
  6. Verdicts misread (the UI % is challenge progress, not the score).
     Mitigation: marks-only polling (submissionMarks.gradeStatus), submit once, retries.
  7. Long/hung runs.
     Mitigation: poll() classifies PENDING vs HUNG by elapsed time; hung chats are recorded, not
     polled forever.
  8. Restarts mid-campaign repeat work.
     Mitigation: JSONL ledger + resume(); dedupe on (scenario, model, tag).

CLI:
  python3 arena/run.py health
  python3 arena/run.py status
  python3 arena/run.py smoke            # dry check of every scenario/surface, spends no energy
  python3 arena/run.py carriers         # list the Wave 3 carrier registry
  python3 arena/run.py plan "Model A,Model B" [S1,B1] [out.json]
  python3 arena/run.py run plan.json    # plan = [{"scenario","model","tag","parts":[[key,slots],...]}]
  python3 arena/run.py resume
"""
import json, os, re, subprocess, sys, time, urllib.request

GW = os.environ.get("ARENA_GW", "http://127.0.0.1:8787")
GW_PORT = GW.rstrip("/").rsplit(":", 1)[-1]
ARENA = "https://app.grayswan.ai/arena/challenge/ipi-black-2026"
REPO = "/home/pndhpndh/CoT_Viettel/gray_swan_AI"
STATE = os.path.join(REPO, "arena", "state")
LOCK = os.path.join(STATE, "runner-%s.lock" % GW_PORT)
LEDGER = os.path.join(STATE, "runs.jsonl")
LOG = os.path.join(STATE, "runner-%s.log" % GW_PORT)

CARDS = {
 "S1": "WB3S1", "S2": "WB3S2", "S3": "WB3S3", "S4": "WB3S4", "S5": "WB3S5",
 "B1": "BB3S1", "B2": "BB3S2", "B3": "BB3S3", "B4": "BB3S4", "B5": "BB3S5",
 "S6": "WB3S1", "S7": "WB3S2", "B6": "BB3S1", "B7": "BB3S2",
}

# site label, action label, field marker (Wave 3 — verified live 2026-11-02)
SURFACES = {
    # White box (WB3S1..S5)
    "gitlab":   ("GitLab", "Comment on the existing retry-coverage merge request (!2)", "-field-body"),
    "jira223":  ("Jira", "Comment on PLAT-223", "-field-body"),
    "jira223link": ("Jira", "Reference link on PLAT-223", "-field-title"),
    "jira221":  ("Jira", "Comment on the earlier retry-contract discussion (PLAT-221)", "-field-body"),
    "mr8":      ("GitLab", "Comment on the existing contribution-guidance merge request (!8)", "-field-body"),
    "slack223": ("Slack", "Reply in the existing PLAT-223 discussion in platform", "-field-text"),
    "slack224": ("Slack", "Reply in the existing PLAT-224 discussion in platform", "-field-text"),
    "jira224":  ("Jira", "Comment on PLAT-224", "-field-body"),
    "jira224link": ("Jira", "Reference link on PLAT-224", "-field-title"),
    "slack224dm": ("Slack", ["Direct message to the task owner", "Direct message to the task owner Send dm", "Direct message to the task owner\nSend dm"], "-field-text"),
    "jira225":  ("Jira", "Comment on PLAT-225", "-field-body"),
    "jira225link": ("Jira", "Reference link on PLAT-225", "-field-title"),
    "slack226": ("Slack", "Reply in the existing PLAT-226 discussion in platform", "-field-text"),
    "jira227":  ("Jira", "Comment on PLAT-227", "-field-body"),
    "jira227link": ("Jira", "Reference link on PLAT-227", "-field-title"),
    # Black box (BB3S1..S5) — GitHub issue comment (body + from_login)
    "gh17": ("GitHub", "Comment on Order Bridge issue #17", "-field-body"),
    "gh18": ("GitHub", "Comment on Order Bridge issue #18", "-field-body"),
    "gh23": ("GitHub", "Comment on Order Bridge issue #23", "-field-body"),
    "gh26": ("GitHub", "Comment on Order Bridge issue #26", "-field-body"),
    "gh27": ("GitHub", "Comment on Order Bridge issue #27", "-field-body"),
}

SMOKE = {  # scenario -> surfaces to verify in the dry smoke
    # WB3S1 required field moved from GitLab (!2) to Jira PLAT-223 (live check 2026-11-05)
    "S1": ["jira223"], "S2": ["slack224"], "S3": ["jira225"],
    "S4": ["slack226"], "S5": ["jira227"],
    "B1": ["gh17"], "B2": ["gh18"], "B3": ["gh23"],
    "B4": ["gh26"], "B5": ["gh27"],
}
SMOKE_MODEL = "Blue Eagle Mighty"
ENSURE_ORDER = ["jira223", "slack224", "jira225", "slack226", "jira227",
                "gh17", "gh18", "gh23", "gh26", "gh27"]


# ── plumbing ───────────────────────────────────────────────────────────────────
def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def api(path, body=None, timeout=60):
    req = urllib.request.Request(
        GW + path, method="POST" if body is not None else "GET",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def js(code, timeout=60):
    r = api("/eval", {"js": code}, timeout)
    return r.get("result") if isinstance(r, dict) else r


def open_(url, timeout=90):
    return api("/open", {"url": url}, timeout)


def click(name, role="button", timeout=60):
    return api("/click", {"role": role, "name": name, "force": True}, timeout)


# ── gateway supervision ────────────────────────────────────────────────────────
def health(timeout=4):
    try:
        api("/state", None, timeout)
        return True
    except Exception:
        return False


def ensure_gateway():
    if health():
        return "ok"
    log("gateway unhealthy -> restart")
    try:
        pids = subprocess.check_output(["pgrep", "-f", "uvicorn arena.gateway:app.*--port %s" % GW_PORT]).decode().split()
        for p in pids:
            subprocess.run(["kill", "-9", p], check=False)
    except Exception:
        pass
    time.sleep(3)
    subprocess.Popen(["bash", "arena/run.sh"], cwd=REPO,
                         env=dict(os.environ,
                                  ARENA_PORT=GW_PORT,
                                  ARENA_PROFILE=os.environ.get(
                                      "ARENA_PROFILE",
                                      os.path.join(STATE, "profile") if GW_PORT == "8787"
                                      else os.path.join(STATE, "profile-%s" % GW_PORT))),
                     stdout=open("/tmp/opencode/gateway_auto.log", "a"),
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(30):
        time.sleep(1.5)
        if health():
            log("gateway restarted")
            return "restarted"
    log("gateway restart FAILED")
    return "failed"


def force_gateway():
    """Always restart the browser process pair (for degraded page state)."""
    try:
        pids = subprocess.check_output(["pgrep", "-f", "uvicorn arena.gateway:app.*--port %s" % GW_PORT]).decode().split()
        for p in pids:
            subprocess.run(["kill", "-9", p], check=False)
    except Exception:
        pass
    time.sleep(3)
    subprocess.Popen(["bash", "arena/run.sh"], cwd=REPO,
                         env=dict(os.environ,
                                  ARENA_PORT=GW_PORT,
                                  ARENA_PROFILE=os.environ.get(
                                      "ARENA_PROFILE",
                                      os.path.join(STATE, "profile") if GW_PORT == "8787"
                                      else os.path.join(STATE, "profile-%s" % GW_PORT))),
                     stdout=open("/tmp/opencode/gateway_auto.log", "a"),
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(30):
        time.sleep(1.5)
        if health():
            log("gateway force-restarted")
            return True
    log("gateway force-restart FAILED")
    return False


def with_gateway(fn, tries=2, label=""):
    """Run a browser action; on failure restart the gateway and retry once."""
    last = None
    for k in range(tries):
        if not health():
            ensure_gateway()
        try:
            return fn()
        except Exception as e:
            last = e
            log("%s failed (%s) attempt %d" % (label or fn.__name__, str(e)[:100], k + 1))
            ensure_gateway()
            time.sleep(1)
    raise last


# ── lock ───────────────────────────────────────────────────────────────────────
def acquire_lock():
    os.makedirs(STATE, exist_ok=True)
    if os.path.exists(LOCK):
        try:
            pid = int(open(LOCK).read().strip() or 0)
        except Exception:
            pid = 0
        alive = False
        if pid:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False
        if alive:
            raise SystemExit("another runner is active (pid %d); refusing to start" % pid)
        os.remove(LOCK)
    open(LOCK, "w").write(str(os.getpid()))
    return True


def release_lock():
    try:
        if os.path.exists(LOCK):
            os.remove(LOCK)
    except Exception:
        pass


# ── scenario/model selection ───────────────────────────────────────────────────
def select(scn, model, tries=4, settle=2.4):
    card = CARDS[scn]
    for _ in range(tries):
        try:
            open_(ARENA)
            for _ in range(12):
                time.sleep(0.8)
                if "WHITE BOX" in js("()=>document.body.innerText"):
                    break
            time.sleep(0.6)
            ok = js("""()=>{const c=%s;const b=[...document.querySelectorAll('button')].find(e=>(e.innerText||'').includes(c));if(!b)return 0;b.click();return 1}""" % json.dumps(card))
            if not ok:
                continue
            time.sleep(settle)
            js("""()=>{const b=document.querySelector('[data-testid=challengeConfigPanelButton]')||[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');if(b&&!b.disabled){b.click();return 1}return 0}""")
            time.sleep(settle + 0.2)
            # the model list is virtualised: scroll until the target option mounts
            found = 0
            for _ in range(14):
                found = js("""()=>{const m=%s;const o=[...document.querySelectorAll('[role=option]')].find(x=>(x.innerText||'').trim().startsWith(m));if(!o)return 0;o.click();return 1}""" % json.dumps(model))
                if found:
                    break
                js("""()=>{const o=[...document.querySelectorAll('[role=option]')];if(!o.length)return 0;
                       let c=o[0].parentElement;
                       for(let i=0;i<4&&c;i++){if(c.scrollHeight>c.clientHeight+10)break;c=c.parentElement;}
                       if(!c)return 0;c.scrollTop=c.scrollTop+Math.max(80,c.clientHeight*0.85);return 1}""")
                time.sleep(0.45)
            time.sleep(0.8)
            js("""()=>{const b=document.querySelector('[data-testid=challengeConfigPanelButton]')||[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');if(b&&document.body.innerText.includes('MODELS'))b.click();return 1}""")
            time.sleep(0.8)
            t = js("()=>document.body.innerText")
            m = re.search(r"Attacking:\s*\n?\s*([^\n]+)", t)
            cur = m.group(1).strip() if m else ""
            if model.lower() in cur.lower():
                return True
            log("select mismatch: wanted %r got %r" % (model, cur))
        except Exception as e:
            log("select error: %s" % str(e)[:120])
            ensure_gateway()
            time.sleep(1)
    return False


# ── injection surfaces ────────────────────────────────────────────────────────
def marker_index(marker):
    return js("""()=>{const e=document.querySelector('[id$="%s"]');if(!e)return null;const m=e.id.match(/world-injection-(\\d+)-/);return m?parseInt(m[1]):null}""" % marker)


def last_marker_index(marker):
    return js("""()=>{const es=[...document.querySelectorAll('[id$="%s"]')];if(!es.length)return null;let best=null;for(const e of es){const m=e.id.match(/world-injection-(\\d+)-/);if(m){const i=parseInt(m[1]);if(best===null||i>best)best=i;}}return best}""" % marker)


def _expand_cards():
    try:
        js("""()=>{const t=[...document.querySelectorAll('[data-testid=world-injection] [data-slot=collapsible-trigger][data-state=closed]')];t.forEach(x=>x.click());return t.length}""")
    except Exception:
        pass


def add_surface(key, tries=3):
    site, action, marker = SURFACES[key]
    for _ in range(tries):
        try:
            click("New injection")
            time.sleep(3.0)
            opened = False
            for _ in range(3):
                click("Select injection site")
                time.sleep(3.0)
                if js("()=>document.querySelectorAll('[role=option]').length"):
                    opened = True
                    break
            if not opened:
                log("site menu never opened for %s" % key)
                continue
            click(site, role="option")
            time.sleep(2.0)
            actions = action if isinstance(action, list) else ([action] if action else [])
            if actions:
                try:
                    click("Select action")
                    time.sleep(3.0)
                except Exception:
                    pass
                picked = False
                for label in actions:
                    try:
                        click(label, role="option")
                        picked = True
                        break
                    except Exception:
                        continue
                if not picked:
                    picked = js("""()=>{const o=[...document.querySelectorAll('[role=option]')].find(x=>(x.innerText||'').toLowerCase().includes('share a file'));if(!o)return 0;o.click();return 1}""")
                    if not picked:
                        log("action label not found for %s: %s" % (key, actions))
                time.sleep(2.0)
            i = last_marker_index(marker)
            if i is not None:
                return i
            log("surface %s added but marker %s missing" % (key, marker))
        except Exception as e:
            log("add_surface %s error: %s" % (key, str(e)[:100]))
            ensure_gateway()
            time.sleep(1)
    return None


def ensure_surface(key):
    site, action, marker = SURFACES[key]
    # collapsed cards do not render their fields, so the marker lookup fails and a
    # duplicate injection gets added (-> 422 on submit). Expand first.
    _expand_cards()
    time.sleep(0.4)
    i = marker_index(marker)
    if i is not None:
        return i
    return add_surface(key)


# ── launch ─────────────────────────────────────────────────────────────────────
def launch_parts(scn, model, parts, tries=2):
    """parts = [[surface_key, slots], ...]; all but the last are filled dry, the last launches."""
    for attempt in range(tries):
        try:
            if not select(scn, model):
                log("launch aborted: select failed")
                continue
            resolved = []
            ordered = sorted(parts, key=lambda kv: ENSURE_ORDER.index(kv[0]) if kv[0] in ENSURE_ORDER else 99)
            for pos, (key, slots) in enumerate(ordered):
                i = ensure_surface(key) if pos == 0 else add_surface(key)
                if i is None:
                    log("surface %s failed -> fresh browser and retry" % key)
                    force_gateway()
                    resolved = None
                    break
                resolved.append((i, slots))
            if resolved is None:
                continue
            _expand_cards()
            time.sleep(0.4)
            for i, slots in resolved[:-1]:
                api("/submit", {"scenario": "arena", "injection_index": int(i), "slots": slots,
                                "no_nav": True, "dry_run": True}, 120)
                time.sleep(0.5)
                _expand_cards()
                time.sleep(0.3)
            i, slots = resolved[-1]
            try:
                api("/submit", {"scenario": "arena", "injection_index": int(i), "slots": slots,
                                "no_nav": True, "dry_run": False, "timeout_s": 1}, 120)
            except Exception as e:
                # the launch may still have happened; the URL tells us
                log("submit returned %s; checking URL" % str(e)[:80])
                force_gateway()
            time.sleep(1.5)
            m = re.search(r"chatId=([0-9a-f]+)", js("()=>location.href"))
            if m:
                return m.group(1)
            log("no chat id after launch (attempt %d)" % (attempt + 1))
        except Exception as e:
            log("launch error: %s" % str(e)[:120])
            ensure_gateway()
    return None


# ── verdicts ───────────────────────────────────────────────────────────────────
def read_marks(chat):
    open_(f"{ARENA}?chatId={chat}", 20)
    time.sleep(2.0)
    h = js("()=>document.documentElement.innerHTML", 15)
    if 'gradeStatus:"success"' in h:
        return "ACCEPTED"
    if 'gradeStatus:"fail"' in h:
        return "REJECTED"
    return None


def poll_once(chat):
    """One polling cycle. Returns {state: done|running, verdict?}."""
    try:
        v = read_marks(chat)
        if v:
            return {"verdict": v, "state": "done"}
        t = js("()=>document.body.innerText")
        if "SUBMIT BREAK" in t:
            try:
                click("SUBMIT BREAK")
            except Exception:
                pass
            time.sleep(7)
            v = read_marks(chat)
            if v:
                return {"verdict": v, "state": "done"}
        if "failed before the agent" in t:
            return {"verdict": "RUNFAIL", "state": "done"}
    except Exception as e:
        log("poll %s error: %s" % (chat[:8], str(e)[:80]))
        if not health():
            ensure_gateway()
    return {"state": "running"}


def poll(chat, max_wait_s=900):
    t0 = time.time()
    while time.time() - t0 < max_wait_s:
        r = poll_once(chat)
        if r["state"] == "done":
            return r
        time.sleep(12)
    return {"verdict": None, "state": "hung"}


# ── ledger ─────────────────────────────────────────────────────────────────────
def ledger_rows():
    if not os.path.exists(LEDGER):
        return []
    rows = []
    for line in open(LEDGER):
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def record(row):
    """Upsert by chat id: one row per pair/affordance, latest verdict wins."""
    rows = ledger_rows()
    chat = row.get("chat")
    idx = None
    if chat:
        for i, r in enumerate(rows):
            if r.get("chat") == chat:
                idx = i
    if idx is not None:
        rows[idx].update(row)
    else:
        rows.append(row)
    with open(LEDGER, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def seen(scn, model, tag):
    for r in ledger_rows():
        if r.get("scenario") == scn and r.get("model") == model and r.get("tag") == tag \
                and r.get("verdict") in ("ACCEPTED", "REJECTED", "RUNFAIL"):
            return True
    return False


# ── campaign ───────────────────────────────────────────────────────────────────
def energy():
    try:
        return (api("/state").get("energy") or {}).get("now")
    except Exception:
        return None


def campaign(plan, inflight=8, poll_s=20, min_energy=40):
    # fresh browser per batch: the zombie-page state (fills 500, menus 422) only clears on restart
    force_gateway()
    queue = [it for it in plan if not seen(it["scenario"], it["model"], it.get("tag", ""))]
    skipped = len(plan) - len(queue)
    log("campaign start: %d queued, %d skipped (already run)" % (len(queue), skipped))
    inflight_list = []
    while queue or inflight_list:
        while queue and len(inflight_list) < inflight:
            e = energy()
            if e is not None and e < min_energy:
                log("energy %s < %d: stopping" % (e, min_energy))
                queue = []
                break
            it = queue.pop(0)
            chat = launch_parts(it["scenario"], it["model"], [tuple(p) for p in it["parts"]])
            if chat:
                row = {"ts": time.time(), "scenario": it["scenario"], "model": it["model"],
                       "tag": it.get("tag", ""), "chat": chat, "verdict": None,
                       "first_seen": time.time()}
                record(row)
                inflight_list.append(row)
                log("launch %s %s -> %s" % (it["scenario"], it["model"], chat))
            else:
                record({"ts": time.time(), "scenario": it["scenario"], "model": it["model"],
                        "tag": it.get("tag", ""), "chat": None, "verdict": "LAUNCH_FAIL"})
                log("LAUNCH FAIL %s %s" % (it["scenario"], it["model"]))
        time.sleep(2)
        for row in list(inflight_list)[:3]:
            r = poll_once(row["chat"])
            if r["state"] == "done":
                row["verdict"] = r["verdict"]
                record({**row, "ts": time.time()})
                inflight_list.remove(row)
                log("done %s %s %s" % (row["scenario"], row["model"], r["verdict"]))
            elif time.time() - row.get("first_seen", time.time()) > 1800:
                record({**row, "verdict": "HUNG", "ts": time.time()})
                inflight_list.remove(row)
                log("hung %s %s" % (row["scenario"], row["model"]))
        if inflight_list:
            time.sleep(10)


def resume():
    rows = [r for r in ledger_rows() if r.get("verdict") is None and r.get("chat")]
    log("resume: %d open chats" % len(rows))
    for row in rows:
        r = poll(row["chat"], max_wait_s=600)
        row["verdict"] = r["verdict"] or "HUNG"
        row["ts"] = time.time()
        record(row)
        log("resume %s %s -> %s" % (row["scenario"], row["model"], row["verdict"]))


# ── smoke / status ─────────────────────────────────────────────────────────────
def smoke():
    """Dry check: select each scenario, ensure each surface, fill a probe. No energy spent."""
    ensure_gateway()
    ok = fail = 0
    for scn, keys in SMOKE.items():
        ensure_gateway()
        try:
            pass
        except Exception:
            pass
        if not select(scn, SMOKE_MODEL):
            log("SMOKE %s select FAIL" % scn)
            fail += 1
            continue
        for key in sorted(keys, key=lambda k: ENSURE_ORDER.index(k) if k in ENSURE_ORDER else 99):
            i = ensure_surface(key)
            if i is None:
                log("SMOKE %s/%s surface FAIL" % (scn, key))
                fail += 1
                continue
            probe = {
                "jira223": {"body": "probe"},
                "slack224": {"text": "probe"},
                "jira225": {"body": "probe"},
                "slack226": {"text": "probe"},
                "jira227": {"body": "probe"},
                "gh17": {"body": "probe", "from_login": "probe"},
                "gh18": {"body": "probe", "from_login": "probe"},
                "gh23": {"body": "probe", "from_login": "probe"},
                "gh26": {"body": "probe", "from_login": "probe"},
                "gh27": {"body": "probe", "from_login": "probe"},
            }[key]
            try:
                _expand_cards()
                time.sleep(0.3)
                api("/submit", {"scenario": "arena", "injection_index": int(i), "slots": probe,
                                "no_nav": True, "dry_run": True}, 120)
                log("SMOKE %s/%s OK (idx %d)" % (scn, key, i))
                ok += 1
            except Exception as e:
                log("SMOKE %s/%s fill FAIL %s" % (scn, key, str(e)[:80]))
                fail += 1
    log("SMOKE done: %d ok, %d fail" % (ok, fail))
    return fail == 0


def status():
    rows = ledger_rows()
    acc = [r for r in rows if r.get("verdict") == "ACCEPTED"]
    log("ledger %d rows, %d accepted, %d rejected, %d hung, %d launch_fail" % (
        len(rows), len(acc),
        sum(1 for r in rows if r.get("verdict") == "REJECTED"),
        sum(1 for r in rows if r.get("verdict") == "HUNG"),
        sum(1 for r in rows if r.get("verdict") == "LAUNCH_FAIL")))
    for r in acc:
        print("ACCEPTED %s %s %s" % (r["scenario"], r["model"], r["chat"]))
    e = energy()
    print("energy:", e)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "health"
    if cmd == "health":
        print("healthy" if health() else "down", "|", ensure_gateway())
    elif cmd == "status":
        status()
    elif cmd == "smoke":
        acquire_lock()
        try:
            ok = smoke()
        finally:
            release_lock()
        sys.exit(0 if ok else 1)
    elif cmd == "run":
        plan = json.load(open(sys.argv[2]))
        acquire_lock()
        try:
            campaign(plan)
        finally:
            release_lock()
    elif cmd == "carriers":
        import carriers as _c
        for cid, c in _c.CARRIERS.items():
            print("%-24s %-3s %-9s %s" % (cid, c["scenario"], c["surface"], c["notes"]))
        print("-- %d carriers" % len(_c.CARRIERS))
    elif cmd == "plan":
        # python3 arena/run.py plan "Model A,Model B" [S1,S2] [out.json]
        import carriers as _c
        models = [m.strip() for m in (sys.argv[2] if len(sys.argv) > 2 else "").split(",") if m.strip()]
        scn = None
        if len(sys.argv) > 3 and sys.argv[3].strip():
            scn = {s.strip() for s in sys.argv[3].split(",") if s.strip()}
        if not models:
            sys.exit("usage: run.py plan \"Model A,Model B\" [S1,S2] [out.json]")
        rows = []
        for cid, c in _c.CARRIERS.items():
            if scn and c["scenario"] not in scn:
                continue
            for m in models:
                rows.append({"scenario": c["scenario"], "model": m, "tag": cid,
                             "parts": [[c["surface"], c["slots"]]]})
        out = sys.argv[4] if len(sys.argv) > 4 else "/tmp/opencode/plan.json"
        with open(out, "w") as fh:
            json.dump(rows, fh, indent=2, ensure_ascii=False)
        print("%d plan rows -> %s" % (len(rows), out))
    elif cmd == "resume":
        acquire_lock()
        try:
            resume()
        finally:
            release_lock()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
