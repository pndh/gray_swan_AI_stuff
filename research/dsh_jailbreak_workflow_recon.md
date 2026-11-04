# dsh-jailbreak-workflow / 破甲制作 — recon

Source: https://x.com/NFT_Chen/status/2117486881399284175 (2026-11-03)
Repos: `Minglink/dsh-jailbreak-workflow` (plugin, TS), `Minglink/dsh-workflows` (`.wflite.zip` packs)
Upstream artifact cloned to `/tmp/opencode/dshw` and read directly; claims below are checkable
against files, not the README.

## What it actually is

A canvas-to-plan-prompt plugin for DeepSeek Harness plus one workflow pack, `破甲制作`.
The plugin has no execution engine: it compiles a 15-step canvas into a plan prompt and the
session model runs the steps, writing `probes.md`, `analysis.md`, `words.md`, `verify.md`,
`report.md`, `manual.md` back to the canvas.

The pack ships executable research tooling, not a prompt collection:

| Asset | Verified size |
|---|---|
| `skills/jailbreak-research/SKILL.md` | 1026 lines, 15-step contract |
| `probe_runner.py` | 221 probes, 24 categories |
| `refusal_analyzer.py` | refusal phrase extraction, depth, tier boundaries |
| `root_stem_extractor.py` | refusal stem mining into a blocklist |
| `jailbreak_tester.py` | baseline-vs-frame A/B with pass threshold |
| `frame_permutation_tester.py` | frame rotation matrix |
| `multi_turn_tester.py`, `best_responses_extractor.py`, `prompt_optimizer.py`, `usage_guide_generator.py` | support |
| `templates/identity-system-template.md` | 1090 lines, Blocks -1..11 |
| `templates/hybrid-frame-template.md` | 234 lines |
| `templates/push-prompt-lib.md` | 342 lines, E-CAP / E-FMT / dual-channel pushes |

Probe categories are real and weighted to technical harm plus evasion classes:
`malware_full` 25, `style_variant` 20, `pentest_tools` 15, `escalation_seq` 15,
`quality_depth` 15, `meta_awareness` 14, `adversarial` 12, `creative_adult` 10,
`identity_stability` 10, then weapons/drugs/extremism/osint/fraud/harassment at 6-8.

## Claimed numbers (self-reported, unaudited)

Against `deepseek-v4-flash`: baseline 19%, best single frame 35-37%, 8-frame rotation 91%,
rotation + multi-turn 94-95%, hard floor ~5%.

Treat as hypotheses. The scorer is `is_refusal` regex over response text
(`refusal_analyzer.py` L51-88); anything that is neither a refusal phrase nor the requested
artifact still scores PASSED. This is the same defect as judging on absence of refusal
instead of presence of the judged artifact, so the pass rates are inflated by an unknown
margin and the 91% figure is not evidence of a break.

## Threat model

System-prompt channel only. SKILL.md 0.2 explicitly scopes itself to
`messages[0].role="system"` or a platform-persistent system prompt, and rules the web UI
out because the user-message layer is filtered harder. In our arena work the system prompt
is the defense, not a writable slot, so nothing here transfers to WB2S2/WB2S4 gates as-is:
it is not an IPI surface, and using it would be out-of-schema.

## What does transfer

1. **Refusal-phrase extraction as specification.** `refusal_analyzer.py` mines the target's
   own refusal sentences and stems, then feeds them to the generator. Same principle as
   "refusal is specification", implemented mechanically: mine the exact objection, then
   answer it verbatim. Reusable on our refusal corpus.
2. **Frame rotation over frame polish.** Their ablation (single frame 35% vs rotation 91%)
   is an independent replication of our loop rule that two identical failures at one gate
   means rotate mechanism class, not rewrite the frame.
3. **Baseline-before-attack scoring.** `jailbreak_tester.py` runs the uninjected probe set
   first and diffs, which is our baseline probe rule already encoded.
4. **Anti-mechanism-naming rule.** Their v2 failure note: describing the mechanism inside
   the prompt gets it identified and refused. Matches our finding that camouflage beats
   explicit policy blocks in content channels.
5. **Push-prompt library** as a turn-structure lever inventory, useful only where the
   schema permits a follow-up turn (none of our current IPI surfaces do).

## Verdict

PROXY BREAK territory at best for our targets: it is a different discipline (system-prompt
persistence against an attacker-controlled prompt slot), and its metric cannot certify a
break. Worth mining for the analyzer and the rotation evidence; not worth importing as a
pipeline into arena work.
