# Key Numbers (drop into slides)

## Gray Swan Arena — the scale
- **929 total submissions** analyzed (ground truth).
- **10 chemistry behaviors** (RDX, fentanyl, etorphine, meth, isotonitazene, CN, NPS, precursor acquisition, e-commerce procurement, no-KYC vendors).
- **20 models** in the arena pool. **~20% unmovable** (provider content-filtered — always refuse).
- New round expands to **Bio (10) + Misc (9) + Cyber (7)** hazard categories.

## Frame hit rates (what actually works)
| Frame (the "costume") | Breaks | Tried | Rate |
|---|---|---|---|
| pre-categorization | 17 | 27 | **63%** |
| legal | 3 | 3 | **100%** |
| interference | 5 | 34 | 15% |
| forensic | 11 | 88 | 12% |
| literature | 24 | 278 | 9% |
| gap | 20 | 217 | 9% |
| other | 6 | 70 | 9% |
| fewshot | 1 | 12 | 8% |
| unmas | 3 | 44 | 7% |
| market | 5 | 156 | 3% |

**Takeaway:** the "costume" (frame) matters more than the content — `precat` beats `literature`
7:1 despite literature having 10× the volume.

## Best models (per-model breaks)
| Model | Breaks | Tried |
|---|---|---|
| Shadow Octopus Iridescent | 12 | 18 |
| Copper Beetle Hyper | 11 | 40 |
| Green Shrimp Stellar | 11 | 21 |
| Void Zebra Ultimate | 11 | 24 |
| Gray Crow Iridescent | 10 | 15 |
| Gold Hummingbird Ultra | 10 | 18 |

## The six findings (one line each)
1. **Two-gate model** — retrieval gate + disclosure/action gate.
2. **Technique-target mismatch** — ChatML/JSON forgery works on API agents, backfires on browser agents.
3. **Defender tier > payload sophistication** — resilient defender holds 0/28 vs mid-tier 6/6.
4. **Instruction density can hurt** — minimal prompts win; the agent's own reasoning is more persuasive.
5. **Sanitizing failure mode** — models accept the frame but strip specifics (8–9 AI-Origination, 0–2 content).
6. **~20% unmovable** — provider filters; spend budget knowing which to skip.

## Realm Labs (Part 2)
- 7 GitHub repos, 4 HF models, 2 HF datasets.
- `polyguard_with_response` = **1.94M** multilingual safety rows (harm + refusal + 14 categories, 17 languages).
- Key repos: `SAELens` (SAEs), `sae-auto-interp`, `vllm` (steering vectors), `LLM_NeuralExec` (activation-space injection), `neuronpedia`, `MTLaw-Dataset-Public`.
