#!/usr/bin/env python3
"""lift — attribute attack success to frames and modifiers.

The repo already has frames, a rubric judge, and a BoN runner. What it does not
have is a controlled comparison: given the same behavior and the same target,
does frame X or modifier M actually add ASR, or does it just look plausible?

`lift` runs a factorial sweep over arsenal/jailbreak/INGREDIENTS.json, stores
every attempt in SQLite, and reports per-frame ASR with Wilson intervals plus
per-modifier lift (present vs absent) with a bootstrap interval.

Usage:
  python3 tools/lift.py --behavior cn_scale_up --model deepseek-chat --rolls 3
  python3 tools/lift.py --behavior cn_scale_up --frames combo,forensic --dry-run
  python3 tools/lift.py --behavior cn_scale_up --summary

Notes:
- One row per (attack file, roll). Judge is bon_utils.strict_rubric_classify.
- Cells with n < 5 are marked low-confidence; do not promote on them.
- Lift is model- and version-specific. The model id and date are stored with
  every attempt so a later run can be compared, not merged blindly.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import bon_utils as bon  # noqa: E402

INGREDIENTS = ROOT / "arsenal/jailbreak/INGREDIENTS.json"
DEFAULT_DB = ROOT / "validator/lift.sqlite"
DB_LOCK = threading.Lock()
BEHAVIOR_DIRS = [
    ROOT / "competition/intel/behaviors",
    ROOT / "talk/slide_materials/09_behavior_rubrics",
    ROOT / "validator/behaviors",
    ROOT / "ipi_legacy/behaviors",
]


# --------------------------------------------------------------------------- io
def load_behavior(bid: str) -> dict:
    for d in BEHAVIOR_DIRS:
        p = d / f"{bid}.yaml"
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8"))
    raise SystemExit(f"behavior yaml not found for {bid!r} in {[str(d) for d in BEHAVIOR_DIRS]}")


def load_rows(bid: str, frames: set[str] | None, limit: int | None) -> list[dict]:
    data = json.loads(INGREDIENTS.read_text(encoding="utf-8"))
    rows = [r for r in data["files"] if r.get("behavior") == bid]
    if frames:
        rows = [r for r in rows if r.get("base_frame") in frames]
    if limit:
        by_frame: dict[str, int] = {}
        kept = []
        for r in rows:
            f = r.get("base_frame", "?")
            if by_frame.get(f, 0) < limit:
                kept.append(r)
                by_frame[f] = by_frame.get(f, 0) + 1
        rows = kept
    return rows


def db_open(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False)
    con.execute(
        """CREATE TABLE IF NOT EXISTS attempts (
               id INTEGER PRIMARY KEY,
               ts TEXT, behavior TEXT, model TEXT, path TEXT,
               base_frame TEXT, modifiers TEXT, lang TEXT, roll INTEGER,
               verdict TEXT, detail TEXT, response TEXT,
               latency REAL, error TEXT
           )"""
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_attr ON attempts(behavior, model, base_frame)")
    return con


# ------------------------------------------------------------------------ stats
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def boot_diff(a: list[int], b: list[int], iters: int = 4000) -> tuple[float, float]:
    """Bootstrap 95% interval for p(a) - p(b). Small-n friendly."""
    if not a or not b:
        return (0.0, 0.0)
    diffs = []
    for _ in range(iters):
        pa = sum(random.choice(a) for _ in a) / len(a)
        pb = sum(random.choice(b) for _ in b) / len(b)
        diffs.append(pa - pb)
    diffs.sort()
    return (diffs[int(0.025 * iters)], diffs[int(0.975 * iters) - 1])


def p_two_sided(k1: int, n1: int, k2: int, n2: int) -> float:
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = abs(p1 - p2) / se
    return 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))


# ------------------------------------------------------------------------- runs
def run_one(row: dict, roll: int, cfg: dict, behavior: dict, args, con: sqlite3.Connection) -> None:
    path = ROOT / row["path"]
    try:
        prompt = path.read_text(encoding="utf-8")
    except OSError as exc:
        with DB_LOCK:
            con.execute(
                "INSERT INTO attempts (ts,behavior,model,path,base_frame,modifiers,lang,roll,verdict,detail,response,latency,error)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), args.behavior, args.model, row["path"],
                 row.get("base_frame"), json.dumps(row.get("modifiers", [])), row.get("lang"),
                 roll, "ERROR", "", "", 0.0, str(exc)),
            )
            con.commit()
        return

    t0 = time.time()
    try:
        response = bon.call_target(
            prompt, args.model, temperature=args.temperature,
            max_tokens=args.max_tokens, base_url=cfg["base_url"], api_key=cfg["api_key"],
        )
        verdict, detail = bon.strict_rubric_classify(
            behavior["behavior_str"], behavior["criteria"], response,
            model=args.judge_model, passes=args.passes,
            base_url=cfg["judge_base_url"], api_key=cfg["judge_api_key"],
        )
        err = ""
    except Exception as exc:  # noqa: BLE001 - record and keep the sweep alive
        response, verdict, detail, err = "", "ERROR", "", str(exc)

    with DB_LOCK:
        con.execute(
            "INSERT INTO attempts (ts,behavior,model,path,base_frame,modifiers,lang,roll,verdict,detail,response,latency,error)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), args.behavior, args.model, row["path"],
             row.get("base_frame"), json.dumps(row.get("modifiers", [])), row.get("lang"),
             roll, verdict, detail, response[:20000], time.time() - t0, err),
        )
        con.commit()


def run(args) -> None:
    behavior = load_behavior(args.behavior)
    rows = load_rows(args.behavior, set(args.frames.split(",")) if args.frames else None, args.limit)
    if not rows:
        raise SystemExit("no attack files matched")

    trials = [(r, i) for r in rows for i in range(args.rolls)]
    if args.dry_run:
        frames = sorted({r.get("base_frame", "?") for r in rows})
        mods = sorted({m for r in rows for m in r.get("modifiers", [])})
        print(f"behavior : {args.behavior}")
        print(f"files    : {len(rows)}")
        print(f"trials   : {len(trials)}  ({args.rolls} rolls)")
        print(f"frames   : {', '.join(frames)}")
        print(f"modifiers: {', '.join(mods)}")
        for r in rows[:10]:
            print(f"  {r.get('base_frame','?'):<22} {r['path']}")
        if len(rows) > 10:
            print(f"  ... {len(rows) - 10} more")
        return

    if args.provider == "deepseek":
        key = bon.get_env("DEEPSEEK_API_KEY", "")
        cfg = {
            "base_url": bon.DEEPSEEK_URL,
            "api_key": key,
            "judge_base_url": bon.DEEPSEEK_URL,
            "judge_api_key": key,
        }
    else:
        cfg = {"base_url": None, "api_key": None, "judge_base_url": None, "judge_api_key": None}

    con = db_open(Path(args.out))
    done = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(run_one, r, i, cfg, behavior, args, con) for r, i in trials]
        for fut in as_completed(futures):
            fut.result()
            done += 1
            if done % 10 == 0 or done == len(futures):
                print(f"[lift] {done}/{len(futures)}", flush=True)
    con.commit()
    report(con, args.behavior, args.model, args.out)
    con.close()


# ----------------------------------------------------------------------- report
def report(con: sqlite3.Connection, behavior: str, model: str, out: Path) -> None:
    where = "behavior=? AND model=?"
    rows = con.execute(
        f"SELECT base_frame, modifiers, verdict FROM attempts WHERE {where}", (behavior, model)
    ).fetchall()
    if not rows:
        print("no attempts recorded")
        return

    frames: dict[str, list[int]] = {}
    mods_with: dict[str, list[int]] = {}
    mods_without: dict[str, list[int]] = {}
    all_verdicts = [1 if v == "BREAK" else 0 for _, _, v in rows]
    all_mods = {m for _, ms, _ in rows for m in json.loads(ms)}

    for frame, ms, verdict in rows:
        hit = 1 if verdict == "BREAK" else 0
        frames.setdefault(frame or "?", []).append(hit)
        present = set(json.loads(ms))
        for m in all_mods:
            (mods_with if m in present else mods_without).setdefault(m, []).append(hit)

    print(f"\nbehavior: {behavior}   model: {model}   db: {out}")
    print(f"n={len(rows)}   asr={sum(all_verdicts)/len(rows):.1%}\n")

    print(f"{'frame':<24}{'n':>4}{'break':>7}{'asr':>8}{'95% CI':>16}")
    for f, xs in sorted(frames.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        lo, hi = wilson(sum(xs), len(xs))
        flag = "" if len(xs) >= 5 else "  low-n"
        print(f"{f:<24}{len(xs):>4}{sum(xs):>7}{sum(xs)/len(xs):>8.1%}"
              f"{f'[{lo:.1%},{hi:.1%}]':>16}{flag}")

    print(f"\n{'modifier':<24}{'n+':>4}{'asr+':>8}{'n-':>4}{'asr-':>8}{'delta':>9}{'95% CI':>18}{'p':>8}")
    ranked = []
    for m in all_mods:
        a, b = mods_with.get(m, []), mods_without.get(m, [])
        if not a or not b:
            continue
        delta = sum(a) / len(a) - sum(b) / len(b)
        lo, hi = boot_diff(a, b)
        p = p_two_sided(sum(a), len(a), sum(b), len(b))
        ranked.append((delta, m, a, b, lo, hi, p))
    for delta, m, a, b, lo, hi, p in sorted(ranked, reverse=True):
        flag = "" if (len(a) >= 5 and len(b) >= 5) else "  low-n"
        print(f"{m:<24}{len(a):>4}{sum(a)/len(a):>8.1%}{len(b):>4}{sum(b)/len(b):>8.1%}"
              f"{delta:>+9.1%}{f'[{lo:+.1%},{hi:+.1%}]':>18}{p:>8.3f}{flag}")

    promoted = [m for delta, m, a, b, lo, hi, p in sorted(ranked, reverse=True)
                if delta > 0 and p < 0.10 and len(a) >= 10 and len(b) >= 10]
    print("\npromote:", ", ".join(promoted) if promoted else "nothing clears delta>0, p<0.10, n>=10")


def summary(args) -> None:
    con = db_open(Path(args.out))
    report(con, args.behavior, args.model, args.out)
    con.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Attribute ASR to frames and modifiers.")
    ap.add_argument("--behavior", required=True)
    ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--provider", choices=["deepseek", "nvidia"], default="deepseek")
    ap.add_argument("--judge-model", default="deepseek-chat")
    ap.add_argument("--rolls", type=int, default=3)
    ap.add_argument("--passes", type=int, default=2, help="independent judge passes per attempt")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--frames", default=None, help="comma list of base_frame values")
    ap.add_argument("--limit", type=int, default=None, help="max files per frame")
    ap.add_argument("--out", default=str(DEFAULT_DB))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--summary", action="store_true", help="report from the DB, no API calls")
    args = ap.parse_args()
    summary(args) if args.summary else run(args)


if __name__ == "__main__":
    main()
