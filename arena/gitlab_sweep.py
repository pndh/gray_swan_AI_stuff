"""GitLab surface runner: add injection, fill, launch; 6 in flight."""
import sys, json, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv, sched


def prep_gitlab(action_label):
    t = drv.js("()=>document.body.innerText")
    if action_label not in t:
        drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim().startsWith('New injection'));if(b)b.click();return 1}""")
        time.sleep(1.0)
        drv.click("Select injection site"); time.sleep(0.9)
        drv.click("GitLab", role="option"); time.sleep(0.9)
        drv.click("Select action"); time.sleep(0.9)
        drv.click(action_label, role="option"); time.sleep(0.9)
    return drv.js("""()=>{const e=document.querySelector('[id$="-field-from_username"]');return e?parseInt(e.id.match(/world-injection-(\\d+)-/)[1]):null}""")


def sweep(scenario, action_label, slots, models, inflight_max=6, rounds=60):
    queue = list(models)
    inflight = []
    results = []
    while (queue or inflight) and rounds > 0:
        rounds -= 1
        while queue and len(inflight) < inflight_max:
            m = queue.pop(0)
            if not sched.jsel(scenario, m):
                results.append({"scenario": scenario, "model": m, "chat": None, "err": "select"})
                continue
            idx = prep_gitlab(action_label)
            if idx is None:
                results.append({"scenario": scenario, "model": m, "chat": None, "err": "no_panel"})
                continue
            c = sched.launch({"injection_index": int(idx), "slots": slots})
            print("launch", m, c, flush=True)
            if c:
                inflight.append({"scenario": scenario, "model": m, "chat": c})
        time.sleep(18)
        for it in list(inflight):
            r = sched.poll(it["chat"])
            if r is None:
                continue
            accepted, pct = r
            results.append({**it, "accepted": accepted, "pct": pct})
            inflight.remove(it)
            print("done", it["model"], accepted, pct, flush=True)
            open("/tmp/opencode/sweep_gitlab.json", "a").write(json.dumps(results[-1]) + "\n")
        print("inflight", len(inflight), "queue", len(queue), flush=True)
    return results
