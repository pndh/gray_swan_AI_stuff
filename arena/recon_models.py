import sys, json, re, time
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


def parse_models(t):
    i = t.rfind("MODELS")
    if i < 0:
        return None, []
    seg = t[i:]
    seg = seg.split("Toggle sidebar")[0]
    lines = [x.strip() for x in seg.split("\n") if x.strip()]
    out, cur = [], None
    for ln in lines[1:]:
        if ln in ("BATCH", "Closed", "BROKEN"):
            if ln == "Closed" and cur:
                cur["status"] = "closed"; out.append(cur); cur = None
            elif ln == "BROKEN" and cur:
                cur["status"] = "broken"; out.append(cur); cur = None
            continue
        if cur is None:
            cur = {"name": ln, "status": "open"}
        else:
            if cur["status"] == "open":
                out.append(cur)
                cur = {"name": ln, "status": "open"}
    if cur:
        out.append(cur)
    return seg, out


res = {}
for name in SCEN:
    sid = name.split(" ")[0]
    drv.open_(drv.ARENA)
    time.sleep(1.5)
    r = drv.click(name, role="button")
    time.sleep(1.5)
    t = drv.js("()=>document.body.innerText")
    seg, ms = parse_models(t)
    # injection surface description
    inj = ""
    m = re.search(r"SEE SUCCESS CRITERIA\n(.*?)\nTo launch:", t, re.S)
    if m:
        inj = m.group(1)[:1600]
    res[sid] = {"models": ms,
                "open_unbroken": [x["name"] for x in ms if x["status"] == "open"],
                "inj": inj}
    print(sid, "open_unbroken=", len(res[sid]["open_unbroken"]), res[sid]["open_unbroken"], flush=True)

json.dump(res, open("/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena/state/modelmap.json", "w"), indent=1)
print("saved")
