"""Arena driver. Talks JSON to the local gateway. No shell parsing."""
import json, re, time, urllib.request, hashlib, os

GW = "http://127.0.0.1:8787"
ARENA = "https://app.grayswan.ai/arena/challenge/ipi-black-2026"


def api(p, b=None, t=180):
    r = urllib.request.Request(GW + p, method="POST" if b is not None else "GET",
                               data=json.dumps(b).encode() if b is not None else None,
                               headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=t))


def js(c):
    return api("/eval", {"js": c})["result"]


def open_(u):
    return api("/open", {"url": u})


def click(name, role="button", force=True):
    return api("/click", {"role": role, "name": name, "force": force})


def state():
    return api("/state")


def models():
    return api("/state?models=true").get("open_models", [])


def fill(spec):
    return api("/submit", spec)


def launch():
    click("LAUNCH")
    time.sleep(2)
    m = re.search(r"chatId=([0-9a-f]+)", js("()=>location.href"))
    return m.group(1) if m else None


def text(c, wait=4):
    open_(f"{ARENA}?chatId={c}")
    time.sleep(wait)
    return js("()=>document.body.innerText")


def score(c, wait=6):
    t = text(c)
    if "SUBMIT BREAK" not in t:
        return None
    click("SUBMIT BREAK")
    time.sleep(wait)
    t = js("()=>document.body.innerText")
    pct = re.search(r"(\d+)%", t)
    return ("ACCEPTED" if "BREAK ACCEPTED" in t else "REJECTED"), int(pct.group(1)) if pct else None


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def ledger(row, path="/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena/state/ledger2.jsonl"):
    with open(path, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
