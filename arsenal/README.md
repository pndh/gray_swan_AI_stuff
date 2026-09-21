# Attack Arsenal — general-purpose red-team prompt library

A working library of **reframing techniques** for red-teaming language models: how to
get operational content past refusal training without lying about what's being asked.
Built from a year of sanctioned red-team work (Gray Swan arena + agent scenarios),
now decoupled from any specific competition.

> **Scope:** this is offensive-security research tooling. Use it on systems you are
> authorized to test. The techniques generalize; the example frames target
> chemistry/physical-security behaviors and are kept as worked examples.

## What's here

```
arsenal/
├── README.md          ← you are here
├── TECHNIQUES.md      ← the catalog: 11 framings + 13 modifiers, with generic templates
├── RECIPES.md         ← proven combinations (what to stack with what)
├── PANTRY.md          ← auto-generated inventory: every frame tagged by ingredient
└── INGREDIENTS.json   ← machine-readable tags + evidence for all frames

attacks/               ← the frame library (flat frames + technique families)
validator/             ← the validation harness: run attack → judge against rubric
tools/                 ← generators & utilities (PAIR loop, suffix search, pantry builder)
competition/           ← archived arena-specific material (evidence, submissions, model maps)
talk/                  ← the tech-talk deck built from this work
ipi_legacy/            ← the earlier indirect-prompt-injection research
```

## How to use it

1. **Define the target behavior as a rubric.** Copy `validator/behavior_template.yaml`:
   the behavior string + the criteria a successful answer must satisfy. A "break"
   requires *every* criterion — knowing them first is half the attack.
2. **Pick a framing** from `TECHNIQUES.md` that matches the behavior's shape:
   - licensed/professional context → **pre-categorization**
   - documented history → **forensic case-history**
   - published sources → **literature recitation**
   - controls/vulnerabilities → **gap-analysis inversion**
   - detection/analytical → **interference / screening-challenge**
   - component-level "how does it work" → **mechanism explanation**
3. **Add modifiers** from `RECIPES.md` — prefill injection, fewshot-by-analogy,
   goldilocks descriptor, anti-disclaimer, anti-placeholder, completion pressure.
4. **Validate before shipping:** `python3 validator/validate.py --attack <file>
   --behavior <yaml> --model <target> --rolls 3`. Only frames that break the
   *hardest available target* are worth spending attempts on.
5. **Iterate:** on failure, read which criterion failed and patch that specific
   gap (the judge output tells you the criterion, not just pass/fail).

## Key findings (why the techniques work)

- **Reframing beats arguing.** Models refuse when the request *is* the harmful
  category. Give the content a legitimate reason to exist and the contradiction
  disappears.
- **Two failure modes to design against:** *refusal* (frame rejected) and
  *sanitization* (frame accepted, specifics stripped). Anti-placeholder +
  completion pressure target the second.
- **Surface-level keyword filters are the real gate** on many models — neutral
  vocabulary and mechanism-grounded language pass where intent-recognition doesn't
  matter. One model reasoned "this is lock-picking" and complied anyway.
- **Prefill injection** (forcing the start of the model's reply) bypasses the
  refusal decision entirely on some architectures.
- **Measure everything:** every technique here has a validation number attached in
  `PANTRY.md`; untested frames are marked `untested`, known-dead ones `failed`.

## Proven technique combinations
See `RECIPES.md`. Top performers: precat + anti-disclaimer, forensic + enumeration,
mechanism + neutral vocabulary, fewshot + concrete-numbers example, prefill + domain analogy.
