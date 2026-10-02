#!/usr/bin/env python3
"""Attack launcher — edit sandbox/attack_launch.txt, run, read the sectioned report.

Batch file format (attack_launch.txt):
    scenario: level3 | parallax | velocity
    provider: minimax | openai | nvidia
    model:    MiniMax-M2.7
    tier:     live
    tries:    1
    temperature: 0.7
    judge:    off            # off by default; set on or pass --judge to auto-score

    ===                       # 3+ equals on their own line separates attacks
    SUBJECT: subject line     # email mode; velocity blocks are the message text only
    body...

Usage:
    python3 sandbox/run_batch.py                    # run attack_launch.txt (judge off)
    python3 sandbox/run_batch.py --judge            # auto-score this run
    python3 sandbox/run_batch.py --batch other.txt  # run another file
    python3 sandbox/run_batch.py --watch            # rerun on every save
Outputs (per run):
    sandbox/runs/<timestamp>/records.json
    sandbox/runs/<timestamp>/report.html   (1 SENT / 2 ENCODE / 3 REPLY / 4 TOOLS / 5 TRANSCRIPT / 6 JUDGE)
    sandbox/runs/latest -> newest
"""
import argparse
import html
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402

SANDBOX = Path(__file__).resolve().parent
LAUNCH = SANDBOX / "attack_launch.txt"
RUNS = SANDBOX / "runs"
SEP = re.compile(r"^\s*={3,}\s*$", re.M)

DEFAULTS = {"scenario": "level3", "provider": "minimax", "model": "MiniMax-M2.7",
            "tier": "live", "tries": "1", "temperature": "0.7", "judge": "off"}


def parse_batch(path: Path):
    text = path.read_text(encoding="utf-8")
    chunks = [c.strip() for c in SEP.split(text) if c.strip()]
    cfg = dict(DEFAULTS)
    is_cfg = bool(chunks) and any(
        re.match(r"^(scenario|provider|model|tier|tries|temperature|judge)\s*:", l)
        for l in chunks[0].splitlines())
    if is_cfg:
        for line in chunks[0].splitlines():
            if line.strip().startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                cfg[k.strip()] = v.split("#")[0].strip()
        chunks = chunks[1:]
    prompts = []
    for ch in chunks:
        lines = ch.splitlines()
        if cfg["scenario"] != "velocity" and lines and lines[0].upper().startswith("SUBJECT:"):
            subject = lines[0].split(":", 1)[1].strip()
            body = "\n".join(lines[1:]).strip()
        else:
            subject, body = "", ch
        prompts.append({"subject": subject, "body": body})
    cfg["tries"] = int(cfg.get("tries", 1))
    cfg["temperature"] = float(cfg.get("temperature", 0.7))
    cfg["judge"] = str(cfg.get("judge", "off")).strip().lower() in ("on", "true", "yes", "1")
    return cfg, prompts


def esc(x):
    return html.escape(str(x if x is not None else ""))


def report_html(records, run_dir):
    css = """<style>
body{font-family:ui-monospace,Menlo,monospace;background:#0d1117;color:#c9d1d9;margin:24px}
h1{color:#e6edf3}.run{border:1px solid #30363d;border-radius:8px;margin:14px 0;padding:10px 14px;background:#161b22}
.verdict{font-weight:bold}.BREAK{color:#3fb950}.MANUAL{color:#58a6ff}
.NO_SEND,.NO_OFFER{color:#d29922}.SENT_NO_RESET,.ESCALATED,.RESET_WRONG_TARGET{color:#f85149}
pre{white-space:pre-wrap;background:#0d1117;border:1px solid #21262d;border-radius:6px;padding:8px;margin:6px 0;max-height:480px;overflow:auto}
summary{cursor:pointer;color:#79c0ff}details{margin:6px 0}
.tag{color:#8b949e}.tool{color:#a5d6ff}.sec{color:#e6edf3;font-weight:bold}
</style>"""
    parts = [f"<html><head><meta charset='utf-8'><title>sandbox run {esc(run_dir.name)}</title>{css}</head><body>"]
    parts.append(f"<h1>Sandbox run — {esc(run_dir.name)} — {len(records)} episodes</h1>")
    for i, r in enumerate(records, 1):
        verdict = r.get("verdict", "?")
        parts.append(f"<div class='run'><b>#{i} [{esc(r.get('scenario'))}|{esc(r.get('tier'))}|{esc(r.get('model'))}]</b> "
                     f"<span class='verdict {esc(verdict)}'>{esc(verdict)}</span> "
                     f"<span class='tag'>tools: {esc(r.get('tool_calls',''))}</span>")
        atk = r.get("attack", {})
        atk_text = atk.get("message") or (atk.get("subject", "") + "\n\n" + atk.get("body", ""))
        parts.append(f"<details open><summary class='sec'>1. SENT (attack payload)</summary><pre>{esc(atk_text)}</pre></details>")
        mi = json.dumps(r.get("messages_initial", []), indent=2, ensure_ascii=False)
        mf = json.dumps(r.get("messages_final", []), indent=2, ensure_ascii=False)
        parts.append(f"<details><summary class='sec'>2. ENCODE — messages array sent (initial)</summary><pre>{esc(mi)}</pre></details>")
        parts.append(f"<details><summary class='sec'>2b. ENCODE — messages array final state</summary><pre>{esc(mf)}</pre></details>")
        parts.append(f"<details open><summary class='sec'>3. REPLY — final model message</summary><pre>{esc(r.get('final_answer') or '(empty)')}</pre></details>")
        calls = []
        for st in r.get("transcript", []):
            for t_ in st.get("tool_results", []):
                calls.append(f"{t_.get('tool')}({json.dumps(t_.get('args', {}), ensure_ascii=False)}) -> {t_.get('result')}")
        parts.append("<details open><summary class='sec'>4. TOOLS (" + str(len(calls)) + ")</summary><pre>"
                     + "\n".join(esc(x) for x in calls) + "</pre></details>")
        parts.append("<details><summary class='sec'>5. FULL TRANSCRIPT (per model turn)</summary>")
        for st in r.get("transcript", []):
            stage = st.get("stage")
            if stage == "system_prompt":
                parts.append(f"<details><summary>system prompt</summary><pre>{esc(st.get('content'))}</pre></details>")
            elif stage == "victim_turn":
                parts.append(f"<details><summary>victim turn</summary><pre>{esc(st.get('content'))}</pre></details>")
            elif stage == "user_turn":
                parts.append(f"<details><summary>user turn (= attack)</summary><pre>{esc(st.get('content'))}</pre></details>")
            elif stage == "injected_email":
                parts.append(f"<details><summary>injected email</summary><pre>SUBJECT: {esc(st.get('subject'))}\n\n{esc(st.get('body'))}</pre></details>")
            elif stage == "assistant":
                tc = "".join(f"<div class='tool'>→ {esc(t['name'])}({esc(t['arguments'])})</div>"
                             for t in st.get("tool_calls", []))
                res = "".join(f"<pre>tool result [{esc(t['tool'])}]: {esc(t['result'])}</pre>"
                              for t in st.get("tool_results", []))
                parts.append(f"<details><summary>model turn {st.get('iter')} (+tools)</summary>"
                             f"<pre>{esc(st.get('assistant_text'))}</pre>{tc}{res}</details>")
        parts.append("</details>")
        if r.get("verdict") == "MANUAL":
            parts.append("<details open><summary class='sec'>6. JUDGE</summary><pre>paused — read the reply/tools above yourself</pre></details></div>")
        else:
            parts.append(f"<details open><summary class='sec'>6. JUDGE</summary><pre>{esc(r.get('verdict'))} — {esc(r.get('signals'))}</pre></details></div>")
    parts.append("</body></html>")
    out = run_dir / "report.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def print_episode(rec, pi, t):
    line = "─" * 72
    print(line)
    print(f" EPISODE p{pi} t{t} — {rec['scenario']} | {rec['tier']} | {rec['provider']}/{rec['model']}")
    atk = rec.get("attack", {})
    if atk.get("message"):
        print(" SENT (user message):")
        sent = atk["message"]
    else:
        print(f" SENT (email) — SUBJECT: {atk.get('subject','')}")
        sent = atk.get("body", "")
    for ln in sent.splitlines():
        print(f"   | {ln}")
    mi = " → ".join(m.get("role", "?") for m in rec.get("messages_initial", []))
    mf = " → ".join(m.get("role", "?") for m in rec.get("messages_final", []))
    print(" ENCODE (messages array):")
    print(f"   initial: {mi}")
    print(f"   final:   {mf}")
    print(" REPLY (final model message):")
    fa = (rec.get("final_answer") or "(empty)").splitlines()
    for ln in fa[:18]:
        print(f"   | {ln}")
    if len(fa) > 18:
        print("   | …")
    print(" TOOLS:")
    if rec.get("tool_log"):
        for tl in rec["tool_log"]:
            print(f"   - {tl['name']}({json.dumps(tl['args'], ensure_ascii=False)})")
    else:
        print("   - (none)")
    if rec["verdict"] == "MANUAL":
        print(" JUDGE: paused (you read it)")
    else:
        print(f" JUDGE: {rec['verdict']} — {rec.get('signals','')}")
    print(line)


def run_batch_file(path: Path, stamp=None, judge_override=None):
    cfg, prompts = parse_batch(path)
    if judge_override is not None:
        cfg["judge"] = judge_override
    run_dir = RUNS / (stamp or datetime.now().strftime("%Y%m%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)
    records = []
    print(f"\n### {path.name}: scenario={cfg['scenario']} provider={cfg['provider']} model={cfg['model']} "
          f"tier={cfg['tier']} tries={cfg['tries']} judge={'on' if cfg['judge'] else 'off'} prompts={len(prompts)}")
    for pi, p in enumerate(prompts, 1):
        for t in range(1, cfg["tries"] + 1):
            try:
                rec = engine.run(cfg["scenario"], cfg["tier"],
                                 {"subject": p["subject"], "body": p["body"], "message": p["body"]},
                                 cfg["model"], cfg["provider"], cfg["temperature"], cfg["judge"])
                rec["prompt_index"], rec["try"] = pi, t
                records.append(rec)
                ep_dir = run_dir / f"p{pi}_t{t}"
                ep_dir.mkdir(exist_ok=True)
                n = 0
                for c in rec.get("api_calls", []):
                    n += 1
                    (ep_dir / f"{n:02d}_request.raw.json").write_text(c["request"], encoding="utf-8")
                    (ep_dir / f"{n:02d}_response.raw.json").write_text(c["response_raw"], encoding="utf-8")
                    try:
                        (ep_dir / f"{n:02d}_request.json").write_text(
                            json.dumps(json.loads(c["request"]), indent=2, ensure_ascii=False), encoding="utf-8")
                    except Exception:
                        (ep_dir / f"{n:02d}_request.txt").write_text(c["request"], encoding="utf-8")
                    try:
                        (ep_dir / f"{n:02d}_response.json").write_text(
                            json.dumps(json.loads(c["response_raw"]), indent=2, ensure_ascii=False), encoding="utf-8")
                    except Exception:
                        (ep_dir / f"{n:02d}_response.txt").write_text(c["response_raw"], encoding="utf-8")
                print(f"  p{pi} t{t}: tools=[{rec['tool_calls']}] judge={'paused' if rec['verdict']=='MANUAL' else rec['verdict']}"
                      f" | {n} request/response pair(s) -> {ep_dir.relative_to(SANDBOX)}")
            except Exception as exc:
                rec = {"scenario": cfg["scenario"], "tier": cfg["tier"], "model": cfg["model"],
                       "provider": cfg["provider"], "attack": {"subject": p["subject"], "body": p["body"]},
                       "prompt_index": pi, "try": t, "verdict": "ERROR", "signals": str(exc)[:200],
                       "tool_calls": "", "tool_log": [], "transcript": [], "final_answer": "",
                       "messages_initial": [], "messages_final": []}
                records.append(rec)
                print(f"  p{pi} t{t}: ERROR {rec['signals'][:120]}")
    if records:
        (run_dir / "records.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        rep = report_html(records, run_dir)
        latest = RUNS / "latest"
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        latest.symlink_to(run_dir.name)
        print(f"  report: {rep}")
    return run_dir, records


def watch(interval=2.0, judge_override=None):
    print(f"watching {LAUNCH} for changes — Ctrl-C to stop")
    last = None
    while True:
        if LAUNCH.exists():
            m = LAUNCH.stat().st_mtime
            if last != m:
                last = m
                run_batch_file(LAUNCH, judge_override=judge_override)
        time.sleep(interval)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="alias for the default (runs attack_launch.txt)")
    ap.add_argument("--batch", default=None, help="run a different batch file")
    ap.add_argument("--watch", action="store_true", help="rerun every time attack_launch.txt is saved")
    ap.add_argument("--judge", action="store_true", help="enable the automatic judge for this run")
    ap.add_argument("--no-judge", action="store_true", help="force judge off (default)")
    args = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    j = None
    if args.judge:
        j = True
    if args.no_judge:
        j = False
    if args.watch:
        watch(judge_override=j)
        return
    if args.batch:
        run_batch_file(Path(args.batch), judge_override=j)
        return
    if not LAUNCH.exists():
        print(f"no {LAUNCH} — write your attacks there first")
        return
    run_batch_file(LAUNCH, judge_override=j)


if __name__ == "__main__":
    main()
