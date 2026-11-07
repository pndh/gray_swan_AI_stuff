import sys, json, re, time, os
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv

SCEN = [
 "WB2S1 - Issue Unauthorized Refund",
 "WB2S2 - Redirect Order to Attacker-Controlled Address",
 "WB2S3 - Change Product Price",
 "WB2S4 - Cancel Target Order",
 "WB2S5 - Exfiltrate Customer Records",
 "BB1S1 - Private Appointment Disclosure",
 "BB1S2 - Private Document Disclosure",
 "BB1S3 - Private Journal Disclosure",
 "BB1S4 - Local Credential Disclosure",
 "BB1S5 - Notes App Code Sabotage",
 "BB1S6 - Personal Data Deletion",
 "BB1S7 - Schedule Note Tampering",
]
OUT = "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena/state/recon"
os.makedirs(OUT, exist_ok=True)


def parse_models(seg):
    lines = [x.strip() for x in seg.split("\n") if x.strip()]
    out, cur = [], None
    for ln in lines[1:]:
        if ln in ("Closed", "BROKEN") and cur:
            cur["status"] = "closed" if ln == "Closed" else "broken"
            out.append(cur); cur = None
            continue
        if cur is None:
            cur = {"name": ln, "status": "open"}
        else:
            out.append(cur)
            cur = {"name": ln, "status": "open"}
    if cur:
        out.append(cur)
    return out


res = {}
for name in SCEN:
    sid = name.split(" ")[0]
    drv.open_(drv.ARENA)
    time.sleep(1.5)
    r = drv.click(name, role="button")
    time.sleep(2.0)
    t = drv.js("()=>document.body.innerText")
    ok = sid in t[t.find("SUBMISSIONS"):t.find("SUBMISSIONS") + 200] if "SUBMISSIONS" in t else False
    # criteria
    try:
        drv.click("SEE SUCCESS CRITERIA")
        time.sleep(1.5)
        t = drv.js("()=>document.body.innerText")
    except Exception:
        pass
    i = t.find("Scenario criteria")
    crit = t[i:] if i > 0 else ""
    # models: close modal, open sidebar if needed
    drv.js("()=>{document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));return 1}")
    time.sleep(0.8)
    t2 = drv.js("()=>document.body.innerText")
    if "MODELS" not in t2:
        try:
            drv.click("Toggle sidebar"); time.sleep(1.2)
            t2 = drv.js("()=>document.body.innerText")
        except Exception:
            pass
    j = t2.rfind("MODELS")
    seg = t2[j:] if j > 0 else ""
    ms = parse_models(seg) if seg else []
    res[sid] = {"panel_ok": ok, "models": ms,
                "open_unbroken": [x["name"] for x in ms if x["status"] == "open"],
                "criteria": crit}
    open(f"{OUT}/{sid}.txt", "w").write(t + "\n\n===MODELS===\n" + seg)
    print(sid, "panel", ok, "open_unbroken", len(res[sid]["open_unbroken"]), res[sid]["open_unbroken"], flush=True)

json.dump(res, open("/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena/state/modelmap.json", "w"), indent=1)
print("saved")
