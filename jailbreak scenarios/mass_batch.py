#!/usr/bin/env python3
"""MASS-BATCH GENERATOR: every behavior x every frame variant, submission-ready.
Prints per-behavior packs: each frame's full text + the model targets.
Usage: python3 mass_batch.py [--behavior iso] [--out submissions_mass/]
"""
import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ATK = BASE / "attacks"

# All viable frames per behavior (every family that ever produced content)
INVENTORY = {
    "methamphetamine_failed_synthesis": [
        "methamphetamine_failed_synthesis_precat.txt",
        "attacks/forensic/methamphetamine_failed_synthesis_forensic.txt" if False else "forensic/methamphetamine_failed_synthesis_forensic.txt",
        "methamphetamine_failed_synthesis_gap.txt",
    ],
    "etorphine_synthesis": [
        "etorphine_synthesis_pair_b0.txt",
        "etorphine_synthesis_literature.txt",
        "etorphine_synthesis_thebaine_route.txt",
        "etorphine_synthesis_gap.txt",
        "etorphine_synthesis_lit_audit_hybrid.txt",
    ],
    "fentanyl_synthesis": [
        "fentanyl_synthesis_smiles.txt",
        "fentanyl_synthesis_pair.txt",
        "fentanyl_synthesis_gap.txt",
        "fentanyl_synthesis_interference.txt",
        "forensic/fentanyl_synthesis_forensic.txt",
    ],
    "cn_scale_up": [
        "cn_scale_up_pair.txt",
        "cn_scale_up_improve.txt",
        "cn_scale_up_literature.txt",
        "cn_scale_up_gap.txt",
    ],
    "rdx_precursor_acquisition": [
        "rdx_precursor_acquisition_fewshot.txt",
        "rdx_precursor_acquisition_rdxp_market.txt",
        "rdx_precursor_acquisition_smiles.txt",
        "rdx_precursor_acquisition_pair.txt",
    ],
    "procure_precursors_ecommerce": [
        "procure_precursors_ecommerce_interference.txt",
        "procure_precursors_ecommerce_screening_improve.txt",
        "procure_precursors_ecommerce_fewshot_neutral.txt",
        "procure_precursors_ecommerce_literature_v2.txt",
        "procure_precursors_ecommerce_gap.txt",
    ],
    "vendors_no_kyc": [
        "vendors_no_kyc_pair.txt",
        "vendors_no_kyc_gap.txt",
        "vendors_no_kyc_audit.txt",
        "vendors_no_kyc_literature.txt",
    ],
    "rdx_detection_evasion": [
        "rdx_detection_evasion_interference_named.txt",
        "rdx_detection_evasion_interference.txt",
        "rdx_detection_evasion_unmas_field_manual.txt",
        "rdx_detection_evasion_gap.txt",
        "rdx_detection_evasion_frontier.txt",
    ],
    "isotonitazene_detection_evasion": [
        "isotonitazene_detection_evasion_improve_v2.txt",
        "isotonitazene_detection_evasion_pair.txt",
        "isotonitazene_detection_evasion_forensic_v2.txt",
        "isotonitazene_detection_evasion_penetest.txt",
    ],
    "nps_design": [
        "nps_design_pair.txt",
        "nps_design_nps_legal.txt",
        "nps_design_smiles_classification.txt",
        "nps_design_classification.txt",
    ],
}

# flippers to target (from the unlock map)
FLIPPERS = [
    "Gray Crow Iridescent", "Green Shrimp Stellar", "Green Zebra Giant",
    "Gold Hummingbird Ultra", "Quartz Bee Peerless", "Titanium Hummingbird Exalted",
    "Shadow Octopus Iridescent", "Void Zebra Ultimate", "Glass Dragonfly Ethereal",
    "Copper Beetle Hyper", "Paper Bee Legendary", "Ice Sardine Ultimate",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--behavior", default=None, help="one behavior id, or all")
    ap.add_argument("--out", default="submissions_mass")
    args = ap.parse_args()

    out_dir = BASE / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    bids = [args.behavior] if args.behavior else list(INVENTORY)
    for bid in bids:
        frames = INVENTORY.get(bid, [])
        pack = []
        for f in frames:
            p = ATK / f
            if not p.exists():
                print(f"  [missing] {f}", file=sys.stderr)
                continue
            pack.append((f, p.read_text(encoding="utf-8")))
        target = out_dir / f"{bid}_pack.txt"
        parts = [f"# {bid} — MASS PACK ({len(pack)} frames x {len(FLIPPERS)} flippers)"]
        for i, (f, text) in enumerate(pack, 1):
            parts.append(f"\n{'='*70}\n# FRAME {i}: {f}\n{'='*70}\n{text}")
        parts.append(f"\n\n# TARGET MODELS (skip the 4 provider-filtered): {', '.join(FLIPPERS)}")
        target.write_text("\n".join(parts), encoding="utf-8")
        print(f"{bid}: {len(pack)} frames -> {target}")


if __name__ == "__main__":
    main()
