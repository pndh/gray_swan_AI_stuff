import sys, json, re, time
sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI/arena")
import drv


def open_settings():
    if "MODELS" in drv.js("()=>document.body.innerText"):
        return
    drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');if(b)b.click();return 1}""")
    time.sleep(1.0)


def current_model():
    try:
        return drv.js("""()=>{const b=[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Open challenge settings panel');return b?b.innerText.trim():''}""")
    except Exception:
        return ""


def model_status():
    t = drv.js("()=>document.body.innerText")
    i = t.rfind("MODELS")
    seg = t[i:] if i > 0 else ""
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


def select_model(name):
    open_settings()
    ok = drv.js("""()=>{const o=[...document.querySelectorAll('div[role=option]')].find(e=>e.innerText.trim().startsWith(%s));if(!o)return 'nf';o.click();return 'ok'}""" % json.dumps(name))
    time.sleep(1.0)
    return ok, current_model()


def drive_index():
    """Return the DOM injection index of the Drive card, or None."""
    return drv.js("""()=>{const e=document.querySelector('[id$="-field-title"]');if(!e)return null;const m=e.id.match(/world-injection-(\\d+)-field-title/);return m?parseInt(m[1]):null}""")


def gmail_index():
    return drv.js("""()=>{const e=document.querySelector('[id$="-field-subject"]');if(!e)return null;const m=e.id.match(/world-injection-(\\d+)-field-subject/);return m?parseInt(m[1]):null}""")
