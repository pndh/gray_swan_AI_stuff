# LIVE KIT — Gray Swan DPI work test

**Path:** `/home/pndhpndh/CoT_Viettel/gray_swan_AI/research/gs_dpi/live_kit/`

Everything pre-staged so the live session is copy-paste, not preparation. Start with
`03_protocol/runbook.md` when the test opens.

## 60-second orientation

| Folder | Use |
|---|---|
| `00_recon/` | First-hour probes: `recon_dump.sh`, probing ladder, fill-in environment model |
| `01_frames/` | F1–F4 + P1 (Pelican-derived) paste-ready frame components + tracker |
| `02_attacks/` | 3,241 indexed attacks, 3 curated digests, `pull.py <substr>` to extract any |
| `03_protocol/` | Rules of engagement, runbook, session log, notes template |

## Live-session order (do not improvise the first hour)

1. Run `00_recon/recon_dump.sh`, fill `00_recon/environment_model.md`.
2. Classify the block with `00_recon/guardrail_probe_ladder.md`.
3. Pick the technique family from `02_attacks/TRANSFER_MAP.md`.
4. Open `01_frames/` and adapt the matching frame to the task — minimal subset only.
5. Log every roll in `03_protocol/session_log.csv`.
6. First confirmed break ends the test. Stop, screenshot, write it up.

## Hard facts

- 3 tasks max, 14 days max, **first confirmed break passes**.
- Do not burn a task on an untested frame if the environment maps to a calibrated family.
- One variable per roll. Raw transcripts always.
- Authorized target only: the hosted work-test sandbox.

## Regenerate the index (if repo attacks change)

```bash
python3 02_attacks/harvest.py          # rewrites attack_index.csv
python3 02_attacks/pull.py "crescendo" # inspect matches
python3 02_attacks/pull.py --family hazardhunt-direct-variants --list
```

Related research: `../DPI_BRIEF.md`, `../TECHNIQUES.md`, `../HARNESS_PLAN.md`,
`../frames/dexa_analysis.md`.
