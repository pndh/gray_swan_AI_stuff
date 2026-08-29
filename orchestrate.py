#!/usr/bin/env python3
"""BoN practice loop for Gray Swan behaviors (HarmBench-style track).

Sample N prompt variants (LLM-rewrites at temp 1.0 + text augmentations + optional
image perturbations), screen each against a local proxy target, score with the
vendored HarmBench classifier, then harvest everything to CSV and emit top-k
submissions ready to paste into the arena.

Usage:
  export NVIDIA_API_KEY=...
  python3 orchestrate.py --behavior jailbreak_game_piracy                  # full screen
  python3 orchestrate.py --behavior jailbreak_game_piracy --n 20           # cap trials
  python3 orchestrate.py --behavior jailbreak_game_piracy --dry-run        # plan only, no API calls
"""
import argparse
import csv
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

import bon_utils as bon

BASE_DIR = Path(__file__).resolve().parent
BEHAVIORS_DIR = BASE_DIR / "behaviors"

VERDICT_ORDER = {"BREAK": 4, "TOO_SHORT": 2, "NO": 2, "ERROR": 1}
CSV_FIELDS = [
    "behavior_id", "variant_id", "kind", "prompt", "image", "response",
    "classifier", "verdict", "model", "temperature", "elapsed_s",
]


def build_trials(cfg):
    """Build the trial list: seed + LLM variants + text augs + image perturbs."""
    seed = cfg["seed_text"]
    image = cfg.get("image")
    trials = [{"variant_id": 0, "kind": "seed", "prompt": seed, "image": image}]
    for rep in range(1, cfg.get("_seed_repeats", 1)):
        trials.append({"variant_id": len(trials), "kind": "seed_rep", "prompt": seed, "image": image})

    for hand_seed in cfg.get("extra_seeds", []):
        trials.append({"variant_id": len(trials), "kind": "handseed", "prompt": hand_seed, "image": image})

    # MSJ-style context trials: prefix seed with a compliant user/assistant history
    # (the paper's multi-shot jailbreak; here hand-built "no-sorry" tuples).
    for msj in cfg.get("msj_tuples", []):
        u, a = msj
        history = f"User: {u}\n\nAssistant: {a}"
        trials.append({"variant_id": len(trials), "kind": "msj",
                       "prompt": f"{history}\n\nUser: {seed}", "image": image})
        for hand_seed in cfg.get("extra_seeds", [])[:1]:
            trials.append({"variant_id": len(trials), "kind": "msj",
                           "prompt": f"{history}\n\nUser: {hand_seed}", "image": image})

    sampler_model = cfg.get("sampler_model", cfg.get("classifier_model", "openai/gpt-oss-120b"))
    sampler_kwargs = cfg.get("_sampler_kwargs", {})
    n_llm = cfg.get("n_llm_variants", 0)

    def _sample(i):
        variant = bon.sample_variant(
            seed, model=sampler_model, temperature=cfg.get("sampler_temperature", 1.0),
            note=cfg.get("sampler_note", ""),
            structured=cfg.get("sampler_structured", False), **sampler_kwargs,
        )
        return i, variant

    llm_results = []
    if n_llm:
        with ThreadPoolExecutor(max_workers=min(8, n_llm)) as pool:
            futs = [pool.submit(_sample, i) for i in range(n_llm)]
            done = 0
            for fut in as_completed(futs):
                i, variant = fut.result()
                done += 1
                print(f"[sample] {done}/{n_llm} variant #{i} {'OK' if variant else 'EMPTY'}", flush=True)
                llm_results.append((i, variant))
    for i, variant in sorted(llm_results):
        if variant:
            trials.append({"variant_id": len(trials), "kind": "llm", "prompt": variant, "image": image})

    sigma = cfg.get("sigma", 0.4)
    for aug_name, fn in [
        ("word_scramble", bon.apply_word_scrambling),
        ("rand_caps", bon.apply_random_capitalization),
        ("ascii", bon.apply_ascii_noising),
    ]:
        trials.append({
            "variant_id": len(trials), "kind": f"aug_{aug_name}",
            "prompt": fn(seed, sigma), "image": image,
        })

    n_perturbs = cfg.get("n_image_perturbs", 0)
    if n_perturbs and image:
        perturb_dir = BASE_DIR / "harvest" / f"{cfg['behavior_id']}_perturbed"
        perturb_dir.mkdir(parents=True, exist_ok=True)
        kinds = ["blur", "noise", "brightness"]
        for i in range(min(n_perturbs, len(kinds))):
            kind = kinds[i % len(kinds)]
            out = perturb_dir / f"perturb_{kind}_{i}.png"
            bon.perturb_image(image, out, kind, seed=42 + i)
            trials.append({
                "variant_id": len(trials), "kind": f"image_{kind}",
                "prompt": seed, "image": str(out),
            })
    return trials[: cfg.get("total_n", len(trials))]


def run_trial(cfg, trial, behavior):
    """One trial: target call -> too-short filter -> classifier. Returns row dict."""
    t0 = time.time()
    try:
        response = bon.call_target(
            trial["prompt"], cfg["target_model"], cfg.get("target_temperature", 0.7),
            image_path=trial.get("image"), **cfg.get("_target_kwargs", {}),
        )
        if bon.too_short(behavior, response):
            verdict, classifier = "TOO_SHORT", ""
        elif cfg.get("criteria"):
            verdict, classifier = bon.rubric_classify(
                behavior, cfg["criteria"], response, cfg["classifier_model"],
                cfg.get("classifier_temperature", 0.0), **cfg.get("_classifier_kwargs", {}))
            verdict = "BREAK" if verdict == "BREAK" else "NO"
        else:
            classifier = bon.classify(behavior, response, cfg["classifier_model"],
                                      cfg.get("classifier_temperature", 0.0),
                                      **cfg.get("_classifier_kwargs", {}))
            verdict = "BREAK" if classifier == "Yes" else "NO"
    except Exception as exc:
        response, classifier, verdict = f"<error: {exc}>", "", "ERROR"
    return {
        "behavior_id": cfg["behavior_id"], "variant_id": trial["variant_id"],
        "kind": trial["kind"], "prompt": trial["prompt"], "image": trial.get("image") or "",
        "response": response, "classifier": classifier, "verdict": verdict,
        "model": cfg["target_model"], "temperature": cfg.get("target_temperature", 0.7),
        "elapsed_s": round(time.time() - t0, 1),
    }


def write_submissions(rows, cfg, behavior, out_dir, asr, tag=""):
    """top_k: real BREAKs first (with target response embedded for quality checks).
    If zero breaks, fall back to near-misses ranked by response engagement (length)."""
    breaks = [r for r in rows if r["verdict"] == "BREAK"]
    misses = sorted(
        [r for r in rows if r["verdict"] not in ("BREAK", "ERROR", "TOO_SHORT")],
        key=lambda r: len((r.get("response") or "").split()), reverse=True,
    )
    top = breaks or misses[: min(5, len(misses))]
    sub_dir = out_dir / "top_k"
    sub_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "behavior_id": cfg["behavior_id"], "behavior_str": behavior,
        "target_model": cfg["target_model"], "n_trials": len(rows), "asr": asr,
        "tag": tag, "top_k": [],
    }
    print("\n=== top-k candidates ===")
    for rank, r in enumerate(top, 1):
        resp = r.get("response") or ""
        name = f"{cfg['behavior_id']}_{rank:02d}_{r['kind']}_{int(r['variant_id']):03d}.txt"
        body = (f"PROMPT:\n{r['prompt']}\n\n--- target response ({r['verdict']} / {r['classifier']}) ---\n\n{resp}")
        (sub_dir / name).write_text(body, encoding="utf-8")
        manifest["top_k"].append({
            "rank": rank, "file": name, "variant_id": r["variant_id"], "kind": r["kind"],
            "verdict": r["verdict"], "classifier": r["classifier"], "image": r.get("image"),
            "response_words": len(resp.split()),
        })
        preview = " ".join(resp.split())[:100]
        print(f"  #{rank} {r['kind']:<14} [{r['verdict']:<6} {r['classifier']}] {preview}...", flush=True)
    manifest_path = out_dir / f"{cfg['behavior_id']}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nsubmissions -> {sub_dir}  (manifest -> {manifest_path})")


def rejudge(rows, cfg, behavior, concurrency):
    """Re-score an existing harvest with a different classifier (e.g. deepseek)."""
    lock = threading.Lock()

    def _judge(row):
        if row["verdict"] in ("TOO_SHORT", "ERROR") or not row.get("response"):
            return row
        try:
            if cfg.get("criteria"):
                verdict, classifier = bon.rubric_classify(
                    behavior, cfg["criteria"], row["response"], cfg["classifier_model"],
                    cfg.get("classifier_temperature", 0.0), **cfg.get("_classifier_kwargs", {}))
                row["verdict"] = "BREAK" if verdict == "BREAK" else "NO"
            else:
                c = bon.classify(behavior, row["response"], cfg["classifier_model"],
                                 cfg.get("classifier_temperature", 0.0),
                                 **cfg.get("_classifier_kwargs", {}))
                row["verdict"] = "BREAK" if c == "Yes" else "NO"
                classifier = c
            row["classifier"] = classifier
        except Exception as exc:
            row["verdict"], row["classifier"] = "ERROR", f"rejudge_failed:{exc}"
        return row

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        return list(pool.map(_judge, rows))


def main():
    ap = argparse.ArgumentParser(description="BoN screen -> harvest -> submit loop.")
    ap.add_argument("--behavior", required=True, help="behavior id, e.g. jailbreak_game_piracy")
    ap.add_argument("--behaviors-dir", default=str(BEHAVIORS_DIR),
                    help="dir containing <behavior>.yaml (default: repo behaviors/)")
    ap.add_argument("--n", type=int, default=None, help="cap total trials")
    ap.add_argument("--n-llm", type=int, default=None, help="override n_llm_variants")
    ap.add_argument("--repeats", type=int, default=1,
                    help="duplicate the seed trial N times (flip-flop farming; skips LLM sampling)")
    ap.add_argument("--dry-run", action="store_true", help="plan trials only, no API calls")
    ap.add_argument("--no-llm", action="store_true", help="skip LLM variant sampling")
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--target-model", default=None)
    ap.add_argument("--target-provider", default=None, choices=["nvidia", "deepseek"])
    ap.add_argument("--classifier-model", default=None)
    ap.add_argument("--seed-text", default=None, help="override seed_text (e.g. evolve from a winning attack)")
    ap.add_argument("--extra-seeds-file", default=None,
                    help="txt file, one prompt per line: elite seeds to add as trials")
    ap.add_argument("--text-only", action="store_true", help="no image input (text-only targets like gpt-oss)")
    ap.add_argument("--image", default=None, help="override image path (for vision targets)")
    ap.add_argument("--rejudge", action="store_true",
                    help="re-classify the existing harvest CSV with a different classifier and rewrite top_k")
    ap.add_argument("--out-dir", default="harvest")
    args = ap.parse_args()

    cfg_path = Path(args.behaviors_dir) / f"{args.behavior}.yaml"
    if not cfg_path.exists():
        raise SystemExit(f"behavior config not found: {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if args.n:
        cfg["total_n"] = args.n
    if args.n_llm:
        cfg["n_llm_variants"] = args.n_llm
    if args.repeats > 1:
        cfg["n_llm_variants"] = 0
        cfg["_seed_repeats"] = args.repeats
    if args.no_llm:
        cfg["n_llm_variants"] = 0
    if args.dry_run:
        cfg["n_llm_variants"] = 0
    if args.concurrency:
        cfg["concurrency"] = args.concurrency
    if args.target_model:
        cfg["target_model"] = args.target_model
    if args.target_provider:
        cfg["target_provider"] = args.target_provider
    if args.classifier_model:
        cfg["classifier_model"] = args.classifier_model
    if args.seed_text:
        cfg["seed_text"] = args.seed_text
    if args.extra_seeds_file:
        p = Path(args.extra_seeds_file)
        if p.suffix == ".jsonl":
            extra = [json.loads(ln)["prompt"].strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        else:
            extra = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()
                     if ln.strip() and not ln.startswith("#")]
        cfg.setdefault("extra_seeds", []).extend(extra)
        print(f"[config] +{len(extra)} elite seeds from {args.extra_seeds_file}", flush=True)
    if args.text_only:
        cfg["image"] = None
        cfg["n_image_perturbs"] = 0
    if args.image:
        cfg["image"] = args.image

    # sampler provider resolution (e.g. deepseek for fast iteration)
    if cfg.get("sampler_provider") == "deepseek":
        cfg["_sampler_kwargs"] = {
            "base_url": bon.DEEPSEEK_URL,
            "api_key": os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("NVIDIA_API_KEY"),
        }
    # target provider resolution
    if cfg.get("target_provider") == "deepseek":
        cfg["_target_kwargs"] = {
            "base_url": bon.DEEPSEEK_URL,
            "api_key": os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("NVIDIA_API_KEY"),
        }
    else:
        cfg["_target_kwargs"] = {}
    # classifier provider resolution (NVIDIA gpt-oss returns EMPTY on harmful content -> use deepseek)
    if cfg.get("classifier_provider") == "deepseek":
        cfg["_classifier_kwargs"] = {
            "base_url": bon.DEEPSEEK_URL,
            "api_key": os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("NVIDIA_API_KEY"),
        }
    else:
        cfg["_classifier_kwargs"] = {}

    print(f"[config] behavior={cfg['behavior_id']} target={cfg['target_model']} "
          f"sampler={cfg.get('sampler_model')} image={cfg.get('image')} n_llm={cfg.get('n_llm_variants')}",
          flush=True)
    behavior = cfg["behavior_str"]
    random.seed(0)
    trials = build_trials(cfg)
    print(f"[plan] {len(trials)} trials for '{cfg['behavior_id']}' "
          f"(target={cfg['target_model']}, image={cfg.get('image')})", flush=True)
    for t in trials:
        preview = " ".join(t["prompt"].split())[:90]
        print(f"  #{t['variant_id']:>3} {t['kind']:<14} {preview}...", flush=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{cfg['behavior_id']}_screen.csv"

    # --- rejudge mode --------------------------------------------------------
    if args.rejudge:
        if not csv_path.exists():
            raise SystemExit(f"no harvest to rejudge: {csv_path}")
        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        print(f"[rejudge] re-scoring {len(rows)} rows with {cfg['classifier_model']} "
              f"(provider={cfg.get('classifier_provider')})", flush=True)
        rows = rejudge(rows, cfg, behavior, cfg.get("concurrency", 8))
        with csv_path.open("w", encoding="utf-8", newline="") as h:
            w = csv.DictWriter(h, fieldnames=CSV_FIELDS)
            w.writeheader()
            w.writerows(rows)
        n_break = sum(1 for r in rows if r["verdict"] == "BREAK")
        print(f"[rejudge] BREAK: {n_break}/{len(rows)}")
        write_submissions(rows, cfg, behavior, out_dir, n_break / len(rows) if rows else 0.0, tag="rejudge")
        return

    with csv_path.open("w", encoding="utf-8", newline="") as h:
        csv.DictWriter(h, fieldnames=CSV_FIELDS).writeheader()

    if args.dry_run:
        print(f"\n[dry-run] no API calls; trial plan -> {csv_path}")
        return

    lock = threading.Lock()
    rows = []
    n_break = 0
    with ThreadPoolExecutor(max_workers=cfg.get("concurrency", 8)) as pool:
        futs = {pool.submit(run_trial, cfg, t, behavior): t for t in trials}
        for fut in as_completed(futs):
            row = fut.result()
            with lock:
                rows.append(row)
                with csv_path.open("a", encoding="utf-8", newline="") as h:
                    csv.DictWriter(h, fieldnames=CSV_FIELDS).writerow(row)
                if row["verdict"] == "BREAK":
                    n_break += 1
            status = "BREAK" if row["verdict"] == "BREAK" else row["verdict"]
            print(f"[trial #{row['variant_id']:>3} {row['kind']:<14}] {status:<8} "
                  f"({row['elapsed_s']}s)", flush=True)

    rows.sort(key=lambda r: VERDICT_ORDER.get(r["verdict"], 0), reverse=True)
    asr = n_break / len(rows) if rows else 0.0
    print(f"\n=== tally ({len(rows)} trials) ===")
    for v in ("BREAK", "NO", "TOO_SHORT", "ERROR"):
        c = sum(1 for r in rows if r["verdict"] == v)
        if c:
            print(f"  {v}: {c}")
    print(f"ASR (BREAK): {asr:.0%}")

    # --- submissions ---------------------------------------------------------
    write_submissions(rows, cfg, behavior, out_dir, asr)
    print(f"\nharvest -> {csv_path}")


if __name__ == "__main__":
    main()
