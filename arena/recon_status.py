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


def parse(seg):
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
    return [x for x in out if x["name"] != "BATCH"]


res = {}
for name in SCEN:
    sid = name.split(" ")[0]
    drv.open_(drv.ARENA); time.sleep(2.0)
    drv.click(name, role="button"); time.sleep(2.0)
    t = drv.js("()=>document.body.innerText")
    if "MODELS" not in t:
        drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');if(b)b.click();return 1}""")
        time.sleep(1.2)
        t = drv.js("()=>document.body.innerText")
    i = t.rfind("MODELS")
    ms = parse(t[i:]) if i > 0 else []
    res[sid] = ms
    print(sid, len([m for m in ms if m["status"] == "open"]), "open", flush=True)
    drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');if(b&&document.body.innerText.includes('MODELS'))b.click();return 1}""")
    time.sleep(0.5)

json.dump(res, open("/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena/state/modelstatus.json", "w"), indent=1)

from collections import Counter
br = Counter(); op = Counter()
for sid, ms in res.items():
    for m in ms:
        if m["status"] == "broken":
            br[m["name"]] += 1
        elif m["status"] == "open":
            op[m["name"]] += 1
print("\nMOST BROKEN (compliant) models:")
for n, c in br.most_common(12):
    print(f"  {n}: {c} breaks, {op[n]} open")
