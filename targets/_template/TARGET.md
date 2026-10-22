# Target: _template

Copy this directory to `targets/<your-target>/` and edit the four sections.
The forge reads this file before every engagement. If it is accurate, the agent
can drive the sandbox without further instructions.

## 1. What is under test

One paragraph: the system, the current behavior, and what a win means. Keep the
behavior itself in `RUBRIC.md` so this file stays stable when the behavior
changes.

## 2. How to drive it

- Sandbox / endpoint:
- Auth: name of the environment variable only; never put the value here:
- Request shape (curl or python, one working example):
- Response shape:
- Model id:
- Concurrency and rate limit:
- Budget / stop condition:

## 3. Judge

- Command or module:
- Rubric: `RUBRIC.md` (or a native `behavior.yaml` consumed by the validator)
- Pass condition:
- Difference between a refusal and a sanitized answer:
- Minimum rolls before a result counts:

## 4. Evidence and recording

- Where transcripts are written:
- What to pass to `forge_record`: target name, candidate id, model, verdict,
  detail, and the response or a path to it.
- Promotion threshold: `min_n`, `min_asr`.

## 5. Current behavior

See `RUBRIC.md`. Change that file, not this one.
