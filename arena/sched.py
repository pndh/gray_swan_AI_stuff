"""Non-blocking multi-run scheduler: 4-6 chats in flight, 20s poll."""
import sys, json, re, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv

ARENA = drv.ARENA
LED = "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena/state/ledger2.jsonl"


def jsel(sc, m):
    """Select scenario card + model. Returns True on success."""
    drv.open_(ARENA)
    time.sleep(2.2)
    try:
        drv.click(sc, role="button")
    except Exception:
        return False
    time.sleep(1.5)
    # open settings panel
    drv.js("""()=>{const b=document.querySelector('[data-testid=challengeConfigPanelButton]')||[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');if(b)b.click();return 1}""")
    time.sleep(1.0)
    ok = drv.js("""()=>{const o=[...document.querySelectorAll('[role=option]')].find(x=>(x.innerText||'').trim().startsWith(%s));if(!o)return 0;o.click();return 1}""" % json.dumps(m))
    time.sleep(0.4)
    drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');if(b&&document.body.innerText.includes('MODELS'))b.click();return 1}""")
    time.sleep(0.4)
    return bool(ok)


def launch(spec):
    """Fire and return chat id immediately."""
    drv.fill(dict(spec, scenario="arena", no_nav=True, dry_run=False, timeout_s=1))
    time.sleep(1.2)
    m = re.search(r"chatId=([0-9a-f]+)", drv.js("()=>location.href"))
    return m.group(1) if m else None


def poll(chat):
    """Return (accepted, pct) when graded/submitted, else None."""
    drv.open_(f"{ARENA}?chatId={chat}")
    time.sleep(2.2)
    t = drv.js("()=>document.body.innerText")
    if "SUBMIT BREAK" not in t:
        if "failed before the agent" in t:
            return (False, -1)
        return None
    try:
        drv.click("SUBMIT BREAK")
    except Exception:
        return None
    time.sleep(4)
    g = drv.js("""()=>{const s=document.documentElement.innerHTML;const i=s.indexOf('submissionMarks');if(i<0)return 'nf';const seg=s.slice(i,i+1500);const m=seg.match(/gradeStatus:"(\\w+)"/);return m?m[1]:'none'}""")
    if g == "success":
        return (True, 100)
    if g == "fail":
        # read the percentage if the verdict panel is up
        t2 = drv.js("()=>document.body.innerText")
        p = re.search(r"(\d+)%", t2)
        return (False, int(p.group(1)) if p else 0)
    return None


def run(queue, inflight_max=6, rounds=40, logfn=None):
    inflight = []
    results = []
    while (queue or inflight) and rounds > 0:
        rounds -= 1
        while queue and len(inflight) < inflight_max:
            sc, m, spec = queue.pop(0)
            if not jsel(sc, m):
                results.append({"scenario": sc, "model": m, "chat": None, "err": "select"})
                continue
            c = launch(spec)
            print("launch", sc, m, c, flush=True)
            if c:
                inflight.append({"scenario": sc, "model": m, "chat": c})
            else:
                results.append({"scenario": sc, "model": m, "chat": None, "err": "launch"})
        time.sleep(18)
        for it in list(inflight):
            r = poll(it["chat"])
            if r is None:
                continue
            accepted, pct = r
            row = {**it, "accepted": accepted, "pct": pct}
            results.append(row)
            inflight.remove(it)
            print("done", it["scenario"], it["model"], accepted, pct, flush=True)
            if logfn:
                logfn(row)
            else:
                with open(LED, "a") as f:
                    f.write(json.dumps(row) + "\n")
        print("inflight", len(inflight), "queue", len(queue), flush=True)
    return results
