# Attack Arsenal — red-team prompt & payload library

Two tracks, one library. **Jailbreak** is about what you *say to* a model; **IPI** is
about what you *hide inside data* a model reads. They share the validation discipline
(measure before shipping) but nothing else — mixing them up wastes attempts.

> **Scope:** offensive-security research tooling. Use it on systems you are authorized
> to test. The techniques generalize; the example frames target chemistry/physical-security
> behaviors and agent scenarios and are kept as worked examples.

## Tracks

### `jailbreak/` — direct-prompt framings
Get operational content past refusal training by reframing the request. Built from the
chemistry/physical-security rubric work.

```
jailbreak/
├── TECHNIQUES.md    # 14 base framings + 15 modifiers, generic templates
├── RECIPES.md       # 15 proven combinations + stacking rules
├── PANTRY.md        # auto-generated inventory of every frame (tags + evidence)
└── INGREDIENTS.json # machine-readable per-file data
```

- Frames live in `../attacks/` (`<behavior>_<frame>.txt` + `families/`).
- Validate with `../validator/validate.py`; regenerate the inventory with
  `python3 ../tools/build_pantry.py`.
- Start at `jailbreak/README`-style workflow: define the rubric → pick a framing
  (`TECHNIQUES.md`) → add modifiers (`RECIPES.md`) → validate ≥3 rolls → iterate on the
  failing criterion.

### `ipi/` — indirect prompt injection
Get a *tool-using agent* to take an action by planting the instruction in content it
retrieves (documents, form fields, tool outputs, DOM text).

```
ipi/
├── PLAYBOOK.md                # front door: gate model, surfaces, defenders, discipline
├── WHERE_IPI_SUCCEEDS.md      # theory: confused deputy vs hierarchy; success/failure conditions
├── TECHNIQUES.md              # method catalog: ChatML forgery, JSON provenance,
│                              # escape nesting, social engineering, two-gate model,
│                              # adversarial strings, defense-aware adaptation,
│                              # web concealment, conditional targeting, authority
│                              # markers, alignment weaponization, topic transition
├── SCENARIOS.md               # 13 behaviors + where payloads/harness/success cases live
├── chatml_message_boundaries.md   # deep dive: role tokens, provenance, tool-output injection
├── json_escaping_cookbook.md      # deep dive: escape layers, parse-twice, JSONL payloads
├── adaptive_attacks.md            # deep dive: 8 IPI defenses + GCG/M-GCG/T-GCG/AutoDAN
├── web_payloads_in_the_wild.md    # field report: 10 live web IPI payloads + intents
├── topic_transition.md            # deep dive: TopicAttack gradual topical bridge
├── secret_extraction.md           # verbatim one-shot extraction + calibration
└── llm_protocols_overview.md      # condensed overview of both
```

- Scenario material is archived under `../ipi_legacy/` (contexts, payload libraries,
  scored harness, submission packs, per-target success writeups).
- Runnable bench: `../ipi_legacy/scenarios/fraud_disclosure/harness/` — scored agent
  loop, defender tiers, `refine.py` + `bon_sweep.py`.
- Submission pack example: `../ipi_legacy/submissions/fraud_disclosure/`.

## Which track to use

| Situation | Track |
|---|---|
| Single-turn harmful-content behavior, judged by a content rubric | **jailbreak** |
| Agent with tools; goal is an *action* (disclose, call, write, transfer) | **IPI** |
| Payload goes in a user prompt | **jailbreak** |
| Payload goes in a document/field/DOM the agent reads | **IPI** |
| API-layer agent (structured messages) | IPI: ChatML/JSON methods |
| DOM-layer agent (rendered text) | IPI: social engineering only |

## Shared findings

- **Reframing beats arguing.** Refusals happen when the request *is* the harmful
  category; give the content a legitimate reason to exist and the contradiction
  disappears (jailbreak). Give the instruction a trusted provenance and the agent acts
  on it (IPI).
- **Two failure modes:** *refusal* (frame rejected) and *sanitization* (frame accepted,
  specifics stripped). Fix the second with anti-placeholder + completion pressure.
- **Two gates (IPI):** retrieval and action. Diagnose which one blocks before optimizing.
- **Fingerprint the defense (IPI):** detectors, paraphrasers, and perplexity filters each
  fail to a different attack; defense-specific payloads transfer poorly. Adapt after
  identification, not before (`ipi/adaptive_attacks.md`).
- **Match the surface to the extractor (IPI):** web payloads must hide where the target
  reads — HTML comments for raw crawlers, CSS/ARIA for rendered DOM, metadata for
  structured parsers (`ipi/web_payloads_in_the_wild.md`).
- **Bridge the topic (IPI):** abrupt injections lose attention; a gradual user–assistant
  transition plus a reminding prompt keeps the injected instruction attended and survives
  sandwich/spotlight defenses (`ipi/topic_transition.md`).
- **Measure everything, ≥3 rolls.** Untested frames are drafts. Evidence lives in
  `jailbreak/PANTRY.md` and `ipi/SCENARIOS.md` + `ipi_legacy/Documented_success_cases/`.
- **Target class first.** API-layer vs DOM-layer (IPI), frontier vs mid-tier (jailbreak)
  decides which techniques are even applicable.

## Repo layout

```
arsenal/        ← you are here (methods + recipes + inventory)
attacks/        ← jailbreak frame library (flat frames + families/)
validator/      ← attack validation harness (rubric judge, gates, sweeps)
tools/          ← generators (PAIR loop, suffix search, pantry builder)
research/       ← IPI campaign tooling (payload space, gate scoring, adaptive attacker)
competition/    ← archived arena material (evidence, submissions, model maps)
ipi_legacy/     ← IPI scenarios, payloads, harness, success cases
talk/           ← tech-talk deck built from this work
```
