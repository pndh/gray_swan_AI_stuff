#!/usr/bin/env python3
"""Thin client for the local arena gateway. No model, no decisions, just HTTP.

  python3 arena/client.py health
  python3 arena/client.py dump --url https://www.grayswan.ai/arena/...
  python3 arena/client.py submit --scenario mock --slot body="hello BREAK" --wait
  python3 arena/client.py submit -f arena/specs/example_mock.json --wait
  python3 arena/client.py log --since 0
  python3 arena/client.py import-export /path/to/arena-export.zip
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("ARENA_GW", "http://127.0.0.1:8787").rstrip("/")
TOKEN = os.environ.get("ARENA_GW_TOKEN", "").strip()


def call(method: str, path: str, body: dict | None = None) -> dict:
    headers = {"content-type": "application/json"}
    if TOKEN:
        headers["x-arena-token"] = TOKEN
    req = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        print(f"HTTP {exc.code}: {detail}", file=sys.stderr)
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print(f"gateway unreachable at {BASE}: {exc.reason}", file=sys.stderr)
        print("start it with: ./arena/run.sh", file=sys.stderr)
        raise SystemExit(1)


def parse_slots(pairs: list[str]) -> dict:
    out = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"bad --slot value (want name=text): {pair}")
        name, text = pair.split("=", 1)
        out[name.strip()] = text
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health")

    p_dump = sub.add_parser("dump")
    p_dump.add_argument("--url")

    p_sub = sub.add_parser("submit")
    p_sub.add_argument("-f", "--file", help="spec json")
    p_sub.add_argument("--scenario", default="arena")
    p_sub.add_argument("--url")
    p_sub.add_argument("--model")
    p_sub.add_argument("--slot", action="append", default=[], metavar="name=text")
    p_sub.add_argument("--dry-run", action="store_true")
    p_sub.add_argument("--wait", action="store_true", help="block until judge returns")
    p_sub.add_argument("--timeout", type=float, default=90)
    p_sub.add_argument("--tags", default="")
    p_sub.add_argument("--scenario-card", default=None,
                       help='e.g. "WB2S2" — click that scenario before filling')
    p_sub.add_argument("--injection-index", type=int, default=None)

    p_v = sub.add_parser("verdict")
    p_v.add_argument("submission_id")

    p_log = sub.add_parser("log")
    p_log.add_argument("--since", type=int, default=0)
    p_log.add_argument("--limit", type=int, default=200)

    p_imp = sub.add_parser("import-export")
    p_imp.add_argument("path")

    p_ck = sub.add_parser("cookies")
    p_ck.add_argument("-f", "--file", required=True, help="Cookie-Editor JSON export")

    p_open = sub.add_parser("open")
    p_open.add_argument("--url", required=True)

    p_click = sub.add_parser("click")
    p_click.add_argument("--role", default="button")
    p_click.add_argument("--name")
    p_click.add_argument("--selector")
    p_click.add_argument("--index", type=int, default=0)

    p_eval = sub.add_parser("eval")
    p_eval.add_argument("--js", required=True)

    p_state = sub.add_parser("state")
    p_state.add_argument("--models", action="store_true")
    args = ap.parse_args()

    if args.cmd == "health":
        print(json.dumps(call("GET", "/health"), indent=2))
    elif args.cmd == "dump":
        q = f"?url={urllib.request.quote(args.url)}" if args.url else ""
        out = call("GET", "/dump" + q)
        slim = {k: out[k] for k in ("url", "title", "screenshot")}
        slim["elements"] = len(out["elements"])
        print(json.dumps(slim, indent=2))
        print(f"full dump (aria + elements + text): {os.path.abspath('arena/state/dump.json')}")
    elif args.cmd == "submit":
        spec = json.load(open(args.file)) if args.file else {}
        spec.setdefault("scenario", args.scenario)
        if args.url:
            spec["url"] = args.url
        if args.model:
            spec["model"] = args.model
        if args.slot:
            spec["slots"] = {**spec.get("slots", {}), **parse_slots(args.slot)}
        spec["dry_run"] = bool(args.dry_run or spec.get("dry_run"))
        spec["timeout_s"] = args.timeout
        if args.wait:
            spec["wait_verdict"] = True
        if args.tags:
            spec["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
        if args.scenario_card:
            spec["scenario_card"] = args.scenario_card
        if args.injection_index is not None:
            spec["injection_index"] = args.injection_index
        print(json.dumps(call("POST", "/submit", spec), indent=2))
    elif args.cmd == "verdict":
        print(json.dumps(call("GET", f"/verdict/{args.submission_id}"), indent=2))
    elif args.cmd == "log":
        out = call("GET", f"/log?since={args.since}&limit={args.limit}")
        for ev in out["events"]:
            print(f'{ev["id"]:>4} {ev["kind"]:<14} {json.dumps(ev["data"], ensure_ascii=False)[:160]}')
        print(f'-- next cursor: {out["next"]}')
    elif args.cmd == "import-export":
        out = call("POST", f"/import-export?path={urllib.request.quote(args.path)}")
        print(json.dumps(out, indent=2)[:4000])
    elif args.cmd == "cookies":
        raw = json.load(open(args.file))
        cookies = raw.get("cookies", raw) if isinstance(raw, dict) else raw
        print(json.dumps(call("POST", "/cookies", {"cookies": cookies}), indent=2))
    elif args.cmd == "open":
        print(json.dumps(call("POST", "/open", {"url": args.url}), indent=2))
    elif args.cmd == "click":
        body = {"role": args.role, "name": args.name,
                "selector": args.selector, "index": args.index}
        print(json.dumps(call("POST", "/click", body), indent=2))
    elif args.cmd == "eval":
        print(json.dumps(call("POST", "/eval", {"js": args.js}), indent=2))
    elif args.cmd == "state":
        q = "?models=true" if getattr(args, "models", False) else ""
        out = call("GET", "/state" + q)
        print(json.dumps({k: v for k, v in out.items() if k != "models"}, indent=2)[:2500])
        print("models:", len(out.get("models", [])),
              "| open:", out.get("open_models"))

if __name__ == "__main__":
    main()
