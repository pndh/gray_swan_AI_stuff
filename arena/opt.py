"""Submission optimisation layer.

Goals
- never launch a (scenario, model, tag-class) twice
- never leave a launched chat unresolved if it can still be reaped
- never launch on a model the panel already marks Closed
- keep launches non-blocking and fast (no gateway restart per launch)

Usage
  python3 arena/opt.py status
  python3 arena/opt.py reap [seconds]
  python3 arena/opt.py matrix
"""
import json, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "runs.jsonl")
DONE = {"ACCEPTED", "REJECTED", "HUNG", "LAUNCH_FAIL", "RUNFAIL"}


def load():
    rows = []
    try:
        with open(LEDGER) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return rows


def seen(rows):
    """(scenario, model, tag-class) already attempted."""
    out = set()
    for r in rows:
        tag = str(r.get("tag") or "")
        cls = re.sub(r"\.(eagle|copper|glass|gold|lion|penguin|quartz|sand|capy|rhino|dolphin|jumbo|tin|steel|tungsten|frog|obsidian|paper|pink)\b.*$", "", tag)
        out.add((r.get("scenario"), r.get("model"), cls))
    return out


def unresolved(rows):
    return [r for r in rows if r.get("verdict") not in DONE]


def cmd_status():
    rows = load()
    from collections import Counter
    print("ledger rows:", len(rows))
    print("verdicts:", dict(Counter(r.get("verdict") for r in rows)))
    un = unresolved(rows)
    print("unresolved:", len(un))
    w3 = [r for r in rows if str(r.get("tag", "")).startswith(("w3s", "smoke"))]
    print("wave-3 rows:", len(w3), dict(Counter(r.get("verdict") for r in w3)))
    print("accepted:", [r.get("chat") for r in rows if r.get("verdict") == "ACCEPTED"])


def fast_poll(chat):
    """Read the verdict from raw SSR HTML - no navigation, no render."""
    js = """(async()=>{const u=location.origin+'/arena/challenge/ipi-black-2026?chatId='+%s;
      const res=await fetch(u,{credentials:'include'});
      const txt=await res.text();
      const m=txt.match(/gradeStatus:"(\\w+)"/);
      if(!m||m[1]==='none') return 'pending';
      return m[1];})()""" % json.dumps(chat)
    try:
        r = run.js(js)
    except Exception:
        return None
    if r == "success":
        return "ACCEPTED"
    if r == "fail":
        return "REJECTED"
    return None


def cmd_reap_fast(budget=300):
    rows = load()
    un = unresolved(rows)
    if not un:
        print("nothing unresolved")
        return 0
    print("fast-reaping", len(un), "chats,", budget, "s budget")
    resolved, t0 = 0, time.time()
    for r in un:
        if time.time() - t0 > budget:
            print("budget reached")
            break
        chat = r.get("chat")
        if not chat:
            continue
        v = fast_poll(chat)
        if v:
            run.record({"ts": time.time(), "scenario": r.get("scenario"),
                        "model": r.get("model"), "tag": r.get("tag"),
                        "chat": chat, "verdict": v})
            resolved += 1
    print("resolved", resolved, "of", len(un), "in %.0fs" % (time.time() - t0))
    return resolved


def cmd_reap(budget=300):
    """Poll unresolved chats and record any verdict. Returns count resolved."""
    rows = load()
    un = unresolved(rows)
    if not un:
        print("nothing unresolved")
        return 0
    print("reaping", len(un), "chats with a", budget, "s budget")
    resolved = 0
    t0 = time.time()
    for r in un:
        if time.time() - t0 > budget:
            print("budget reached")
            break
        chat = r.get("chat")
        if not chat:
            continue
        try:
            res = run.poll_once(chat)
        except Exception:
            continue
        v = res.get("verdict")
        if v:
            run.record({"ts": time.time(), "scenario": r.get("scenario"),
                        "model": r.get("model"), "tag": r.get("tag"),
                        "chat": chat, "verdict": v})
            resolved += 1
            print(" ", r.get("scenario"), r.get("model"), "->", v, flush=True)
    print("resolved", resolved, "of", len(un))
    return resolved


def cmd_matrix():
    rows = load()
    from collections import defaultdict, Counter
    m = defaultdict(Counter)
    for r in rows:
        if str(r.get("tag", "")).startswith("w3"):
            m[r.get("scenario")][r.get("verdict")] += 1
    for scn in sorted(m):
        print(scn, dict(m[scn]))


def submit(scn, surface, slots, models, tag_base, skip_seen=True):
    """Launch on models that have not had this class; returns list of chat ids."""
    rows = load()
    s = seen(rows)
    launched = []
    for m in models:
        if skip_seen and (scn, m, tag_base) in s:
            print("skip (already tried):", scn, m, tag_base)
            continue
        t0 = time.time()
        c = run.launch_parts(scn, m, [(surface, slots)])
        print("%-3s %-24s %s  %.1fs" % (scn, m, c, time.time() - t0), flush=True)
        if c:
            run.record({"ts": time.time(), "scenario": scn, "model": m,
                        "tag": tag_base + "." + m.split()[0].lower(), "chat": c, "verdict": None})
            launched.append((m, c))
    return launched


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        cmd_status()
    elif cmd == "reapfast":
        cmd_reap_fast(int(sys.argv[2]) if len(sys.argv) > 2 else 300)
    elif cmd == "reap":
        cmd_reap(int(sys.argv[2]) if len(sys.argv) > 2 else 300)
    elif cmd == "matrix":
        cmd_matrix()
    else:
        print("unknown command", cmd)
