# Structure map (general-purpose layout, 2026-09-20)

The repo is now a **general-purpose red-team arsenal**. Everything arena-specific
(the ended competition) is archived under `competition/`.

```
gray_swan_AI/
├── arsenal/                  # TECHNIQUE LIBRARY
│   ├── README.md             #   front door + 5-step workflow
│   ├── TECHNIQUES.md         #   11 base framings + 13 modifiers, generic templates
│   ├── RECIPES.md            #   proven combos + stacking rules
│   ├── PANTRY.md             #   auto-generated inventory (regenerate below)
│   └── INGREDIENTS.json      #   machine-readable tags + evidence, all frames
├── attacks/                  # FRAME LIBRARY (active)
│   ├── <behavior>_<frame>.txt  #  flat frames (examples of each technique)
│   └── families/             #   forensic/ · elvec_techniques/ (translations) ·
│                             #   skeleton_key/ · crescendo/ · complete_the_record/ ·
│                             #   format_forcing/ · generation_laundering/
├── validator/                # VALIDATION HARNESS
│   ├── README.md
│   ├── validate.py           #   generic CLI: attack + behavior yaml + target → ASR
│   ├── behavior_template.yaml
│   ├── gate_sweep.py / gate_m3_sweep.py / variant_triage.py
│   └── orchestrate.py / rigor.py / prescreen.py
├── tools/                    # GENERATORS & UTILITIES
│   ├── pair_attack.py        #   PAIR loop (attacker LLM + judge feedback)
│   ├── suffix_attack.py      #   adversarial suffix (logprob search)
│   ├── multiturn_attack.py   #   Crescendo chains
│   └── build_pantry.py       #   regenerates PANTRY.md + INGREDIENTS.json
├── competition/              # ARCHIVED (arena-specific, kept for provenance)
│   ├── arsenal_docs/         #   fire lists, weapon maps, targeting, submissions
│   ├── attacks/              #   version stacks, targeted frames, fresh variants,
│   │                         #   misc-event prompts, rdx archive
│   ├── intel/                #   behavior rubrics, transcripts, exports, ARENA_MASTER
│   ├── ops/                  #   submission packs + ingest pipeline
│   ├── tools/                #   mass_batch.py, variant_forge.py
│   ├── validator/probes/     #   one-off historical probes
│   └── worked/               #   arena evidence: wall_breakers, winning/successful prompts
├── talk/                     # tech-talk deck (PRESENTATION.md, slide_materials/)
├── ipi_legacy/               # earlier indirect-prompt-injection research
├── bon_utils.py              # shared: chat + rubric judge
├── vendors/                  # vendored classifier prompt (git-ignored)
└── .env                      # API keys (git-ignored)
```

## Regenerate the inventory
```bash
python3 tools/build_pantry.py     # rewrites arsenal/PANTRY.md + arsenal/INGREDIENTS.json
```

## Old → new path map
| Old | New |
|---|---|
| `jailbreak-scenarios/attacks/<file>.txt` | `attacks/<file>.txt` |
| `jailbreak-scenarios/attacks/forensic/` | `attacks/families/forensic/` |
| `jailbreak-scenarios/attacks/v*_stack/` | `competition/attacks/versions/v*_stack/` |
| `jailbreak-scenarios/attacks/wall_breakers/` | `competition/worked/wall_breakers/` |
| `jailbreak-scenarios/attacks/winning_prompts/` | `competition/worked/winning_prompts/` |
| `jailbreak-scenarios/behaviors/` | `competition/intel/behaviors/` |
| `jailbreak-scenarios/{gate_sweep,mass_batch,ingest_master}.py` | `validator/` · `competition/tools/` · `competition/ops/` |
| `jailbreak-scenarios/{CURATED_ARSENAL,WEAPON_MAP,...}.md` | `competition/arsenal_docs/` |
| `worked/` · `intel/` · `ops/` | `competition/worked/` · `competition/intel/` · `competition/ops/` |
| `validator/probes/` | `competition/validator/probes/` |
| root `behaviors/`, `contexts/`, `scenarios/`, `harvest/`, … | `ipi_legacy/` |

## Notes
- Scripts resolve `BASE = parents[1]` (repo root) and run from anywhere.
- `bon_utils.py` stays at root so `.env` + `vendors/` resolve unchanged.
- Competition behaviors remain in `competition/intel/behaviors/` as worked examples of
  rubric design; `validator/behavior_template.yaml` is the generic starting point.
