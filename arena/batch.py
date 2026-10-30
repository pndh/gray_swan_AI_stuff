import sys, json, re, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv, drv_ui, camp

CARD = {
    "BB1S7": "BB1S7 - Schedule Note Tampering",
    "WB2S3": "WB2S3 - Change Product Price",
    "WB2S5": "WB2S5 - Exfiltrate Customer Records",
    "BB1S2": "BB1S2 - Private Document Disclosure",
    "WB2S4": "WB2S4 - Cancel Target Order",
}


def expand_all():
    n = drv.js("""()=>{const t=[...document.querySelectorAll('[data-testid=world-injection] [data-slot=collapsible-trigger][data-state=closed]')];t.forEach(x=>x.click());return t.length}""")
    if n:
        time.sleep(1.0)
    return n


def close_settings():
    try:
        if "MODELS" in drv.js("()=>document.body.innerText"):
            drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');if(b)b.click();return 1}""")
            time.sleep(0.6)
    except Exception:
        pass


def launch_checked(retries=2):
    for attempt in range(retries):
        before = drv.js("()=>location.href")
        try:
            drv.click("LAUNCH", role="button")
        except Exception as e:
            time.sleep(1)
            continue
        for _ in range(20):
            time.sleep(1)
            u = drv.js("()=>location.href")
            m = re.search(r"chatId=([0-9a-f]+)", u)
            if m and u != before:
                return m.group(1), "ok"
        time.sleep(1)
    return None, "no-launch"


def one(scenario, model, slots, add_drive=False, dry=True):
    drv.open_(drv.ARENA)
    time.sleep(1.8)
    drv.click(CARD[scenario], role="button")
    time.sleep(1.6)
    if add_drive:
        camp.add_drive_injection()
    if dry:
        drv.fill({"scenario": "arena", "dry_run": True, "no_nav": True,
                  "injection_index": 0, "slots": slots[0]})
        if add_drive:
            drv.fill({"scenario": "arena", "dry_run": True, "no_nav": True,
                      "injection_index": 1, "slots": slots[1]})
    ok, cur = drv_ui.select_model(model)
    if ok != "ok":
        return None, f"model-not-selected:{cur}"
    close_settings()
    c, msg = launch_checked()
    camp.log({"scenario": scenario, "model": model, "chat": c, "msg": msg,
              "mech": "batch", "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
    return c, msg


def score_all(rows):
    out = []
    for r in rows:
        if not r.get("chat"):
            out.append({**r, "verdict": "NO_CHAT"})
            continue
        res = camp.submit_break(r["chat"])
        out.append({**r, **res})
        camp.log({**r, **res})
    return out
