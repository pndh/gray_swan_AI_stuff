"""Transcribe competition screenshots with a vision model (NVIDIA) for context extraction."""
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI")
import bon_utils as bon

PROMPT = (
    "Transcribe ALL text visible in this screenshot VERBATIM, preserving structure and line breaks. "
    "Also briefly describe: (1) what kind of UI this is, (2) any rules, objectives, targets, or models "
    "mentioned, (3) any visible buttons/fields. If it's a competition or challenge description, be "
    "exhaustive. Output format:\n"
    "=== TRANSCRIPT ===\n<verbatim text>\n=== SUMMARY ===\n<UI type + key details>"
)


def transcribe(path, model, key):
    return bon.call_target(PROMPT, model, temperature=0.0, image_path=str(path),
                           max_tokens=2500, base_url=None, api_key=key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="meta/llama-3.2-90b-vision-instruct")
    ap.add_argument("--concurrency", type=int, default=3)
    args = ap.parse_args()

    src, out = Path(args.src), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    key = os.environ["NVIDIA_API_KEY"]
    files = sorted(src.glob("*.png"))
    print(f"[transcribe] {len(files)} images -> {out} (model={args.model})", flush=True)

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futs = {pool.submit(transcribe, f, args.model, key): f for f in files}
        for fut in as_completed(futs):
            f = futs[fut]
            try:
                text = fut.result()
            except Exception as exc:
                text = f"<transcribe error: {exc}>"
            target = out / f"{f.stem}.md"
            target.write_text(text, encoding="utf-8")
            print(f"[ok] {f.name} ({len(text.split())} words) -> {target.name}", flush=True)


if __name__ == "__main__":
    main()
