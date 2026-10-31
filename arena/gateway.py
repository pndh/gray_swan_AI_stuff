#!/usr/bin/env python3
"""Local browser gateway.

One long-lived Firefox profile behind a local HTTP API. You POST a spec, it types
the slots, clicks submit, and returns the verdict plus a full JSON event log.

It never decides what to send and never calls a model. Transport only.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
LOGS = STATE / "logs"
SHOTS = STATE / "shots"
PROFILE = Path(os.environ.get("ARENA_PROFILE", STATE / "profile")).expanduser().resolve()
for _d in (STATE, LOGS, SHOTS, PROFILE):
    _d.mkdir(parents=True, exist_ok=True)
    try:
        _d.chmod(0o700)
    except OSError:
        pass

MAP_PATH = ROOT / "map.json"
LEGER = STATE / "ledger.jsonl"
TOKEN = os.environ.get("ARENA_GW_TOKEN", "").strip()
HEADLESS_MODE = os.environ.get("ARENA_HEADLESS", "auto").strip().lower()
PORT = int(os.environ.get("ARENA_PORT", "8787"))

INTEREST_KEYS = {"judge", "submissionId", "isBreak", "chatId"}


def load_map() -> dict:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def extract_verdict(data: Any, depth: int = 0) -> dict | None:
    """Find a submission/judge record anywhere in a JSON response."""
    if depth > 6:
        return None
    if isinstance(data, dict):
        if INTEREST_KEYS & set(data):
            return {k: data[k] for k in
                    ("submissionId", "chatId", "status", "judge", "model",
                     "title", "submittedAt", "scenario") if k in data}
        for value in data.values():
            rec = extract_verdict(value, depth + 1)
            if rec:
                return rec
    elif isinstance(data, list):
        for value in data[:20]:
            rec = extract_verdict(value, depth + 1)
            if rec:
                return rec
    return None


class SelectorMiss(RuntimeError):
    def __init__(self, slot: str, tried: list[str]):
        super().__init__(f"selector miss for '{slot}' (tried: {', '.join(tried) or 'nothing'})")
        self.slot = slot
        self.tried = tried


class Browser:
    def __init__(self) -> None:
        self.pw = None
        self.ctx = None
        self.page = None
        self.lock = asyncio.Lock()
        self.events: list[dict] = []
        self.captures: dict[str, dict] = {}
        self.started_at = time.time()
        self._seq = 0
        self._wired: set[int] = set()
        self._logfile = LOGS / f"{time.strftime('%Y%m%d')}.jsonl"

    # ---------- logging ----------
    def log(self, kind: str, data: Any) -> None:
        self._seq += 1
        ev = {"id": self._seq, "ts": round(time.time(), 3), "kind": kind, "data": data}
        self.events.append(ev)
        if len(self.events) > 5000:
            self.events = self.events[-2500:]
        with self._logfile.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # ---------- lifecycle ----------
    async def start(self) -> None:
        headless = HEADLESS_MODE == "1" or (
            HEADLESS_MODE == "auto" and not os.environ.get("DISPLAY")
        )
        self.pw = await async_playwright().start()
        self.ctx = await self.pw.firefox.launch_persistent_context(
            user_data_dir=str(PROFILE),
            headless=headless,
            viewport={"width": 1440, "height": 1000},
            locale="en-US",
            firefox_user_prefs={
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False,
            },
        )
        self.ctx.on("page", self._wire)
        self.page = self.ctx.pages[0] if self.ctx.pages else await self.ctx.new_page()
        self._wire(self.page)
        self.log("boot", {"headless": headless, "profile": str(PROFILE), "map": str(MAP_PATH)})

    async def stop(self) -> None:
        try:
            if self.ctx:
                await self.ctx.close()
            if self.pw:
                await self.pw.stop()
        except Exception:
            pass
        self.log("shutdown", {})

    # ---------- event wiring ----------
    def _wire(self, page) -> None:
        if id(page) in self._wired:
            return
        self._wired.add(id(page))
        page.on("console", lambda m: self.log("console", {"level": m.type, "text": m.text[:2000]}))
        page.on("pageerror", lambda e: self.log("pageerror", {"error": str(e)[:2000]}))
        page.on("requestfailed", lambda r: self.log(
            "requestfailed", {"url": r.url, "error": (r.failure or "")[:300]}))
        page.on("framenavigated", lambda f: (
            self.log("nav", {"url": f.url}) if f == page.main_frame else None))
        page.on("response", lambda r: asyncio.create_task(self._on_response(r)))
        page.on("dialog", lambda d: asyncio.create_task(d.dismiss()))

    async def _on_response(self, resp) -> None:
        ctype = (resp.headers or {}).get("content-type", "")
        if "json" not in ctype:
            return
        try:
            data = await resp.json()
        except Exception:
            return
        rec = extract_verdict(data)
        if not rec:
            return
        sid = rec.get("submissionId")
        self.log("response", {"url": resp.url, "status": resp.status,
                              "submissionId": sid, "judge": rec.get("judge")})
        if sid:
            self.captures[sid] = {**self.captures.get(sid, {}), **rec,
                                  "_source": resp.url}

    async def _wait_new_capture(self, before: dict, timeout: float) -> str | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            for sid in self.captures:
                if sid not in before:
                    self.log("capture.new", {"submissionId": sid})
                    return sid
            await asyncio.sleep(0.25)
        self.log("capture.timeout", {"timeout": timeout})
        return None

    async def _wait_judge(self, sid: str, timeout: float) -> dict | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            judge = (self.captures.get(sid) or {}).get("judge")
            if judge is not None:
                return judge
            await asyncio.sleep(0.5)
        return None

    # ---------- element location ----------
    async def _locate(self, cfg: dict):
        page = self.page
        tried: list[str] = []
        if cfg.get("selector"):
            tried.append(cfg["selector"])
            loc = page.locator(cfg["selector"]).first
            if await loc.count():
                return loc
        label = cfg.get("label")
        if label:
            tried.append(f"label:{label}")
            makers = (
                lambda: page.get_by_label(label, exact=False),
                lambda: page.get_by_placeholder(label, exact=False),
                lambda: page.get_by_role("textbox", name=label),
            )
            for make in makers:
                try:
                    loc = make().first
                    if await loc.count():
                        return loc
                except Exception:
                    continue
        role, name = cfg.get("role"), cfg.get("name")
        if role and name:
            tried.append(f"role:{role}[name:{name}]")
            try:
                loc = page.get_by_role(role, name=name, exact=False).first
                if await loc.count():
                    return loc
            except Exception:
                pass
        if name and not role:
            tried.append(f"text:{name}")
            try:
                loc = page.get_by_text(name, exact=False).first
                if await loc.count():
                    return loc
            except Exception:
                pass
        raise SelectorMiss(cfg.get("slot") or cfg.get("name") or "?", tried)

    # ---------- actions ----------
    async def dump(self, url: str | None = None) -> dict:
        async with self.lock:
            if url:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(600)
            aria = await self.page.aria_snapshot()
            text = await self.page.inner_text("body")
            elements = await self.page.evaluate(JS_ELEMENTS)
            shot = SHOTS / f"{time.strftime('%Y%m%d-%H%M%S')}-dump.png"
            await self.page.screenshot(path=str(shot), full_page=True)
            out = {"url": self.page.url, "title": await self.page.title(),
                   "screenshot": str(shot),
                   "elements": elements,
                   "text": text[:6000],
                   "aria": aria[:24000]}
            (STATE / "dump.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                             encoding="utf-8")
            self.log("dump", {"url": self.page.url, "elements": len(elements),
                              "screenshot": str(shot)})
            return out

    async def submit(self, spec: dict) -> dict:
        spec_map = load_map()
        name = spec.get("scenario") or "arena"
        sc = spec_map["scenarios"].get(name)
        if sc is None:
            raise HTTPException(404, f"unknown scenario '{name}' in map.json")
        url = spec.get("url") or sc.get("url")
        if not url or "TODO" in url:
            raise HTTPException(409, "no URL for this scenario; run: "
                                     "python3 arena/client.py dump --url <page>")
        raw_idx = spec.get("injection_index")
        idx = int(raw_idx) if raw_idx is not None else int(sc.get("injection_index") or 0)

        def slot_cfg(slot: str) -> dict:
            raw = dict(sc.get("slots", {}).get(slot) or {})
            sel = raw.get("selector") or f"#world-injection-{idx}-field-{slot}"
            raw["selector"] = sel.replace("{i}", str(idx))
            raw.setdefault("label", slot)
            raw["slot"] = slot
            return raw

        canonical = json.dumps({"scenario": name, "slots": spec.get("slots"),
                                "model": spec.get("model")}, sort_keys=True)
        sha = spec.get("sha256") or hashlib.sha256(canonical.encode()).hexdigest()

        async with self.lock:
            t0 = time.time()
            self.log("submit.start", {"scenario": name, "url": url,
                                      "dry_run": bool(spec.get("dry_run")),
                                      "sha256": sha})
            try:
                if not spec.get("no_nav"):
                    await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as exc:
                self.log("goto.error", {"error": str(exc)[:400]})
            await self.page.wait_for_timeout(int(sc.get("settle_ms", 800)))
            await self.page.bring_to_front()

            card = spec.get("scenario_card") or sc.get("scenario_card")
            if card:
                try:
                    await self.page.get_by_role("button", name=card,
                                                exact=False).first.click()
                    await self.page.wait_for_timeout(900)
                    self.log("scenario.select", {"card": card, "url": self.page.url})
                except Exception as exc:
                    raise HTTPException(409, f"could not select scenario card "
                                             f"'{card}': {exc}") from exc

            try:
                visible = await self.page.evaluate(
                    "(i) => { const el=document.querySelector(`[id^=world-injection-${i}-field]`);"
                    " if(!el) return false; const r=el.getBoundingClientRect();"
                    " return r.width>0 && r.height>0; }", idx)
                if not visible:
                    await self.page.evaluate(
                        "(i) => { [...document.querySelectorAll('button')]"
                        ".filter(b => (b.innerText||'').trim().startsWith('Injection ' + (i+1)))"
                        ".forEach(b => b.click()); }", idx)
                    await self.page.wait_for_timeout(900)
            except Exception:
                pass

            filled: dict[str, int] = {}
            for slot, text in (spec.get("slots") or {}).items():
                cfg = slot_cfg(slot)
                el = await self._locate(cfg)
                try:
                    await el.click(timeout=4000)
                except Exception:
                    pass
                await el.fill("")
                await el.fill(text)
                filled[slot] = len(text)
                self.log("fill", {"slot": slot, "chars": len(text)})

            if spec.get("model"):
                cfg = dict(sc.get("model_select") or {})
                cfg.update({"slot": "model", "label": cfg.get("label") or "model"})
                try:
                    el = await self._locate(cfg)
                    try:
                        await el.select_option(label=spec["model"])
                    except Exception:
                        await el.click()
                        await self.page.get_by_text(spec["model"], exact=False).first.click()
                    self.log("model.select", {"model": spec["model"]})
                except Exception as exc:
                    self.log("model.skip", {"error": str(exc)[:300]})

            shot = SHOTS / f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}-pre.png"
            await self.page.screenshot(path=str(shot), full_page=True)

            if spec.get("dry_run"):
                out = {"ok": True, "dry_run": True, "sha256": sha, "filled": filled,
                       "screenshot": str(shot), "url": self.page.url,
                       "elapsed_s": round(time.time() - t0, 2)}
                self.log("submit.dry_run", out)
                return out

            before = dict(self.captures)
            btn = dict(sc.get("submit_button") or {"role": "button", "name": "Submit"})
            btn.update({"slot": "submit", "name": btn.get("name") or "Submit"})
            el = await self._locate(btn)
            if await el.is_disabled():
                msg = "submit button is disabled (required slot empty, or out of energy)"
                self.log("submit.disabled", {"button": btn.get("name")})
                raise HTTPException(409, msg)
            await el.click()
            self.log("submit.clicked", {"elapsed_s": round(time.time() - t0, 2)})

            sid = await self._wait_new_capture(before, float(spec.get("timeout_s", 90)))
            judge = None
            if sid and spec.get("wait_verdict"):
                judge = await self._wait_judge(sid, float(spec.get("verdict_timeout_s", 180)))

            rec = self.captures.get(sid, {}) if sid else {}
            result = {"ok": bool(sid), "submissionId": sid, "sha256": sha,
                      "judge": judge if judge is not None else rec.get("judge"),
                      "status": rec.get("status"), "model": spec.get("model"),
                      "filled": filled, "screenshot": str(shot),
                      "elapsed_s": round(time.time() - t0, 2), "url": self.page.url}
            with LEGER.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                     "scenario": name, **result,
                                     "tags": spec.get("tags") or []},
                                    ensure_ascii=False) + "\n")
            self.log("submit.done", result)
            return result


BROWSER = Browser()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await BROWSER.start()
    try:
        yield
    finally:
        await BROWSER.stop()


app = FastAPI(title="arena-gateway", lifespan=lifespan)


async def auth(x_arena_token: str | None = Header(default=None)) -> None:
    if TOKEN and x_arena_token != TOKEN:
        raise HTTPException(401, "bad token")


class SubmitSpec(BaseModel):
    scenario: str = "arena"
    url: str | None = None
    slots: dict[str, str] = {}
    model: str | None = None
    dry_run: bool = False
    wait_verdict: bool = False
    timeout_s: float = 90
    verdict_timeout_s: float = 180
    sha256: str | None = None
    tags: list[str] = []
    no_nav: bool = False
    injection_index: int | None = None
    scenario_card: str | None = None


@app.post("/tab")
async def new_tab(url: str | None = None, _: None = Depends(auth)) -> dict:
    """Open a second tab and make it the active page (parallel runs)."""
    async with BROWSER.lock:
        page = await BROWSER.ctx.new_page()
        BROWSER._wire(page)
        BROWSER.page = page
        if url:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        return {"ok": True, "pages": len(BROWSER.ctx.pages), "url": page.url}


@app.get("/health")
async def health(_: None = Depends(auth)) -> dict:
    return {"ok": True, "uptime_s": round(time.time() - BROWSER.started_at, 1),
            "url": BROWSER.page.url if BROWSER.page else None,
            "captures": len(BROWSER.captures), "events": len(BROWSER.events)}


@app.get("/dump")
async def dump(url: str | None = None, _: None = Depends(auth)) -> dict:
    try:
        return await BROWSER.dump(url)
    except SelectorMiss as exc:
        raise HTTPException(422, str(exc))


@app.post("/submit")
async def submit(spec: SubmitSpec, _: None = Depends(auth)) -> dict:
    try:
        return await BROWSER.submit(spec.model_dump())
    except SelectorMiss as exc:
        BROWSER.log("selector.miss", {"slot": exc.slot, "tried": exc.tried})
        raise HTTPException(422, {"error": str(exc), "slot": exc.slot,
                                  "tried": exc.tried,
                                  "next": "GET /dump then patch arena/map.json"})


@app.get("/verdict/{submission_id}")
async def verdict(submission_id: str, _: None = Depends(auth)) -> dict:
    rec = BROWSER.captures.get(submission_id)
    if not rec:
        raise HTTPException(404, "unknown submissionId")
    return rec


@app.get("/log")
async def log(since: int = 0, limit: int = 200, _: None = Depends(auth)) -> dict:
    events = [e for e in BROWSER.events if e["id"] > since][:limit]
    return {"events": events, "next": events[-1]["id"] if events else since}


@app.post("/login")
async def login(url: str | None = None, _: None = Depends(auth)) -> dict:
    target = url or load_map().get("base_url")
    async with BROWSER.lock:
        await BROWSER.page.goto(target, wait_until="domcontentloaded", timeout=60000)
        await BROWSER.page.bring_to_front()
    return {"ok": True, "url": BROWSER.page.url,
            "note": "log in by hand in the Firefox window; the profile persists"}


class OpenReq(BaseModel):
    url: str


class ClickReq(BaseModel):
    role: str | None = "button"
    name: str | None = None
    selector: str | None = None
    exact: bool = False
    index: int = 0
    force: bool = False


class EvalReq(BaseModel):
    js: str
    arg: Any | None = None


STATE_JS = r"""
() => {
  const txt = e => (e ? (e.innerText || e.textContent || '') : '').trim();
  const out = {};
  const heads = [...document.querySelectorAll('h1,h2,h3,p,div,span')]
      .filter(e => txt(e) === 'HARMFUL TASK');
  if (heads.length) {
    let el = heads[0];
    for (let i = 0; i < 14 && el; i++) {
      el = el.previousElementSibling || el.parentElement;
      if (!el) break;
      const m = txt(el).match(/(WB2S\d|BB1S\d)/);
      if (m) { out.scenario = m[1]; break; }
    }
  }
  out.fields = [...document.querySelectorAll('[id^="world-injection"]')]
      .map(e => ({id: e.id, len: (e.value || '').length,
                  value: (e.value || '').slice(0, 60)}));
  const lb = [...document.querySelectorAll('button')].find(b => /LAUNCH/i.test(txt(b)));
  out.launch = lb ? {label: txt(lb).replace(/\s+/g, ' ').slice(0, 40),
                     disabled: !!lb.disabled} : null;
  const em = document.body.innerText.match(/Energy\s+(\d+)\s+of\s+(\d+)/);
  out.energy = em ? {now: +em[1], max: +em[2]} : null;
  const am = document.body.innerText.match(/Attacking:\s*\n?\s*([^\n]{2,40})/);
  out.model = am ? am[1].trim() : null;
  const body = document.body.innerText;
  const bi = body.lastIndexOf('BATCH');
  out.panel_open = bi >= 0;
  out.models_raw = bi >= 0 ? body.slice(bi) : null;
  out.url = location.href;
  return out;
}
"""

STATUSES = {"BROKEN", "Closed", "OPEN", "Pending"}


def parse_models(raw: str | None) -> list[dict]:
    if not raw:
        return []
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    models: list[dict] = []
    for line in lines:
        if line in STATUSES:
            if models:
                models[-1]["status"] = line
            continue
        if line.upper().startswith("MODELS") or "broken for this scenario" in line.lower():
            continue
        if line in {"BATCH", "MODELS"} or line.startswith("WB2S") or line.startswith("BB1S"):
            continue
        models.append({"name": line, "status": "open"})
    return models


@app.get("/state")
async def state(models: bool = False, _: None = Depends(auth)) -> dict:
    async with BROWSER.lock:
        raw = await BROWSER.page.evaluate(STATE_JS)
        if models and not raw.get("panel_open"):
            try:
                await BROWSER.page.get_by_role(
                    "button", name="Open challenge settings panel"
                ).first.click(timeout=8000)
                await BROWSER.page.wait_for_timeout(1000)
                raw = await BROWSER.page.evaluate(STATE_JS)
            except Exception as exc:
                raw["models_error"] = str(exc)[:200]
    raw["models"] = parse_models(raw.pop("models_raw", None))
    raw["open_models"] = [m["name"] for m in raw["models"] if m["status"] == "open"]
    return raw


@app.post("/eval")
async def eval_js(req: EvalReq, _: None = Depends(auth)) -> dict:
    """Run JS in the page. Recon only; nothing here is part of a payload."""
    async with BROWSER.lock:
        try:
            result = await BROWSER.page.evaluate(req.js, req.arg)
        except Exception as exc:
            raise HTTPException(422, f"eval failed: {str(exc)[:400]}") from exc
        BROWSER.log("eval", {"chars": len(req.js)})
        return {"ok": True, "result": result}


@app.post("/click")
async def click(req: ClickReq, _: None = Depends(auth)) -> dict:
    """Click one element; used for recon and scenario/model switching."""
    async with BROWSER.lock:
        if req.selector:
            loc = BROWSER.page.locator(req.selector)
        elif req.name:
            loc = BROWSER.page.get_by_role(req.role or "button",
                                           name=req.name, exact=req.exact)
        else:
            raise HTTPException(400, "need selector or name")
        target = loc.nth(req.index)
        try:
            await target.click(timeout=15000, force=req.force)
        except Exception as exc:
            BROWSER.log("click.error", {"name": req.name, "error": str(exc)[:300]})
            raise HTTPException(422, f"click failed: {str(exc)[:300]}") from exc
        await BROWSER.page.wait_for_timeout(900)
        body = ""
        try:
            body = (await BROWSER.page.inner_text("body"))[:2500]
        except Exception:
            pass
        out = {"ok": True, "url": BROWSER.page.url, "text": body}
        BROWSER.log("click", {"name": req.name or req.selector, "url": out["url"]})
        return out



@app.post("/open")
async def open_url(req: OpenReq, _: None = Depends(auth)) -> dict:
    """Navigate without touching the address bar (long magic links)."""
    async with BROWSER.lock:
        try:
            await BROWSER.page.goto(req.url, wait_until="domcontentloaded", timeout=60000)
        except Exception as exc:
            BROWSER.log("open.error", {"error": str(exc)[:300]})
        await BROWSER.page.wait_for_timeout(1200)
        body = ""
        try:
            body = (await BROWSER.page.inner_text("body"))[:1200]
        except Exception:
            pass
        out = {"ok": True, "url": BROWSER.page.url,
               "title": await BROWSER.page.title(), "text": body}
        BROWSER.log("open", {"url": out["url"]})
        return out


class CookieIn(BaseModel):
    cookies: list[dict]


@app.post("/cookies")
async def cookies(payload: CookieIn, _: None = Depends(auth)) -> dict:
    """Import cookies exported from your daily Firefox (SSO fallback)."""
    norm = []
    for raw in payload.cookies:
        c = dict(raw)
        if "expirationDate" in c and "expires" not in c:
            c["expires"] = c.pop("expirationDate")
        c.setdefault("path", "/")
        norm.append({k: c[k] for k in ("name", "value", "domain", "path",
                                       "expires", "httpOnly", "secure",
                                       "sameSite") if k in c})
    await BROWSER.ctx.add_cookies(norm)
    BROWSER.log("cookies.import", {"count": len(norm)})
    return {"ok": True, "added": len(norm)}


@app.post("/import-export")
async def import_export(path: str, _: None = Depends(auth)) -> dict:
    """Parse an arena export zip and load its verdicts into captures."""
    zp = Path(path).expanduser()
    if not zp.is_file():
        raise HTTPException(404, f"no such file: {zp}")
    rows = []
    with zipfile.ZipFile(zp) as zf:
        for name in zf.namelist():
            if not name.endswith(".json") or name.endswith("manifest.json"):
                continue
            try:
                data = json.loads(zf.read(name))
            except Exception:
                continue
            if not isinstance(data, dict) or "submissionId" not in data:
                continue
            rec = {k: data.get(k) for k in
                   ("submissionId", "status", "judge", "model", "scenario", "submittedAt")}
            BROWSER.captures[rec["submissionId"]] = rec
            judge = rec.get("judge") or {}
            rows.append({"submissionId": rec["submissionId"],
                         "model": rec.get("model"), "status": rec.get("status"),
                         "isBreak": judge.get("isBreak"),
                         "criteria": judge.get("criteria")})
    with LEGER.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "source": "export", **row}, ensure_ascii=False) + "\n")
    BROWSER.log("import_export", {"path": str(zp), "rows": len(rows)})
    return {"ok": True, "count": len(rows), "rows": rows}


# ---------------- mock surface (smoke test, no arena account) ----------------
MOCK_FORM = """<!doctype html><meta charset="utf-8"><title>Arena Mock</title>
<style>body{font:15px system-ui;max-width:760px;margin:40px auto}
label{display:block;margin:14px 0 4px;font-weight:600}
input,textarea{width:100%;padding:8px;box-sizing:border-box}
textarea{height:150px}button{margin-top:16px;padding:8px 18px}
pre{background:#111;color:#0f0;padding:12px;white-space:pre-wrap}</style>
<h1>Arena Mock</h1>
<label for="slot-subject">Subject</label><input id="slot-subject">
<label for="slot-body">Body</label><textarea id="slot-body"></textarea>
<label for="slot-cc">CC</label><input id="slot-cc">
<label for="model">Model</label><select id="model">
<option>Bronze Spider Rare</option><option>Glass Salmon Jumbo</option></select>
<button id="submit" type="button">Submit</button>
<pre id="out">idle</pre>
<script>
document.querySelector('#submit').onclick = async () => {
  const r = await fetch('/mock/submit', {method:'POST',
    headers:{'content-type':'application/json'},
    body: JSON.stringify({
      subject: document.querySelector('#slot-subject').value,
      body: document.querySelector('#slot-body').value,
      cc: document.querySelector('#slot-cc').value,
      model: document.querySelector('#model').value})});
  document.querySelector('#out').textContent = JSON.stringify(await r.json(), null, 2);
};
</script>"""

JS_ELEMENTS = """() => [...document.querySelectorAll(
 'input,textarea,select,button,[role=button],[contenteditable=true]')].slice(0,120)
 .map(e => ({tag: e.tagName.toLowerCase(), type: e.type || null, id: e.id || null,
   name: e.name || null, placeholder: e.placeholder || null,
   aria: e.getAttribute('aria-label'),
   label: (e.labels && e.labels[0] && e.labels[0].innerText.trim()) || null,
   text: (e.innerText || '').trim().slice(0,80),
   selector: e.id ? '#'+e.id : null}))"""


@app.get("/mock/form", response_class=HTMLResponse)
async def mock_form() -> str:
    return MOCK_FORM


@app.post("/mock/submit")
async def mock_submit(payload: dict) -> dict:
    body = str(payload.get("body", ""))
    is_break = "BREAK" in body
    return {"submissionId": "mock_" + uuid.uuid4().hex[:12],
            "chatId": uuid.uuid4().hex,
            "status": "judged",
            "model": payload.get("model") or "Mock Spider",
            "judge": {"isBreak": is_break,
                      "judges": [{"label": "Combined", "isBreak": is_break}],
                      "criteria": [{"name": "Mock Criterion",
                                    "score": 1 if is_break else 0}]}}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
