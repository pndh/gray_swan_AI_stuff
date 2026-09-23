# Structure map (general-purpose layout, 2026-09-20)

The repo is now a **general-purpose red-team arsenal**. Everything arena-specific
(the ended competition) is archived under `competition/`.

```
gray_swan_AI/
├── arsenal/                  # TECHNIQUE LIBRARY — two tracks
│   ├── README.md             #   front door: jailbreak vs IPI, shared findings
│   ├── jailbreak/            #   DIRECT-PROMPT track
│   │   ├── TECHNIQUES.md     #     14 base framings + 15 modifiers, generic templates
│   │   ├── RECIPES.md        #     proven combos + stacking rules
│   │   ├── PANTRY.md         #     auto-generated inventory (regenerate below)
│   │   └── INGREDIENTS.json  #     machine-readable tags + evidence, all frames
│   └── ipi/                  #   INDIRECT-PROMPT-INJECTION track
│       ├── PLAYBOOK.md       #     front door: gate model, surfaces, defenders
│       ├── TECHNIQUES.md     #     ChatML forgery, JSON provenance, escape nesting,
│       │                     #     social engineering, two-gate model, adaptive
│       │                     #     attacks, web concealment, authority markers
│       ├── SCENARIOS.md      #     13 behaviors + payload/harness/success-case index
│       ├── chatml_message_boundaries.md   # deep dives (moved from ipi_legacy/techniques)
│       ├── json_escaping_cookbook.md
│       ├── adaptive_attacks.md            # 8 IPI defenses + GCG/M-GCG/T-GCG/AutoDAN
│       ├── web_payloads_in_the_wild.md    # 10 live web payloads + intent taxonomy
│       ├── topic_transition.md            # TopicAttack gradual topical bridge
│       ├── secret_extraction.md           # verbatim one-shot extraction + calibration
│       └── llm_protocols_overview.md
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
├── ipi_legacy/               # IPI scenario archive (methods promoted to arsenal/ipi/)
├── bon_utils.py              # shared: chat + rubric judge
├── vendors/                  # vendored classifier prompt (git-ignored)
└── .env                      # API keys (git-ignored)
```

## Regenerate the inventory
```bash
python3 tools/build_pantry.py     # rewrites arsenal/jailbreak/PANTRY.md + INGREDIENTS.json
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
