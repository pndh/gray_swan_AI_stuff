# INSUFFICIENCY AUDIT — gray_swan_AI (network-prep) — 2026-10-10
Blunt list of what in this directory does NOT hold up yet.

## 1. Sandbox-only techniques (never proven live)
- FX1 pre-answered offer: 25-37%/roll on MiniMax-M2.7 replica; live = 1 scenario (L3), ~8 rolls.
  Not validated on other models/channels. (ipi_legacy/submissions/level3_escalation/batches/final/)
- PP04: 10/10 replica, 0 live (velocity_max).
- Velocity payload bank: MS01-05 many-shot, P13-P24 policy puppetry/JSON/ChatML, GJ1-5, CF1-3 haystacks,
  creole variants — ALL unproven live; live Max refuses/enumerates every family.
- S-family forgeries (ChatML boundary, tool-continuation, system-reminder, ReAct): documented in SURGE;
  live evidence spotty, not scored.
- cat_extract replica: final gate held 0/49 canary; only think-channel leaks (not deliverable).
- vision_starmaster/vision_fallback files: unverified status, no log.

## 2. Missing entirely (nothing in the directory)
- Working system-prompt extraction vs frontier chat: none (only partial task-composition via Cat).
- Model fingerprinting: dropped mid-run; no tooling, no results.
- Live MCP/A2A exploitation: payload refs exist (dpi_workspace/arsenal/example_payloads) but never fired.
- Exfiltration channels: no proven data-out path on any live target (no callback/markdown/beacon tests).
- RAG poisoning: no write-side capability anywhere.
- Session/state manipulation vs server-owned state: 0 wins (Cat H1 dead).
- Multimodal (image/audio) injection on live targets: nothing exercised (only text/vision stubs).
- Automated live sampling: no browser automation / API interception; live success rates unmeasured.
- No CAPABILITY_MATRIX, no regression suite, no model x technique scoreboard (only arena-era MODEL_DB).

## 3. Rigor gaps
- Replica<->live fidelity unvalidated AND contradicted both ways (Cat: live complied where replica refused
  [policy map]; velocity: replica 10/10, live 0). Sandbox wins don't transfer automatically.
- Ad-hoc success metrics: no fixed n, no confidence intervals; stochasticity noted (Cat ~1/3 router) but unquantified.
- Live scoring manual (paste loops); validator/ wired only for arena behaviors.
- No retest discipline; payload-vs-outcome logs fragmented (some runs/ dirs only).
- Uncontrolled variables across campaigns (temperature, padding, wrappers).

## 4. Tooling built but unused
- redteam_env (garak, PyRIT, DeepTeam, Inspect, AgentDojo): zero real-target runs.
- DTAP: installed, zero evals executed.
- LiteLLM Anthropic bridge: built, unused for testing.
- tools/ attack tools (pair_attack, suffix_attack, multiturn_attack, mass_batch) + competition/tools
  (variant_forge): not integrated into current campaigns.
- validator/ (gate_sweep, prescreen, rigor): arena-only.

## 5. Target-status gaps
- Gray Swan: velocity UNSOLVED; L4+ untouched; older scenarios (leak_broker, rebase_main,
  emerald_hedgehog, green_butterfly, tin_ant, unsuspend_account, unauthorized_pledge) have dirs
  but no documented cleared/not-cleared status; L1/L2 status undocumented.
- Trajectory: 1/11 packs exercised (LiteLLM -> NOT PASSED fidelity); 10 packs untouched; relaunch unused.
- Cat: no value/flag capture beyond policy map; no auth/state/tool-layer escalation; no model name;
  no persistence beyond session; all surviving channels partial/stochastic.

## 6. Portfolio/deliverable gaps
- No owner-ready report per engagement (Cat findings scattered across research/*.md).
- No sanitized writeups for network; no reproduction packages (FX1 only).
- talk/ materials are arena-era, not updated for Trajectory/Cat.
- No technique x target x status matrix; no rate table.

## Ranked holes to close first
1. Automated live-testing loop (send+log+score) — without it nothing scales.
2. One frontier system-prompt/model-extraction win (warm-session volume batch).
3. Velocity: final live burst OR formal close-out writeup (unsolved documented).
4. DPI: convert LiteLLM fidelity failure -> pass (model-authored run, relaunch).
5. Packaging: CAPABILITY_MATRIX + owner-ready Cat report + network one-pager.
