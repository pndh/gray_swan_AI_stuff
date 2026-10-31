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
OUT = "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena/state/recon"
import os
os.makedirs(OUT, exist_ok=True)

for name in SCEN:
    sid = name.split(" ")[0]
    drv.open_(drv.ARENA)
    time.sleep(1.2)
    drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim().startsWith('%s'));if(b)b.click();return !!b}""" % sid)
    time.sleep(3.0)
    t = drv.js("()=>document.body.innerText")
    # open criteria modal
    try:
        drv.click("SEE SUCCESS CRITERIA")
        time.sleep(1.2)
        t2 = drv.js("()=>document.body.innerText")
    except Exception as e:
        t2 = t
    open(f"{OUT}/{sid}.txt", "w").write(t + "\n\n===CRITERIA===\n" + t2)
    # models segment
    i = t2.rfind("MODELS")
    seg = t2[i:] if i > 0 else t2
    print(sid, "textlen", len(t2), "models_seg", len(seg), flush=True)
    # close modal
    drv.js("()=>{document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));return 1}")
    time.sleep(0.5)
print("done")
