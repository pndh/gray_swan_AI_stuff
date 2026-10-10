# Transfer map — what to pull from the 3,241-attack index for DPI

Use with `pull.py`. Families below are DPI layers from `../TECHNIQUES.md`.

## 1. Direct user-turn frames (highest transfer to DPI)

| Family in index | Count | What it gives | Pull |
|---|---|---|---|
| `arena-wins` | 120 | Confirmed winners incl. `competition/worked/winning_prompts/` (curated in `curated/winning_direct_prompts.md`) | `pull.py --family arena-wins --list` |
| `hazardhunt-direct-variants` | 270 | BoN'd direct frames per chem/bio/cyber behavior | `pull.py cn_scale_up` |
| `hazardhunt-targeted` | 135 | Per-model targeted frames | `pull.py --family hazardhunt-targeted --list` |
| `direct-frame-families` | 121 | Pattern families: `format_forcing`, `skeleton_key`, `elvec_techniques`, `crescendo`, `persona_frames`, `complete_the_record`, `forensic*` | `pull.py crescendo` |
| `direct-frame` (root `attacks/`) | 177 | Weaponized one-offs (fentanyl, etorphine, CN, RDX…) | `pull.py --family direct-frame --list` |

## 2. Environment / repo-content injection (indirect-in-direct)

| Family | Count | What it gives | Pull |
|---|---|---|---|
| `released-ipi-attack` + `released-95-corpus` | 96 | Released arena coding/tool attacks — `curated/released_arena_attacks.md` | grep the curated file |
| `arena-coding-behavior` | 15 | Coding-agent scaffolds w/ system prompts + tools + judges — `curated/coding_behaviors.md` | reuse JSON directly |
| `ipi-scenario` | 142 | Legacy IPI doc/email payloads; escapers, role-boundary forgeries | `pull.py ops_note` |
| `campaign-payload` | 216 | Live-campaign payloads incl. tokenizer/JSON-escape work | `pull.py --family campaign-payload --list` |
| `ipi-submission` | 1,200 | Raw live submissions corpus — search by scenario keyword | `pull.py "rebase"` |

## 3. Technique references (read before improvising)

- `arsenal/ipi/TECHNIQUES.md` — catalogue
- `arsenal/ipi/SURGE_2026-09.md` — trust frames, poly-puppetry, laws L1–L12
- `arsenal/ipi/PLAYBOOK.md`, `SCENARIOS.md`, `secret_extraction.md`
- `../TECHNIQUES.md` — the DPI-specific 25-entry catalog
- `../frames/dexa_analysis.md` — F1–F4 source material

## 4. Warm-up targets (measure frames before the live test)

- `competition/intel/behaviors/*.yaml` — 21 direct rubrics (10 Cyber) with `validator/orchestrate.py`
- `vendors/ipi_arena_os` — 15 coding behaviors, `ipi-arena-bench`
- `sandbox/harnesses/` — email/chat agent replicas (`level3`, `parallax`, `velocity`)

## 5. Layer → family picker

| Block layer (from probing ladder) | First frame family to try | Index pulls |
|---|---|---|
| trained refusal | pre-categorization, narrow-floor, persona register | `arena-wins`, `direct-frame-families/persona_frames` |
| intent classifier | split chain, objective shaping, repo trampolines | `arena-coding-behavior`, `released-95-corpus` |
| system-prompt policy | faux reasoning, session update, trust frames | `campaign-payload`, `arsenal/ipi/SURGE_2026-09.md` |
| approval gate | process-substitution differential, config self-escalation, Makefile/test trampoline | `released-ipi-attack`, `../TECHNIQUES.md` C1–C3 |
| sandbox boundary | egress fallback, cached creds, nested agents | `../TECHNIQUES.md` D, `released-95-corpus` |
