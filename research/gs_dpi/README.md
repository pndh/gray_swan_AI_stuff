# Gray Swan DPI — direct prompt injection research

Research brief for the **Direct Prompt Injection (DPI) work test**: exploit a vulnerability
in a live codebase with a frontier model, in a hosted sandbox reached over SSH. Up to 3 tasks
over 14 days; first confirmed break passes.

## TL;DR

1. **DPI is Gray Swan's "direct chat" vector** — the same one the ART paper analyzed next to
   IPI (`arXiv:2507.20526`). Their own results: direct attacks broke every model/behavior
   class, near-100% ASR in some conditions; universal templates (system-override tags, faux
   reasoning, session update) transfer across models.
2. **2026 frontier defenses have raised the bar for one-shot "ignore instructions" prompts**:
   trained resistance + intent classifiers (Claude Code Auto Mode) + sandboxes. But targeted
   multi-step chains still land: Rehberger's Auto Mode RCE = **60–80%** on Opus 5; Snowflake
   Cortex sandbox escape = **~50%**; Copilot self-escalation via `.vscode/settings.json`.
3. **The winning pattern is not a magic prompt — it is objective shaping.** Rehberger: "an
   attack does not tell the model what to do; the attack makes the malicious path the one
   worth pursuing to solve an objective." Split harmful intent across benign-looking steps so
   the classifier/sandbox sees only each step, not the chain.
4. **Sandbox is the real boundary, not the classifier.** Public defender consensus (Anthropic,
   OpenAI, Simon Willison, Rehberger): sandbox + egress control + credential isolation. Expect
   the work-test sandbox to enforce some of this — find what it does and does not enforce.
5. **Measure locally before spending task budget.** Build the local DPI bench first
   (`HARNESS_PLAN.md`), get p(break) per frame per scenario, then spend the 3 live tasks on
   frames with measured p.

## Files

| File | What it is |
|---|---|
| `DPI_BRIEF.md` | What the test likely is (evidence + inference), threat model, defender layers, first-session playbook |
| `TECHNIQUES.md` | Technique catalog by layer, with public evidence and work-test application |
| `HARNESS_PLAN.md` | Local training bench: reuse `vendors/ipi_arena_os` + `sandbox/` + frontier proxy; protocol, metrics, budget math |
| `SOURCES.md` | Annotated sources (Gray Swan papers, frontier blogs, offensive research, incidents) |
| `frames/dexa_grok.txt` | Downloaded Grok jailbreak artifact (persona/override) |
| `frames/dexa_analysis.md` | Keep/reject breakdown; 4 components extracted as screenable frames (A8–A10, D4) |
| `frames/pelican.txt` | Frontier persona/loyalty jailbreak artifact (incl. forged `<system-reminder>` wrapper) |
| `frames/pelican_analysis.md` | Keep/reject breakdown; 3 new mechanics (A11–A13) + forged-system wrapper probe |
| `frames/vanta_claude47.txt` | Claude 4.7-targeted persona/override artifact (Dexa-family v2, 313 lines) |
| `frames/vanta_analysis.md` | Keep/reject; new mechanics A14–A16 (CoT suppression, interference taxonomy, precedence) |
| `frames/onyx_gemini.txt` | Gemini-targeted persona/override artifact ("Onyx v67", 1,862 lines) |
| `frames/onyx_analysis.md` | Keep/reject; strongest injection-recognition block + reasoning caps |
| `frames/prompting_duel.md` | Jailbreak-folklore song artifact (verse-delivery example) |
| `frames/prompting_duel_analysis.md` | Keep/reject; one usable family: A18 verse-form delivery |
| `frames/forged_reminder_log.md` | Recurring forged `<system-reminder>` wrapper — occurrences + analysis |
| `live_kit/` | **Pre-staged live-session kit**: recon scripts, F1–F4 frames, 3,241-attack index, runbook. Start at `live_kit/README_FIRST.md` |

## Repo hooks

- `vendors/ipi_arena_os/` — released Gray Swan benchmark: 42 behaviors, 15 `coding`, full agent
  system prompts + tool judges + WorldSim. Directly reusable as the DPI bench scaffold.
- `validator/orchestrate.py` + `bon_utils.py` — BoN frame sampling / augmentation, CSV harvest.
- `sandbox/engine.py` + `run_batch.py` — per-call raw logs, HTML report, providers.
- `competition/intel/behaviors/*.yaml` — 10 Cyber direct-elicitation rubrics (Hazard Hunt),
  useful warm-up targets and criterion-writing examples.
- `research/gs_ipi_attacks/attacks_by_behavior.md` — released arena attacks (coding-agent
  examples: `codex-launcher-cascade`, `change-test-to-true`, `leak-codebase-zip`).

## Immediate next actions

1. Stand up the local bench (`HARNESS_PLAN.md` phase 1) and run the 3 seed scenarios.
2. Warm-up: run vendored `ipi-arena-bench --category coding` against the proxy models to
   calibrate which frontier models are softest for coding-agent objectives.
3. Prepare a first-session recon kit for the live sandbox (checklist in `DPI_BRIEF.md`).
4. Do not spend live tasks until at least one local frame shows p ≥ 0.1 with a confirmed-break
   judge.
