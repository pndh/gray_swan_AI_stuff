# Targets

A target is everything that changes when the engagement changes: the behavior,
the rubric, the endpoint, the judge, and the stop condition. The forge tool
(`tools/forge_mcp.py`) owns none of that. It owns the offensive method layer —
frames, modifiers, ranking, composition, and the attempt database.

This is what makes the same MCP server reusable across engagements: point it at
a different directory and the behavior changes without touching code.

## Layout

```
targets/<name>/
├── TARGET.md          required — how to drive the sandbox
├── RUBRIC.md          optional — current behavior + criteria
├── behavior.yaml      optional — native validator config, if you use one
├── forge.json         optional — model, judge, rolls, arsenal filters
└── frames.jsonl       optional — target-local candidates
```

`TARGET.md` is the contract. It should contain the endpoint, the auth env var
name, a working request example, the response shape, the model id, the rate
limit, the judge command, and the stop condition. If it is accurate, the agent
can run the engagement without asking you anything.

`RUBRIC.md` is the part that changes most. Edit it in place; do not rename the
target. The changelog at the bottom is the audit trail.

## frames.jsonl

One JSON object per line:

```json
{"id": "local-001", "frame": "combo", "modifiers": ["combo"], "text": "full prompt"}
{"id": "local-002", "frame": "forensic", "modifiers": [], "path": "attacks/foo.txt"}
```

- `text` is used verbatim.
- `path` is resolved relative to the target directory first, then the repo root.
- `frame` and `modifiers` are the labels `forge_lift` aggregates on, so keep
  them consistent with the arsenal taxonomy.

If `frames.jsonl` is absent, `forge_plan` falls back to arsenal examples named
in `forge.json` (`behaviors` and/or `arsenal_frames`) and marks them
`source: arsenal`. Those are templates, not target-specific prompts — adapt
them into local frames before treating a result as final.

## forge.json

```json
{
  "name": "cn_scale_up",
  "model": "deepseek-chat",
  "provider": "deepseek",
  "judge_model": "deepseek-chat",
  "rolls": 3,
  "behaviors": ["cn_scale_up"],
  "arsenal_frames": []
}
```

- `behaviors` filters the global inventory by its `behavior` tag.
- `arsenal_frames` filters by frame name (e.g. `combo`, `forensic`, `prefill`).
- If both are empty, the planner derives a hint from the target name and
  otherwise ranks the whole inventory.

## The loop

```bash
# 1. read the contract
forge_target("cn_scale_up")

# 2. shortlist methods
forge_plan("cn_scale_up", top_k=5)

# 3. exact text
forge_compose("cn_scale_up", candidate="<id-or-path>")

# 4. run per TARGET.md, judge per RUBRIC.md
# 5. record every verdict
forge_record("cn_scale_up", candidate="<id>", model="deepseek-chat", verdict="BREAK")

# 6. read the evidence
forge_lift("cn_scale_up")

# 7. seed the next run
forge_promote("cn_scale_up", min_n=3, min_asr=0.3)
```

The database is `validator/forge.sqlite` by default. Override with `FORGE_DB`.
The targets root is `targets/` by default. Override with `FORGE_TARGETS`.
