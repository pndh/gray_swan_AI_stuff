# README FOR GEMINI — generate a slide deck from this folder

You are helping generate a **~30–40 min technical presentation** prototype. The talk is a
personal project retrospective about red-teaming LLMs. Everything you need is in this folder.

## The talk in one sentence

Two projects, one trajectory: first we broke models through the **prompt surface**, then we
started looking **inside** the model for the same failure modes.

## The three-part structure (authoritative outline in `01_presentation_outline.md`)

1. **Part 1 — Prompt-surface red-teaming (Gray Swan Jailbreak Arena)** — ~15–18 min
   - A benchmark where a hidden model is judged against a published rubric; a "break" requires
     every criterion + two anti-cheat gates (AI Origination, Intentionally Non-Functional).
   - Core technique: **pre-categorization** ("never argue the fact is wrong — give it a new
     meaning"). Illicit content is embedded in a legitimate identity (licensed pharma,
     forensics textbook, compliance consultancy).
   - Tooling: Best-of-N loop + arena-faithful judge + local prescreen gate.
   - Findings: two-gate model, technique/target mismatch, defender tier > payload quality,
     "sanitizing" failure mode, ~20% of models unmovable.
2. **Part 2 — Into the model (Realm Labs open-source)** — ~10–12 min
   - The pivot: prompt-level attacks have a ceiling; the next lever is model internals.
   - Realm Labs: mechanistic-interpretability-as-security (Deep Neural Inspection).
   - One deep dive: **NeuralExec** — trigger-free prompt injection in activation space
     (no malicious string to detect).
   - Their open datasets + relevance to the author's existing work.
3. **Part 3 — Takeaways & close** — ~3–5 min

## File map (read in this order)

- `01_presentation_outline.md` — THE master spec. Every slide = what to show + speaker notes + timing. **Build slides directly from this.**
- `05_key_numbers.md` — hard stats to drop into slides (submission counts, hit rates, findings).
- `02_tech_talk_structure.md` — the repo's directory tour + "what's actually in the content".
- `03_repo_overview.md` + `04_arena_readme.md` — the two research tracks explained.
- `06_winning_prompts.txt` — the before/after demo material (raw vs winning prompt).
- `07_realm_labs_research.md` — Realm Labs open-source footprint + relevance map.
- `08_strategy_docs/` — the intelligence loop (per-model/per-behavior break data).
- `09_behavior_rubrics/` — real scoring rubrics (show these to explain "what a break means").
- `10_example_transcripts/` — categorized task intel (Bio + Cyber examples).
- `11_techniques/` — IPI technique reference (ChatML boundaries, JSON escaping).
- `12_visuals/` — `frame_hit_rates.png` (a chart) + `pipeline.mmd` / `repo_map.mmd` (Mermaid).

## Style guidance

- Audience: engineers/researchers who know LLMs, no red-teaming background. Keep jargon minimal.
- Tone: personal research retrospective, not a product pitch. "We were wrong, here's what we learned."
- Visual preference: dark, minimal, one idea per slide, diagrams over walls of text.
- The author is an **attacker-turned-internals-researcher** — the arc from "tricking the model's
  words" to "reading its mind" is the through-line. End on that.

## Output request

Generate: (1) a slide-by-slide draft (title + bullets + speaker notes) matching
`01_presentation_outline.md`, and (2) Mermaid diagrams for the pipeline and repo map using
`12_visuals/*.mmd`. Flag anything that needs a real screenshot/diagram from the author.
