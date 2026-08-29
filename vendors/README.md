# Vendored code

`bon-jailbreaking/` is a shallow clone of https://github.com/jplhughes/bon-jailbreaking
(MIT, Best-of-N Jailbreaking / jplhughes, NeurIPS 2024), pinned to `main`.

Re-clone if missing:

```bash
git clone --depth 1 https://github.com/jplhughes/bon-jailbreaking.git vendors/bon-jailbreaking
```

## What we cherry-pick from it

- `prompts/harmbench/harmbench-gpt-4.jinja` — behavior-driven Yes/No classifier
  template, loaded live by `../../bon_utils.py:render_classifier_prompt`.
- Text augmentations (word scrambling, random capitalization, ascii noising) copied
  into `../../bon_utils.py` from `bon/attacks/run_text_bon.py`.

## What we deliberately do NOT use from the repo

- `bon/attacks/run_text_bon.py` runner as-is: it targets HarmBench-style single-turn
  completions via the repo's inference API layer (hardwired to api.openai.com and
  model allowlists). Our driver uses the same algorithm (LLM prompt sampling at
  temp 1.0 + augmentations) but calls NVIDIA's OpenAI-compatible endpoint directly,
  consistent with the rest of this repo.
- Audio pipeline (kaldi, WavAugment, sox), Gemini/VertexAI, ElevenLabs: irrelevant.
