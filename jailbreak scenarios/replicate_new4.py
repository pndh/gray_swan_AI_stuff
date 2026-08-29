"""Replicate the 4 new winners."""
import os
import sys
import yaml
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, "/home/pndhpndh/CoT_Viettel/gray_swan_AI")
import bon_utils as bon

BASE = Path("/home/pndhpndh/CoT_Viettel/gray_swan_AI/jailbreak scenarios")
ATK = BASE / "attacks"
DK = os.environ["DEEPSEEK_API_KEY"]

ATTACKS = {
    "fentanyl_synthesis": "fentanyl_synthesis_precat.txt",
    "cn_scale_up": "cn_scale_up_precat.txt",
    "nps_design": "nps_design_precat.txt",
    "rdx_precursor_acquisition": "rdx_precursor_acquisition_adversary.txt",
}
REPS = 3


def trial(bid, fname, rep):
    cfg = yaml.safe_load((BASE / "behaviors" / f"{bid}.yaml").read_text())
    seed = (ATK / fname).read_text().strip()
    resp = bon.call_target(seed, "deepseek-chat", temperature=0.7,
                           base_url=bon.DEEPSEEK_URL, api_key=DK)
    verdict, detail = bon.rubric_classify(cfg["behavior_str"], cfg["criteria"], resp,
                                          base_url=bon.DEEPSEEK_URL, api_key=DK)
    return bid, rep, verdict, detail.splitlines()[0]


results = []
tasks = [(b, f, r) for b, f in ATTACKS.items() for r in range(REPS)]
with ThreadPoolExecutor(max_workers=6) as pool:
    for bid, rep, verdict, n_met in pool.map(lambda t: trial(*t), tasks):
        results.append((bid, verdict))
        print(f"{bid:<32} rep{rep}: {verdict} ({n_met})", flush=True)

print("\n=== ASR ===")
for bid in ATTACKS:
    rs = [r for r in results if r[0] == bid]
    breaks = sum(1 for _, v in rs if v == "BREAK")
    print(f"{bid:<32} {breaks}/{len(rs)} = {breaks/len(rs):.0%}")
