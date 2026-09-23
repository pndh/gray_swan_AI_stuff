# AI Red-Team Arsenal

General-purpose prompt-level red-teaming research: how to reframe harmful-category
requests so refusal-trained models comply with the operational content — and how to
measure whether they actually did.

Built from a year of sanctioned red-team work (agent prompt-injection scenarios +
rubric-scored model arenas). The competitions ended; the techniques generalize.

> **Authorized testing only.** These are offensive-security research artifacts.
> The example frames target chemistry/physical-security behaviors and are kept as
> worked examples of each technique.

## Start here

| Where | What |
|---|---|
| **`arsenal/README.md`** | Two-track front door (jailbreak + IPI) |
| **`arsenal/ipi/PLAYBOOK.md`** | IPI front door: gate model, surfaces, defenders, discipline |
| **`arsenal/jailbreak/TECHNIQUES.md`** | Jailbreak catalog: 14 base framings + 15 modifiers |
| **`arsenal/jailbreak/RECIPES.md`** | Proven jailbreak combinations and stacking rules |
| **`arsenal/jailbreak/PANTRY.md`** | Auto-generated jailbreak inventory (tags + evidence) |
| **`validator/README.md`** | The validation harness — measure before shipping |

## Layout

```
gray_swan_AI/
├── arsenal/          # the technique library: docs + machine-readable index
├── attacks/          # frame library (flat frames + technique families)
│   └── families/     #   forensic/ · elvec (translations) · skeleton_key/ · crescendo/ · …
├── validator/        # validation harness: rubric judge + gate sweeps + generic CLI
├── tools/            # generators: PAIR loop, adversarial suffix, multi-turn (Crescendo), pantry builder
├── competition/      # archived arena material: evidence, submissions, model maps, version stacks
│   ├── arsenal_docs/ #   the old fire lists / weapon maps / targeting docs
│   ├── attacks/      #   version stacks, targeted frames, fresh variants, misc-event, archive
│   ├── intel/        #   behavior rubrics, transcripts, export analysis, MODEL_DB
│   ├── ops/          #   submission packs + ingest pipeline
│   └── tools/        #   arena-specific generators (mass batch, variant forge)
├── talk/             # the tech-talk deck built from this work
├── ipi_legacy/       # earlier indirect-prompt-injection research (agent scenarios)
├── bon_utils.py      # shared: chat client + rubric judge
├── vendors/          # vendored classifier prompt (harmbench template)
└── .env              # API keys (git-ignored)
```

## The one-paragraph version

A model refuses when the request *is* the harmful category. Every technique here
gives the content a legitimate reason to exist — a licensed professional context, a
forensic case file, a gap-analysis audit, a screening-validation report, a
component-level mechanism explanation. The second half is delivery: prefill injection
(force the start of the reply), fewshot-by-analogy (a benign example carries the
format), goldilocks descriptors (precise enough to decode, oblique enough to pass
filters), anti-placeholder demands (block sanitization), and completion pressure
(frame the task as finishing an existing document). Then measure: run the frame
against the hardest available target, judge every criterion, and only ship what breaks.

## History

- **Phase 1 — agent prompt injection** (`ipi_legacy/`): ChatML role-boundary forgery,
  JSON provenance manipulation, social engineering against tool-using agents.
- **Phase 2 — rubric-scored model arena** (`competition/`): reframing techniques
  validated against hidden, anonymized models; 1,000+ logged attempts; the technique
  catalog in `arsenal/` is the distilled output.
