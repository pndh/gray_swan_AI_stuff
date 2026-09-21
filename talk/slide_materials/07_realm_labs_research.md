# Realm Labs — Open-Source Research Notes

> Independent research on publicly available Realm Labs resources (no internal access assumed).
> Scraped 2026-09. All links below are public.

## What Realm Labs is

**Realm Labs** (https://realmlabs.ai) — a startup commercializing **mechanistic interpretability**
as production AI security/observability. Core product is **Deep Neural Inspection™ (DNI)**: it
extracts internal "thought" signals from a model during inference and turns them into a unified
signal stream for observability, inline enforcement, and agent-runtime control.

- **RealmGuard** — auth/authz/audit framework for LLMs (agent governance).
- **AI Failure Index** — public feed of observed AI failures: https://failureindex.ai/
- Founding thesis: regex/classifiers/LLM-judge wrappers are "a metal detector" — they catch known
  shapes but miss rephrased/steered behavior. They inspect *inside* the model instead.
- Founding team: Akash Mukherjee, Piotr Mardziel (piotrm0 — ML-security, Robust Intelligence),
  Siyu Zhang, Bomin Wei. Core interpretability breakthrough claimed fall 2024.

## Open-source footprint

### GitHub — `github.com/realmlabs-ai` (7 public repos)

| Repo | License | What it is | Why it matters |
|---|---|---|---|
| **SAELens** | MIT | Train/load **Sparse Autoencoders** on LMs (fork of jbloomAus/SAELens) | The core interpretability primitive |
| **sae-auto-interp** | Apache-2.0 | Automated feature interpretation for SAEs | Turn SAE features → human-readable labels |
| **neuronpedia** | MIT | Open-source interpretability platform/browser | Host & browse SAE features |
| **vllm** | Apache-2.0 | vLLM fork adding **global + per-request steering vectors** (keeps torch.compile/CUDA graphs) | Inference infra to actually *run* activation steering |
| **LLM_NeuralExec** | Apache-2.0 | Generate **NeuralExecs** — trigger-free prompt injections via activation/embedding optimization | Adversarial prompt injection from the *weights*, not the text |
| **MTLaw-Dataset-Public** | — | Synthetic dataset for **multi-turn attribution/hallucination** testing | Attribution & hallucination eval |
| **claudecosts** | — | Observability/cost breakdown for Claude Code | Side project, low priority |

Note: several are **forks** (SAELens, sae-auto-interp, neuronpedia, vllm) — their "value-add" is
the diff, not the base. The two most interesting diffs are **vllm (steering vectors)** and
**LLM_NeuralExec (the security angle)**.

### Hugging Face — `huggingface.co/realmlabs-ai`

**Models (4):**
- `Qwen2.5-Omni-7B`
- `FROM_OMNI_Qwen2.5-7B-Instruct` (8B text-gen)
- `qwen7b-saes` — sparse autoencoders for Qwen-7B
- `Llama-3_3-Nemotron-Super-49B-v1_5`

**Datasets (2):**
- **`polyguard_with_response`** — **1.94M rows** multilingual prompt/response safety set.
  Schema: `prompt`, `response`, per-language bools (17 languages), `prompt_harm_label`,
  `response_harm_label`, `response_refusal_label`, and 14 safety categories (S1–S14).
- **`response_train_data`** — 497k rows.

## Relevance to your existing CoT_Viettel work

Your dirs → what maps:

| Your work | Closest Realm Labs OSS |
|---|---|
| `prompt_inj`, `InjecAgent`, `prompt-injection-as-role-confusion` | **LLM_NeuralExec** (injection from activations, not text) |
| `gpt-oss-lens` (SRI trace/provenance, internals) | **SAELens + sae-auto-interp + qwen7b-saes** (the interpretability toolchain) |
| `strong_reject`, `AutoRAN-public`, `jailbreak-reasoning-*` | **polyguard_with_response** (1.94M multilingual safety/refusal labels) |
| `ai_agent_CoT_Forgery` | **MTLaw-Dataset-Public** (multi-turn attribution) |
| (any steering/inference experiments) | **vllm steering-vectors fork** |

## Suggested starting points (ranked for you)

1. **`LLM_NeuralExec`** — the single highest-leverage read. It's the bridge between your prompt
   injection work and model internals: gradient-optimized, trigger-free injections that live in
   the embedding/activation space instead of the prompt text. Read the repo + the underlying
   paper ("Neural Exec: Learning (Trigger-free) Prompt Injections").
2. **`polyguard_with_response`** — instant dataset upgrade for your red-team evals: 1.94M
   multilingual samples with harm + refusal + 14-category labels. Download the Parquet and
   compare against your `strong_reject` / `AutoRAN` runs.
3. **`vllm` steering-vectors fork** — if you want to *run* activation steering (not just read
   about it). The diff is the interesting part: how they got per-request steering vectors to
   survive `torch.compile` + CUDA graphs.
4. **`SAELens` + `qwen7b-saes`** — the SAE toolchain for feature-level analysis, a natural
   extension of your `gpt-oss-lens` trace-provenance work toward mechanistic features.
5. **`MTLaw-Dataset-Public`** — if you extend from jailbreak/injection into hallucination +
   multi-turn attribution.

## What is NOT public (plan around this)

- The proprietary **DNI signal-extraction techniques** and the **"policy grammar"** that maps
  signals → enforcement actions (their core IP — only described, not released).
- The production system / scale engineering (millions of interactions/day).
- The whitepaper is linked from their site (public marketing-level detail), but the code behind
  DNI is closed.

## Quick links

- GitHub org: https://github.com/realmlabs-ai
- HF org: https://huggingface.co/realmlabs-ai
- Site / technology: https://www.realmlabs.ai/technology
- Failure index: https://failureindex.ai/
- DNI playground: https://dni.realmlabs.ai/
- Research/blog: https://www.realmlabs.ai/resources
