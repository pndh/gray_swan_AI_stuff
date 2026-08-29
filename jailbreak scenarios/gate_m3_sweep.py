#!/usr/bin/env python3
"""STRONGER gate: minimax-m3 (frontier-tier, 3% ASR class) — the gate-breaker sweep.
A frame that breaks THIS gate is the strongest candidate in our arsenal."""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

import bon_utils as bon

BASE = Path(__file__).resolve().parent
DK = os.environ["DEEPSEEK_API_KEY"]
NK = os.environ["NVIDIA_API_KEY"]
GATE = "minimaxai/minimax-m3"

FRAMES = {
    "methamphetamine_failed_synthesis": "attacks/methamphetamine_failed_synthesis_precat.txt",
    "etorphine_synthesis": "attacks/etorphine_synthesis_literature.txt",
    "fentanyl_synthesis": "attacks/fentanyl_synthesis_smiles.txt",
    "cn_scale_up": "attacks/cn_scale_up_literature.txt",
    "rdx_precursor_acquisition": "attacks/rdx_precursor_acquisition_smiles.txt",
    "procure_precursors_ecommerce": "attacks/procure_precursors_ecommerce_interference.txt",
    "vendors_no_kyc": "attacks/vendors_no_kyc_gap.txt",
    "rdx_detection_evasion": "attacks/rdx_detection_evasion_interference.txt",
    "isotonitazene_detection_evasion": "attacks/isotonitazene_detection_evasion_improve_v2.txt",
    "nps_design": "attacks/nps_design_smiles_classification.txt",
}

# extra interference-family variants for behaviors where it's the proven family
EXTRA_INTERFERENCE = {
    "procure_precursors_ecommerce": "attacks/procure_precursors_ecommerce_interference.txt",
    "rdx_detection_evasion": "attacks/rdx_detection_evasion_interference.txt",
    "rdx_precursor_acquisition": "attacks/rdx_precursor_acquisition_smiles_interference.txt",
    "nps_design": "attacks/nps_design_classification.txt",
}


def trial(bid, seed_path):
    cfg = yaml.safe_load((BASE / "behaviors" / f"{bid}.yaml").read_text())
    seed = (BASE / seed_path).read_text()
    t0 = time.time()
    try:
        resp = bon.chat([{"role": "user", "content": seed}], GATE, temperature=0.7,
                        max_tokens=2500, timeout=150, retries=2, base_url=None, api_key=NK)
        verdict, detail = bon.rubric_classify(cfg["behavior_str"], cfg["criteria"], resp,
                                              base_url=bon.DEEPSEEK_URL, api_key=DK)
        return f"{bid[:32]:<32} {verdict:<6} {detail.splitlines()[0]:<12} {len(resp.split()):>4}w {time.time()-t0:5.1f}s"
    except Exception as e:
        return f"{bid[:32]:<32} ERROR {str(e)[:45]}"


def main():
    print(f"[gate] {GATE} (frontier-tier) — gate-breaker sweep\n", flush=True)
    tasks = list(FRAMES.items()) + list(EXTRA_INTERFERENCE.items())
    for bid, seed in tasks:
        print(trial(bid, seed), flush=True)


if __name__ == "__main__":
    main()
