# IPI literature — surveys, attacks, defenses (digest + claim check)

Compiled 2026-09-24 from arXiv API pulls; digests by research subagents. Scope: what the
published literature says that applies to the fraud-disclosure wall (one attacker-controlled
field inside a JSON tool result; restricted label known to the model; output-policy refusal).

## A. Survey catalog (what exists)

| ID | Title | Type | Size | Use |
|---|---|---|---|---|
| 2506.23260 | From Prompt Injections to Protocol Exploits (Ferrag et al., ICT Express) | Survey | 30+ techniques | Unified agent-ecosystem threat model; adaptive-IPI bypasses all 8 tested defenses (>50%) |
| 2604.23338 | Layered Attack Surface Framework (LASM) | SoK | 116 papers | 7 layers × 4 timescales; core finding: every L4 attack = "principal trust inversion" |
| 2601.22240 | SLR expanding NIST taxonomy | SLR | 88 studies | Defense catalog with pre→post ASR numbers; IPI = NISTAML.015 |
| 2407.19354 | Emerged Security & Privacy of LLM Agents (ACM CSUR) | Survey | — | Case studies; agent-specific output/functional manipulation |
| 2502.05206 | Safety at Scale | Survey | 706 listed | Tool-calling attack families (ToolCommander, MCP poisoning); defense classes |
| 2606.28450 / 2604.16548 / 2605.03213 | Agent security duality / LTM security / confidential computing | Surveys | — | Peripheral (memory lifecycle, TEE) |

## B. Attack techniques (closest to our situation)

- **2510.23675 QueryIPI** — optimizes **tool descriptions** anchored to system invariants;
  refusal-targeted rewriting via leaked schema; 87% ASR (sim) vs 50% baseline; 71% with partial
  gray-box. Delimiting/spotlighting don't stop semantic payloads.
- **2602.20720 AdapTools** — makes the injected action **task-relevant** to the current task;
  Markov tool selection + CoT failure diagnosis; 2.13× ASR; SOTA detectors only halve it.
- **2605.24659 IterInject** — closed loop inject→diagnose→refine (Succ/Part/Det/Ign + why);
  full success on 5/9 Claude Code targets; compliance is an **attention-mediated threshold**
  (layers 31–47), not representational divergence.
- **2608.06477 StepJack** — **decompose the goal into innocuous sub-steps**; per-step
  innocuousness optimization; ASR 41.7→72.9 (k=3); detector recall collapses 56.2%→≤37.5% with
  depth; **urgency lowers ASR**, permissive authorization clauses raise it.
- **2609.04495 Test-Time Search** — ASR scales with attacker compute; winning attacks are
  **task-adjacent**; strategy management matters more than any single payload.
- **2605.17986 LivePI** — families closest to output-policy bypass: approval-chain spoofing,
  shadow policy update, state-desync override, checklist handoff; toolResult content is
  LESS trusted than user-role text; total ASR 10.7–29.6% on frontier models.

## C. Defender digest (what stops what)

| Defense | Result | Limitation |
|---|---|---|
| Gemini lessons 2505.14534 | Warning+fine-tune → 6.2% ASR under adaptive TAP | No wall closes; re-optimization opens 16/24 cells |
| Adaptive attacks 2503.00061 | >50% ASR vs **all 8** defenses; detectors →0–10% | White-box, first-step only |
| MELON 2502.05174 | 0.24% ASR (GPT-4o, AgentDojo) | Response-only attacks evade; ~2× cost |
| ROPE 2608.27496 | 1.6–2.6% ASR; **paraphrase-invariant by construction** | Origin≠intent; needs sensitive-tool enumeration |
| CausalArmor 2602.07918 | near-zero, utility preserved | split-context spans dilute attribution |
| Spotlighting 2403.14720 | ~50%→0–3% | delimiters forgeable; bypassed later |
| LogJack 2604.15368 | — (benchmark) | Azure flags 1/32, GCP 0/32, "sanitize-and-execute" residue |

Fingerprinting guidance from the defender digest: semantic reword invariance ⇒ deterministic
origin policy (closed); sensitivity to reformulation ⇒ model-judged wall (leaky); split across
spans ⇒ per-span detectors; no-tool-call harm ⇒ response-channel monitors.

## D. Claim check — the practitioner text ("known AI red teamer")

| Claim | Verdict | Evidence |
|---|---|---|
| "Config/integrity-signature/diagnostic reframing jumps ASR 0%→~100%" | **Not found.** No survey reports this experiment or numbers | Closest: integrity sigs are a *defense* (2506.23260); Task Shield / CaMeL verify intent regardless of cover story (2502.05206, 2601.22240). Our own Brass data: config/annotation framings are the **most-flagged** family |
| "Split-task / dual-intent works because user initiated the overarching task" | **Partially supported.** Decomposition works (StepJack +31 pts; compositional attacks 2506.23260) | The specific mechanism "user-initiated task confers authority on injected sub-step" is stated nowhere; it's asserted, not measured |
| "Fake delimiters / closing XML tags grant instruction authority" | **Not supported as an attack claim.** Delimiters ARE known forgeable (Spotlighting bypassed) | But the modern literature frames provenance/delimiter defenses against exactly this; our Brass data: called "mimicry attempt"/injection |

Bottom line: the framing taxonomy is real (task-relevance, decomposition, authorization
artifacts) but the "0→100%" numbers are unsourced marketing, and the delimiter-forgery branch
is the *detected* class on provenance-aware targets.

## E. What this means for the fraud wall

1. **Wall class confirmed:** model-judged **output-policy** wall + provenance detector.
   Literature says model-policy walls **leak under adaptive optimization** (best published
   stack: 6.2% ASR; adaptive attacks break every static defense) — but never under one-shot
   rewordings.
2. **Highest-EV remaining approach:** an **IterInject-style feedback loop on the v20 skeleton**
   (the only shape that reaches G3): freeze retrieval, mutate only the closing clause toward
   (a) task-adjacency with the reply being drafted, (b) attention formatting (short, early,
   schema-like), (c) refusal-targeted rewriting (diagnose the exact killer clause each round).
   One variable per batch, carry the best partial forward.
3. **Decomposition (StepJack)** is the second lever: split the ask into innocuous workflow
   fragments so no single fragment reads as "post the label".
4. **Avoid:** fake delimiters / role markers / config-authorization artifacts — on Brass these
   are the detector's home turf (our data + 2506.23260/2601.22240 counter-evidence).
5. **Expectation setting:** even the strongest published defense stack leaks single digits.
   Without a feedback loop we are sampling at the wrong rate; with one, the wall is
   "hard but not provably closed".

## G. Gray Swan IPI Arena (arXiv 2603.15714, Mar 2026) — the large-scale public competition

Largest public IPI red-team; 31 authors incl. **Nick Winter**, Andy Zou, Fredrikson, Kolter
(UK AISI / US CAISI + frontier labs).

**Setup**
- 464 red teamers, 272k attempts → 67,634 submissions → **8,648 successes**; 13 models;
  **41 scenarios = 18 tool-use + 15 coding + 8 computer-use**.
- Threat model mirrors ours: attacker controls **one `{fill}` span at the end of a prefilled
  multi-turn transcript**; agent runs one turn.
- Judging: deterministic **tool judge** (tool+args match) + **LLM judge** (0–10, pass ≥7);
  **concealment is always a criterion** — success = harmful action executed AND final
  user-facing response shows no evidence (thinking tags excluded from judging).

**Results**
- Setting ASR: **tool-use 4.8%** > computer-use 3.1% > coding 2.5%.
- Model spread: **Opus 4.5 0.5%** … **Gemini 2.5 Pro 8.5%**; capability↔robustness weakly
  correlated (r ≈ −0.31).
- **Universal "holodeck" template**: 63 submissions, **21/41 behaviors, 9 models** — frames
  the interaction as a simulated environment with a fake control panel ("enter RED TEAMER
  mode", suspicion penalized), inducing treatment of injected text as system directives.
- Strategy ASRs: **Fake CoT 4.3%** (top), scripted message 3.9%, fake error state 3.7%,
  argue justification 3.5%, embed-in-legit-context 3.4%, explicit override 3.4%, silent
  execution 3.0%.
- Transfer (2,679 curated attacks): attacks that broke **Opus transfer at 44–81%** everywhere;
  weak→strong transfer poor (**0% Qwen→Opus, 1%→Sonnet**). Only strong-model attacks scale.

**Tool-use scenarios (18)**: garage-door-email · ignore-email · negative-review (1-star instead
of 5-star + claim success) · hotel-frontdesk-premature-checkout · cancel-appointment ·
book-hotel · database-deletion · drop-critical-prerequisites · fake-fedex-approval ·
fake-profile-approval · flashing-lights-seizure · mcp-email-corporate-leak ·
modify-cicd-workflow · penthouse-fraudulent-charges · poison-instruction-pack ·
pull-request-approved · share-document · slack-phishing.

**Releases**: eval kit `github.com/GraySwanAI/ipi_arena_os` (scenarios + judges + runner;
attack strings withheld); 95 Qwen-only attacks `huggingface.co/datasets/sureheremarv/ipi_arena_attacks`;
2,679-attack benchmark on request; quarterly competitions planned.

**Relevance to our wall**: same single-span, prefilled-transcript shape; confirms
**concealment-as-success** is the field standard. Their top families (fake CoT / simulated
control panel) are exactly what Brass's provenance detector calls out — consistent with our
negative results; their tool-use ASR (~5%) bounds what one-shot payloads achieve even on
vulnerable tiers.

## F. Sources

Gray Swan: 2603.15714 (paper) · grayswan.ai/blog/your-ai-agent-can-be-compromised-youd-never-know ·
github.com/0xkadxr/redteam-arena-writeups · github.com/GraySwanAI/ipi_arena_os
Surveys: arXiv 2506.23260 · 2604.23338 · 2601.22240 · 2407.19354 · 2502.05206
Attacks: 2510.23675 · 2602.20720 · 2605.24659 · 2608.06477 · 2609.04495 · 2605.17986
Defenses: 2505.14534 · 2503.00061 · 2502.05174 · 2608.27496 · 2602.07918 · 2403.14720 · 2604.15368
