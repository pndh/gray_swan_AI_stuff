import sys, json, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv, drv_ui, batch, camp, p_wb2s3


def prep_s3(model):
    drv.open_(drv.ARENA)
    time.sleep(2.2)
    drv.click("WB2S3 - Change Product Price", role="button")
    time.sleep(2.2)
    idx = drv_ui.drive_index()
    if idx is None:
        batch.expand_all()
        idx = drv_ui.drive_index()
    if idx is None:
        return None, "no-drive-panel"
    r = drv.fill({"scenario": "arena", "dry_run": True, "no_nav": True,
                  "injection_index": idx, "slots": p_wb2s3.S3})
    ok, cur = drv_ui.select_model(model)
    batch.close_settings()
    c, msg = batch.launch_checked()
    camp.log({"scenario": "WB2S3", "model": model, "chat": c, "msg": msg,
              "mech": "intake-procedure", "idx": idx})
    return c, msg


if __name__ == "__main__":
    models = sys.argv[1:] or ["Blue Eagle Mighty", "Copper Elk Jumbo", "Gold Turtle Stellar"]
    rows = []
    for m in models:
        c, msg = prep_s3(m)
        print(m, c, msg, flush=True)
        rows.append({"scenario": "WB2S3", "model": m, "chat": c})
    json.dump(rows, open("/tmp/opencode/wb2s3_batch.json", "w"))
