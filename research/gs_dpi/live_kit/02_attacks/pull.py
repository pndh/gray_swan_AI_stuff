#!/usr/bin/env python3
"""Pull attacks from the pre-built index by id substring or family.

Usage:
  python3 pull.py coding              # list matches
  python3 pull.py codex-launcher      # show matches with content
  python3 pull.py --family arena-coding-behavior --list
  python3 pull.py 02_attacks/attack_index.csv:path...
"""
import argparse
import csv
from pathlib import Path

KIT = Path(__file__).resolve().parent
ROOT = KIT.parents[3]
INDEX = KIT / "attack_index.csv"


def load():
    with INDEX.open(encoding="utf-8") as h:
        return list(csv.DictReader(h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default=None, help="substring of id or first_line")
    ap.add_argument("--family", default=None)
    ap.add_argument("--list", action="store_true", help="list only, no content")
    ap.add_argument("--max-bytes", type=int, default=8000, help="truncate each file")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    rows = load()
    if args.family:
        rows = [r for r in rows if r["family"] == args.family]
    if args.query:
        q = args.query.lower()
        rows = [r for r in rows if q in r["id"].lower() or q in r["first_line"].lower()]

    print(f"{len(rows)} matches")
    for r in rows[: args.limit]:
        print(f"  [{r['family']}] {r['id']}  ({r['lines']} lines) {r['first_line'][:90]}")

    if not args.list and rows:
        for r in rows[: args.limit]:
            p = ROOT / r["id"]
            print("\n" + "=" * 78 + f"\n# {r['id']}\n" + "=" * 78)
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError as e:
                print(f"<unreadable: {e}>")
                continue
            print(text[: args.max_bytes] + ("\n<...truncated...>" if len(text) > args.max_bytes else ""))


if __name__ == "__main__":
    main()
