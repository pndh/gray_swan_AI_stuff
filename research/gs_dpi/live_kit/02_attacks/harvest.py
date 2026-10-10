#!/usr/bin/env python3
"""Index every attack/payload/technique file in the repo into one CSV.

Usage:
  python3 harvest.py            # writes attack_index.csv next to this file
  python3 pull.py <substr>      # print matching attacks (see pull.py)
"""
import csv
import re
from pathlib import Path

KIT = Path(__file__).resolve().parent
ROOT = KIT.parents[3]  # repo root

SCOPE = {
    "vendors/ipi_arena_os/data/coding": "arena-coding-behavior",
    "vendors/ipi_arena_os/examples/attacks": "released-ipi-attack",
    "research/gs_ipi_attacks": "released-95-corpus",
    "competition/attacks/fresh_variants": "hazardhunt-direct-variants",
    "competition/attacks/targeted": "hazardhunt-targeted",
    "competition/attacks/versions": "hazardhunt-versioned",
    "competition/attacks/misc_category": "hazardhunt-misc",
    "competition/attacks/archive": "hazardhunt-archive",
    "competition/worked": "arena-wins",
    "competition/trajectory/payloads": "campaign-payload",
    "ipi_legacy/scenarios": "ipi-scenario",
    "ipi_legacy/submissions": "ipi-submission",
    "attacks/families": "direct-frame-families",
    "sandbox/harnesses": "harness-attack",
    "arsenal": "technique-doc",
}
ROOTS_EXTRA = ["attacks"]  # direct frames at repo root (non-recursive dirs handled below)

EXTS = {".txt", ".md", ".json", ".jsonl"}


def first_line(p: Path) -> str:
    try:
        with p.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line:
                    return re.sub(r"\s+", " ", line)[:160]
    except OSError:
        pass
    return ""


def classify(rel: str) -> str:
    for prefix, fam in SCOPE.items():
        if rel.startswith(prefix):
            return fam
    if rel.startswith("attacks/"):
        return "direct-frame"
    return "other"


def main():
    rows = []
    for base, fam in SCOPE.items():
        d = ROOT / base
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix in EXTS:
                rel = str(p.relative_to(ROOT))
                rows.append({
                    "id": rel,
                    "family": fam,
                    "ext": p.suffix,
                    "bytes": p.stat().st_size,
                    "lines": sum(1 for _ in p.open(encoding="utf-8", errors="ignore")),
                    "first_line": first_line(p),
                })
    # repo-root attack files not under a family dir
    for p in sorted((ROOT / "attacks").glob("*")):
        if p.is_file() and p.suffix in EXTS:
            rel = str(p.relative_to(ROOT))
            if not any(r["id"] == rel for r in rows):
                rows.append({
                    "id": rel, "family": "direct-frame", "ext": p.suffix,
                    "bytes": p.stat().st_size,
                    "lines": sum(1 for _ in p.open(encoding="utf-8", errors="ignore")),
                    "first_line": first_line(p),
                })

    out = KIT / "attack_index.csv"
    with out.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["id", "family", "ext", "bytes", "lines", "first_line"])
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    counts = Counter(r["family"] for r in rows)
    print(f"indexed {len(rows)} files -> {out}")
    for fam, n in counts.most_common():
        print(f"  {n:5d}  {fam}")


if __name__ == "__main__":
    main()
