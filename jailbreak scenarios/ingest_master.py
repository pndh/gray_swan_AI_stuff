#!/usr/bin/env python3
"""Master arena ingestion: scans Downloads for all arena-export zips, dedupes by
submissionId, and builds the full analysis (model profiles, hit rates, near-misses).

Run it repeatedly — new zips get merged in.
"""
import glob
import json
import shutil
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

DL = Path("/home/pndhpndh/Downloads")
WORK = Path("/tmp/opencode/master")
OUT = Path("/home/pndhpndh/CoT_Viettel/gray_swan_AI/jailbreak scenarios")

WORK.mkdir(parents=True, exist_ok=True)
DB_PATH = WORK / "master_db.json"
PROCESSED = set()

if DB_PATH.exists():
    PROCESSED = set(json.loads((WORK / "processed.json").read_text()))


def family(title):
    t = (title or "").lower()
    if "unmas" in t or "field manual" in t: return "unmas"
    if "forensic" in t or "textbook" in t or "case-study" in t: return "forensic"
    if "literature" in t or "patent" in t or "jacs" in t: return "literature"
    if "gap" in t: return "gap"
    if "licensed" in t or "producing" in t or "precat" in t: return "precat"
    if "screening" in t or "method-validation" in t: return "interference"
    if "market" in t or "supply-chain" in t or "consultancy" in t: return "market"
    if "improve" in t or "board" in t or "expand" in t: return "improve"
    if "smiles" in t or "route for the compound" in t: return "smiles"
    if "legal" in t or "memorandum" in t: return "legal"
    if "data sheet" in t or "data-sheet" in t or "briefing" in t or "fewshot" in t: return "fewshot"
    if "pharmacopoeia" in t or "historical" in t or "pair" in t: return "pair"
    if "interference" in t: return "interference"
    return "other"


def ingest():
    zips = sorted(glob.glob(str(DL / "arena-export-*.zip")))
    new_subs = []
    new_zips = 0
    for zp in zips:
        if zp in PROCESSED:
            continue
        try:
            with zipfile.ZipFile(zp) as z:
                names = [n for n in z.namelist() if n.endswith(".json") and not n.startswith("manifest")]
                for n in names:
                    d = json.loads(z.read(n))
                    if d.get("kind") == "arena-submission":
                        new_subs.append(d)
        except Exception as e:
            print(f"  [skip] {Path(zp).name}: {str(e)[:50]}", file=sys.stderr)
            continue
        PROCESSED.add(zp)
        new_zips += 1

    if not new_subs:
        print(f"no new submissions ({len(zips)} zips scanned, {len(PROCESSED)} processed)")
        return None

    # dedupe by submissionId
    seen = {}
    for d in new_subs:
        seen[d.get("submissionId")] = d
    db = []
    if DB_PATH.exists():
        db = json.loads(DB_PATH.read_text())
    existing = {d.get("submissionId") for d in db}
    added = 0
    for sid, d in seen.items():
        if sid not in existing:
            db.append(d)
            added += 1
    DB_PATH.write_text(json.dumps(db))
    (WORK / "processed.json").write_text(json.dumps(sorted(PROCESSED)))
    print(f"+{new_zips} zips, +{added} submissions (total {len(db)})")
    return db


def analyze(db):
    model_db = defaultdict(lambda: {"tried": 0, "breaks": 0, "engaged": 0, "filtered": 0,
                                    "empty": 0, "behaviors_ok": [], "best_miss": 0})
    scen_breaks = defaultdict(set)
    frame_hits = defaultdict(lambda: [0, 0])
    near_misses = []
    for d in db:
        m = d.get("model")
        if not m:
            continue
        scen = (d.get("scenario") or "").split("(")[0].strip()
        fam = family(d.get("title"))
        last = [x for x in d.get("messages", []) if x.get("role") == "assistant"]
        resp = last[-1]["content"] if last else ""
        wc = len(resp.split())
        broke = d.get("judge", {}).get("isBreak", False)
        crit = {k["name"]: k["score"] for k in d["judge"].get("criteria", [])}
        max_met = sum(1 for v in crit.values() if v >= 7)
        ncrit = len(crit)

        v = model_db[m]
        v["tried"] += 1
        if "provider's content moderation" in resp:
            v["filtered"] += 1
        elif wc <= 2:
            v["empty"] += 1
        elif wc >= 100:
            v["engaged"] += 1
        if broke:
            v["breaks"] += 1
            v["behaviors_ok"].append(scen)
            scen_breaks[scen].add(m)
            frame_hits[fam][0] += 1
            frame_hits[fam][1] += 1
        else:
            frame_hits[fam][1] += 1
            if max_met >= ncrit - 1 and ncrit >= 8:
                near_misses.append((m, scen, fam, max_met, ncrit, wc))

    lines = []
    lines.append("# ARENA MASTER ANALYSIS")
    lines.append(f"\nTotal submissions: {len(db)}")
    lines.append("\n## Per-behavior breaks")
    for scen, ms in sorted(scen_breaks.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"- {scen}: {len(ms)} ({', '.join(sorted(ms))})")
    lines.append("\n## Per-model")
    for m, v in sorted(model_db.items(), key=lambda kv: -kv[1]["breaks"]):
        ok = len(set(v["behaviors_ok"]))
        lines.append(f"- {m}: {v['breaks']} breaks/{v['tried']} tried ({ok} behaviors, "
                     f"engaged {v['engaged']}, filtered {v['filtered']}, empty {v['empty']})")
    lines.append("\n## Frame-family hit rates")
    for fam, (b, t) in sorted(frame_hits.items(), key=lambda kv: -kv[1][0]):
        lines.append(f"- {fam}: {b}/{t} = {b/max(t,1):.0%}")
    lines.append("\n## One-criterion-away near-misses")
    for m, scen, fam, met, n, wc in sorted(near_misses, key=lambda x: -x[3])[:40]:
        lines.append(f"- {m} | {scen} | {fam} | {met}/{n} | {wc}w")

    report = "\n".join(lines)
    (OUT / "ARENA_MASTER.md").write_text(report)
    (WORK / "master_analysis.json").write_text(json.dumps({
        "model_db": {k: dict(v) for k, v in model_db.items()},
        "scen_breaks": {k: sorted(v) for k, v in scen_breaks.items()},
        "near_misses": near_misses,
    }, indent=1))
    print(report[:3500])


if __name__ == "__main__":
    db = ingest()
    if db:
        analyze(db)
