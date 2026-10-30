import sys, json, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv, drv_ui, batch, camp, p_bb1s6 as P

MODELS = sys.argv[1:] or [
    "Diamond Falcon Mighty", "Gray Penguin Galactic", "Obsidian Shrimp Hyper",
    "Paper Rabbit Huge", "Pink Lizard Enormous", "Quartz Kangaroo Plus Ultra",
    "Sand Whale Huge", "Steel Trout Enormous", "Tin Elk Plus Ultra",
    "Tungsten Whale Power", "Turquoise Capybara Brave", "Turquoise Spider Exalted",
    "Blue Frog Bold",
]

rows = []
for m in MODELS:
    try:
        drv.open_(drv.ARENA); time.sleep(2.0)
        drv.click("BB1S6 - Personal Data Deletion", role="button"); time.sleep(2.0)
        t = drv.js("()=>document.body.innerText")
        if "Comment on a public Chat Export Index issue" not in t:
            drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim().startsWith('New injection'));if(b)b.click();return 1}""")
            time.sleep(1)
            drv.click("Select injection site"); time.sleep(1)
            drv.click("GitLab", role="option"); time.sleep(1)
            drv.click("Select action"); time.sleep(1)
            drv.click("Comment on a public Chat Export Index issue", role="option"); time.sleep(1)
        batch.expand_all()
        idx = drv.js("""()=>{const e=document.querySelector('[id$="-field-from_username"]');return e?parseInt(e.id.match(/world-injection-(\\d+)-/)[1]):null}""")
        if idx is None:
            print(m, "NO_IDX", flush=True); rows.append({"model": m, "chat": None}); continue
        drv.fill({"scenario": "arena", "dry_run": True, "no_nav": True,
                  "injection_index": int(idx), "slots": P.S6})
        drv_ui.select_model(m)
        batch.close_settings()
        c, msg = batch.launch_checked()
        print(m, c, msg, flush=True)
        r = {"scenario": "BB1S6", "model": m, "chat": c, "mech": "cleanup-migration"}
        rows.append(r); camp.log(r)
    except Exception as e:
        print(m, "ERR", str(e)[:150], flush=True)
        rows.append({"model": m, "chat": None})
json.dump(rows, open("/tmp/opencode/bb1s6_sweep.json", "w"))
