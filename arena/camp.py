import sys, json, re, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv, drv_ui

LED = "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena/state/ledger2.jsonl"


def goto_scenario(sid, card):
    drv.open_(drv.ARENA)
    time.sleep(2.0)
    drv.click(card, role="button")
    time.sleep(1.8)
    t = drv.js("()=>document.body.innerText")
    return sid in t[t.find("SUBMISSIONS"):t.find("SUBMISSIONS") + 160] if "SUBMISSIONS" in t else False


def add_drive_injection():
    # open a new injection panel
    drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim().startsWith('New injection'));if(b)b.click();return !!b}""")
    time.sleep(1.0)
    # newest site selector
    n = drv.js("""()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.innerText.trim()==='Select injection site');return b.length}""")
    if n == 0:
        return False
    # click the LAST one via playwright by index is not supported; use force click on nth
    drv.js("""()=>{const b=[...document.querySelectorAll('button')].filter(e=>e.innerText.trim()==='Select injection site');b[b.length-1].setAttribute('data-last-site','1');return 1}""")
    drv.click("Select injection site", role="button")
    time.sleep(0.9)
    drv.click("Google Drive", role="option")
    time.sleep(0.8)
    drv.click("Select action", role="button")
    time.sleep(0.9)
    drv.click("Share file with victim", role="option")
    time.sleep(0.9)
    return True


def launch_fast(max_wait=25):
    before = drv.js("()=>location.href")
    try:
        drv.click("LAUNCH", role="button")
    except Exception as e:
        return None, f"click error {e}"
    for _ in range(max_wait):
        time.sleep(1)
        u = drv.js("()=>location.href")
        m = re.search(r"chatId=([0-9a-f]+)", u)
        if m:
            return m.group(1), "ok"
    return None, "no chatId"


def wait_ready(chat, tries=18, gap=8):
    drv.open_(f"{drv.ARENA}?chatId={chat}")
    for _ in range(tries):
        time.sleep(gap)
        t = drv.js("()=>document.body.innerText")
        if "SUBMIT BREAK" in t:
            return t
    return drv.js("()=>document.body.innerText")


def submit_break(chat):
    t = wait_ready(chat)
    if "SUBMIT BREAK" not in t:
        return {"chat": chat, "verdict": "NOT_READY"}
    drv.click("SUBMIT BREAK")
    time.sleep(7)
    t = drv.js("()=>document.body.innerText")
    pct = re.search(r"(\d+)%", t)
    v = "ACCEPTED" if "BREAK ACCEPTED" in t else ("REJECTED" if "BREAK REJECTED" in t else "UNKNOWN")
    return {"chat": chat, "verdict": v, "pct": int(pct.group(1)) if pct else None}


def log(row):
    with open(LED, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def grade(chat):
    """Read stored submission marks from the app state instead of clicking."""
    drv.open_(f"{drv.ARENA}?chatId={chat}")
    time.sleep(2.5)
    raw = drv.js("""()=>{const s=document.documentElement.innerHTML;const i=s.indexOf('submissionMarks');if(i<0)return 'nf';const seg=s.slice(i,i+1200);const m=seg.match(/gradeStatus:"(\\w+)"/);return m?m[1]:'none'}""")
    return raw
