import sys, json, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv, drv_ui, batch, camp, p_wb2s3b as P

MODELS = sys.argv[1:] or [
    "Blue Eagle Mighty", "Blue Frog Bold", "Copper Elk Jumbo", "Diamond Falcon Mighty",
    "Glass Salmon Jumbo", "Gold Turtle Stellar", "Gray Lion Colossal", "Gray Penguin Galactic",
    "Obsidian Shrimp Hyper", "Paper Rabbit Huge", "Pink Lizard Enormous",
    "Quartz Kangaroo Plus Ultra", "Sand Whale Huge", "Steel Trout Enormous",
    "Tin Elk Plus Ultra", "Tungsten Whale Power", "Turquoise Capybara Brave",
    "Turquoise Spider Exalted",
]

rows = []
for m in MODELS:
    try:
        drv.open_(drv.ARENA); time.sleep(2.0)
        drv.click("WB2S3 - Change Product Price", role="button"); time.sleep(2.0)
        idx = drv_ui.drive_index()
        if idx is None:
            batch.expand_all(); idx = drv_ui.drive_index()
        if idx is None:
            print(m, "NO_PANEL", flush=True); rows.append({"model": m, "chat": None}); continue
        drv.fill({"scenario": "arena", "dry_run": True, "no_nav": True,
                  "injection_index": idx, "slots": P.S3B})
        ok, cur = drv_ui.select_model(m)
        batch.close_settings()
        c, msg = batch.launch_checked()
        print(m, c, msg, flush=True)
        rows.append({"scenario": "WB2S3", "model": m, "chat": c, "mech": "signed-intake"})
        camp.log(rows[-1])
    except Exception as e:
        print(m, "ERR", str(e)[:200], flush=True)
        rows.append({"model": m, "chat": None, "err": str(e)[:200]})
json.dump(rows, open("/tmp/opencode/s3_sweep.json", "w"))
