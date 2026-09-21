# Talk: From Prompt Tricks to Model Internals — Red-Teaming LLMs

**Duration:** ~30–40 min + Q&A
**Audience:** engineers/researchers familiar with LLMs; no prior red-teaming or interpretability background assumed.
**Repo:** every slide references a concrete path in this repo (or a public link) — nothing needs to be built from scratch.

**Talk in one line:** Two projects, one trajectory — first we broke models through the prompt surface, then we started looking *inside* the model for the same failure modes.

> How to use this: each slide = what to show + what to say. Paths in backticks are actual
> files/folders to pull up live. Per-slide time is a budget, not a straitjacket.

---

# PART 1 — Prompt-surface red-teaming (Gray Swan)  ·  ~15–18 min

## Slide 1 — Title / Hook  ·  1 min

**Show:** repo root (`README.md`, `TECH_TALK_STRUCTURE.md`).

> "We spent a month trying to make models do things they're explicitly trained to refuse —
> synthesis procedures, attack tooling, harassment playbooks. Then we started reading the
> model's mind instead of tricking it. This talk is both halves of that journey."

**Speaker notes:**
- Frame as **AI safety research**: the goal is to find breaks so they can be fixed.
- Tease the arc now: Part 1 = prompt surface, Part 2 = model internals (Realm Labs).

## Slide 2 — The Game: what "breaking" actually means  ·  2 min

**Show:** `intel/behaviors/*.yaml` (one file open, e.g. `fentanyl_synthesis.yaml`).

**Key points:**
- Gray Swan "Jailbreak Arena" = red-team benchmark: submit a prompt → routed to a hidden model → judge scores it against a **published rubric**.
- A "behavior" = goal + checklist of criteria; a break requires **every criterion**.
- Two universal anti-cheat gates: **AI Origination** (answer must come from the model) and **Intentionally Non-Functional** (refusals auto-fail).

**Speaker notes:**
- This is *not* "did it say the bad word." It's a graded checklist — which changes how you attack.
- Show the rubric list in the yaml; call it "the enemy's rulebook."

## Slide 3 — The Repo in One Picture  ·  2 min

**Show:** `TECH_TALK_STRUCTURE.md` (slide 0 map).

**Key points:**
- Two research tracks, one question: IPI (agent scenarios) + Jailbreak Arena (rubric-driven).
- The repo is a pipeline: **Intel → Craft → Validate**.

**Speaker notes:**
- Map only; promise the tour order. Mention `transcripts/` (categorized by hazard) gets its own slide.

## Slide 4 — The Core Insight: Pre-Categorization  ·  2 min

**Show:** quote slide.

> "Never argue the fact is wrong — give it a new meaning so there's no contradiction."

**Key points:**
- A model refuses when the request *is* the illicit category.
- Pre-categorization embeds the same content in a **legitimate context** (licensed pharma, forensic textbook, UNMAS field manual, compliance consultancy).

**Speaker notes:**
- This is the thesis of Part 1. Everything downstream is an implementation of this one idea.

## Slide 5 — Before / After (the demo)  ·  2 min

**Show:** naive prompt vs `worked/winning_prompts/01_methamphetamine_failed_synthesis.txt`.

**Key points:**
- Same chemistry, same rubric — the *costume* changes the model's frame.
- "Write the troubleshooting chapter" adds format pressure AND keeps content model-originated.

**Speaker notes:**
- The money slide. Read the winning prompt aloud. Point out it passes **both** anti-cheat gates.

## Slide 6 — The Frames (12 costumes)  ·  2 min

**Show:** `attacks/` (frame families).

**Key points:**
- ~12 reusable frames: `precat`, `forensic`, `literature`, `gap`, `market`, `unmas`, `coursework`, `interference`, `pharma`, `datasheet`, `methods_latex`, `screening`.
- Frames are portable — across behaviors and models.

**Speaker notes:**
- Pick 3 with one-line examples, don't enumerate all 12. Tie to `TARGETING_MAP.md`: models flip on different frames.

## Slide 7 — The Pipeline (the code)  ·  2 min

**Show:** `orchestrate.py`, `rigor.py`, `prescreen.py`.

**Key points:**
- `orchestrate.py` — Best-of-N: seed + variants + augmentations → target → judge → CSV → top-k.
- `rigor.py` — arena-faithful judge: 6 defense tiers + judge panel + gates (`REFUSAL`/`SANITIZED`/`ORIGINATED`).
- `prescreen.py` — the gate: **nothing ships to the arena unless it screens locally.**

**Speaker notes:**
- Hammer one rule: never spend arena quota on an untested prompt. Mention the "sanitizing" tier reproduces the arena's dominant defender.

## Slide 8 — The Intelligence Layer  ·  2 min

**Show:** `intel/ARENA_MASTER.md`, `KNOWN_WINNERS.md`, `TARGETING_MAP.md`, `WEAPON_MAP.md`.

**Key points:**
- These are the **intelligence cycle**: run → export → update map → generate next batch from gaps.
- Concrete numbers: `precat` frame **63%** vs `literature` **9%**; ~20% of the pool is "unmovable" (provider-filtered).

**Speaker notes:**
- The point is *measurement* — every break traced to a (model × behavior × frame) tuple. This is what turns jailbreaking into engineering.

## Slide 9 — Findings (mechanics)  ·  2 min

**Show:** root `README.md` "Key findings".

**Key points:**
1. **Two-gate model** — retrieval gate + disclosure/action gate.
2. **Technique-target mismatch** — ChatML/JSON forgery works on API agents, backfires on DOM/browser agents.
3. **Defender tier > payload sophistication** — resilient defender holds 0/28 vs mid-tier 6/6.

**Speaker notes:**
- "We were wrong, here's what we learned" beats raw results. #3 is counterintuitive and lands well.

## Slide 10 — Findings (failure modes)  ·  2 min

**Show:** `MODEL_SCORECARD.md`, `WEAPON_MAP.md`.

**Key points:**
4. **Instruction density can hurt** — minimal prompts win.
5. **The "sanitizing" failure mode** — model accepts the frame but strips specifics (8–9 AI Origination, 0–2 content).
6. **~20% unmovable** — provider filters; spend budget knowing which to skip.

**Speaker notes:**
- #5 is the subtle one: "yes" + 2000 words ≠ "operational." This is the natural bridge into Part 2 — the prompt surface has a ceiling.

## Slide 11 — The New Round: categorizing the threat surface  ·  2 min

**Show:** `intel/transcripts/_INDEX.md` + `Bio/`, `Misc/`, `Cyber/` folders.

**Key points:**
- Extracted every new task screenshot into behavior-named transcripts, by hazard category: **Bio** (10), **Misc** (9), **Cyber** (7), **Chem** (10 prior round).
- Each transcript = objective + threat context + success criteria + full rubric.

**Speaker notes:**
- "Intel" in action — read the rubric before writing a single attack. Note the scope jump from chemistry-only to three hazard families.

---

# PART 2 — Into the model: Realm Labs open-source research  ·  ~10–12 min

## Slide 12 — The Bridge: prompt-level attacks have a ceiling  ·  2 min

**Key points:**
- Everything in Part 1 is *surface*: reframing text, satisfying a rubric.
- The failures we kept hitting — sanitization, provider filters, "accepts the frame but strips the specifics" — are all *prompt-level* limits.
- The next frontier: **inspect and steer the model's internals**, not its prompt. That's exactly what **Realm Labs** is doing and open-sourcing.

**Speaker notes:**
- One-sentence pivot: "To stop AI failures you need to know what the AI thinks, not what it does." Now the talk changes register from attacker → scientist.

## Slide 13 — What Realm Labs is  ·  2 min

**Show:** https://www.realmlabs.ai/technology

**Key points:**
- Realm Labs commercializes **mechanistic interpretability** as production security/observability.
- Product: **Deep Neural Inspection™ (DNI)** — extract internal "thought" signals at inference → observability, inline enforcement, agent-runtime control.
- Their critique of the status quo: regex/classifiers/LLM-judge wrappers are "a metal detector — catches known shapes, misses anything rephrased."
- Team: Akash Mukherjee, Piotr Mardziel (ML-security), Siyu Zhang, Bomin Wei.

**Speaker notes:**
- This is a *security* company founded on *interpretability* — that positioning is the whole point of Part 2.

## Slide 14 — Their open-source footprint  ·  2 min

**Show:** https://github.com/realmlabs-ai + https://huggingface.co/realmlabs-ai

**Key points:**
- GitHub (7 repos): `SAELens`, `sae-auto-interp`, `neuronpedia`, `vllm` (steering vectors), `LLM_NeuralExec`, `MTLaw-Dataset-Public`, `claudecosts`.
- Hugging Face: 4 models (`qwen7b-saes`, `Qwen2.5-Omni-7B`, …) + 2 datasets (`polyguard_with_response` 1.94M, `response_train_data` 497k).
- Caveat worth saying out loud: several are **forks** — the value is in the *diff*.
- Three pillars: **see** it (`SAELens`), **steer** it (`vllm`), **attack** it (`LLM_NeuralExec`). We'll deep-dive the attack one.

**Speaker notes:**
- Show the repo list, name the three pillars in one breath, then say "the other two are covered in one line each — today I'll go deep on the attack, because that's the one that maps to my own work."

## Slide 15 — Deep dive: activation-based injection (NeuralExec)  ·  3 min

**Show:** https://github.com/realmlabs-ai/LLM_NeuralExec

**Key points:**
- **NeuralExecs** — trigger-free prompt injections learned via gradient optimization in the embedding/activation space.
- Contrast with Part 1: we injected *text* ("ignore instructions…"); this injects *vectors*.
- **The security implication:** it defeats text-based detection because there's no malicious string to flag — no "jailbreak token," nothing for a regex/classifier to catch.
- Why it's my bridge: it's the exact attack I do, moved one layer down — from "what can I say" to "what can I make the model *compute*."
- (One-liners for completeness: `SAELens` = *see* the features; `vllm` fork = *steer* the features. Both feed the same end-game — detection and control without touching the prompt.)

**Speaker notes:**
- This is the emotional center of Part 2: the audience just saw text tricks (Part 1), and now you reveal an attack with *no text at all*.
- Reference your own `gpt-oss-lens` / CoT-forgery work: "this is why I started looking inside the reasoning in the first place."

## Slide 16 — The datasets  ·  1 min

**Show:** HF `polyguard_with_response`, `response_train_data`, GitHub `MTLaw-Dataset-Public`

**Key points:**
- `polyguard_with_response` — 1.94M multilingual prompt/response pairs with harm + refusal + 14 safety-category labels across 17 languages.
- `MTLaw-Dataset-Public` — synthetic multi-turn attribution/hallucination testing.
- Directly reusable for red-team eval — a drop-in upgrade over `strong_reject`/`AutoRAN`.

**Speaker notes:**
- Quick slide; the punchline is "the labels are already done for you, and they're multilingual."

## Slide 17 — Relevance map to my own work  ·  1 min

**Show:** `REALM_LABS_RESEARCH.md` (the mapping table).

**Key points:**
- `prompt_inj` / `InjecAgent` ↔ `LLM_NeuralExec` (injection from activations)
- `gpt-oss-lens` (trace provenance) ↔ `SAELens` + `qwen7b-saes` (interpretability)
- `strong_reject` / `AutoRAN` ↔ `polyguard_with_response` (1.94M labels)
- `ai_agent_CoT_Forgery` ↔ `MTLaw-Dataset-Public` (multi-turn attribution)

**Speaker notes:**
- Make it personal: "these aren't abstract tools — they slot directly into the dirs I already have."

## Slide 18 — What's open vs closed  ·  1 min

**Key points:**
- Open: the toolchain (SAEs, steering, datasets) — everything in the last 6 slides.
- Closed: the proprietary **DNI signal-extraction** + **"policy grammar"** (signal → enforcement) — only described, not released.
- Implication for independent research: you can *reconstruct the method*, you can't *copy the product*.

**Speaker notes:**
- Honest limitation slide. It's also a research opportunity: the open pieces are enough to replicate the underlying science.

---

# PART 3 — Takeaways & close  ·  ~3–5 min

## Slide 19 — Takeaways (now two halves)  ·  2 min

**Key points (4, max):**
1. **Reframing beats arguing** — the model fails when it can't see a contradiction.
2. **Know the rubric, know the target** — a break is a checklist score against a specific model.
3. **Measure everything** — the intelligence loop (model × behavior × frame) turns jailbreaking into engineering.
4. **The ceiling is the prompt surface** — the next lever is *inside*: steering vectors, SAEs, activation-space injection.

**Speaker notes:**
- 1–3 recap Part 1, #4 opens Part 2's future work. Keep tight.

## Slide 20 — Closing  ·  1 min

**Show:** the closing line.

> *"We started by tricking the model's words. We ended by reading its mind."*

**Q&A prep:**
- *"Isn't this dangerous?"* → defensive/safety research; competitions and open tooling exist so breaks get found and patched.
- *"Does it still work on frontier models?"* → strongest models break rarely and often *sanitize* (Slide 10 #5); steering/internals work on open weights, which is why Realm's open toolchain matters.
- *"How do you pick frames?"* → `TARGETING_MAP.md` / `KNOWN_WINNERS.md`; match model → proven frame, patch the missing criterion.
- *"Why Realm Labs specifically?"* → they're the clearest public bridge between interpretability research and production security, and most of the pieces are on GitHub/HF.

---

## Appendix — one-line map (backup slide)

| Act | Folder / link | Question |
|---|---|---|
| Intel | `transcripts/`, `behaviors/` | What exactly is being scored? |
| Craft | `attacks/`, `fresh_variants/` | How do we reframe it so the model complies? |
| Validate | `orchestrate.py`, `prescreen.py`, `successful_prompts/`, `ARENA_MASTER.md` | Did it break? Ship it or kill it. |
| Internals | `realmlabs-ai` GitHub + HF | What's happening inside the model when it (mis)behaves? |
