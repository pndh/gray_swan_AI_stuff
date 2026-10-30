import sys, json, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv, sched


def idx_by(suffix):
    return drv.js("""()=>{const e=document.querySelector('[id$="%s"]');return e?parseInt(e.id.match(/world-injection-(\\d+)-/)[1]):null}""" % suffix)


def prep_gmail():
    return idx_by("-field-subject")


def prep_shopify():
    return idx_by("-field-first_name")


def prep_gitlab(action_label):
    t = drv.js("()=>document.body.innerText")
    if action_label not in t:
        drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim().startsWith('New injection'));if(b)b.click();return 1}""")
        time.sleep(1.0)
        drv.click("Select injection site"); time.sleep(0.9)
        drv.click("GitLab", role="option"); time.sleep(0.9)
        drv.click("Select action"); time.sleep(0.9)
        drv.click(action_label, role="option"); time.sleep(0.9)
    return idx_by("-field-from_username")


PREP = {"gmail": prep_gmail, "shopify": prep_shopify}


def run(items, inflight_max=6, rounds=80):
    queue = list(items)
    inflight = []
    results = []
    while (queue or inflight) and rounds > 0:
        rounds -= 1
        while queue and len(inflight) < inflight_max:
            it = queue.pop(0)
            if not sched.jsel(it["sc"], it["model"]):
                results.append({**it, "chat": None, "err": "select"}); continue
            if it["prep"] == "gitlab":
                idx = prep_gitlab(it["action"])
            else:
                idx = PREP[it["prep"]]()
            if idx is None:
                results.append({**it, "chat": None, "err": "no_panel"}); continue
            c = sched.launch({"injection_index": int(idx), "slots": it["slots"]})
            print("launch", it["sc"][:12], it["model"], c, flush=True)
            if c:
                inflight.append({**it, "chat": c})
            else:
                results.append({**it, "chat": None, "err": "launch"})
        time.sleep(18)
        for it in list(inflight):
            r = sched.poll(it["chat"])
            if r is None:
                continue
            accepted, pct = r
            row = {"scenario": it["sc"], "model": it["model"], "chat": it["chat"],
                   "mech": it["mech"], "accepted": accepted, "pct": pct}
            results.append(row); inflight.remove(it)
            print("done", it["sc"][:12], it["model"], accepted, pct, flush=True)
            open("/tmp/opencode/mixed.jsonl", "a").write(json.dumps(row) + "\n")
        print("inflight", len(inflight), "queue", len(queue), flush=True)
    return results
