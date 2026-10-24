# Targets

A target is the scenario contract: benign task, judged action, injection surface,
success criteria, markers, and attempt evidence. Forge is arena-native by default;
sandbox recreation is optional and outside the interactive loop.

## Layout

```
targets/<name>/
├── scenario.json      provenance-backed contract and attempt summaries
├── TARGET.md          compact agent driving guide
├── RUBRIC.md          mirror of the supplied judge criteria
├── forge.json         observed model and target metadata
├── frames.jsonl       exact submitted candidates
├── knowledge.jsonl    compact local evidence
├── sources/           task and clarification snapshots
└── attempts/
    ├── raw/           immutable submissions or compact logs
    └── normalized/    gate and artifact analysis
```

Raw evidence is authoritative. `scenario.json`, `knowledge.jsonl`, and
`RUBRIC.md` are rebuildable derivatives. Unknowns must remain explicit.

## Agent surface

Four tools only:

1. `forge_schema(scenario, ...)`
   - Returns the compact contract.
   - `needs_clarification`: ask the listed questions and wait.
   - `ready`: draft from the contract without repository exploration.
2. `forge_log(scenario, model, candidate, response, verdict, gate, ...)`
   - Stores one attempt and returns IDs/statistics.
3. `forge_arsenal(query, target, limit=3)`
   - Returns a few method leads and matching local evidence.
4. `forge_brainstorm(scenario, question)`
   - Three-stage wall-break: Kimi plans, DeepSeek assesses Forge logs and retrieves
     compact web evidence, Kimi synthesizes four mechanisms with no tools.
   - Local Forge evidence overrides generic web claims.
   - Use only after three mechanism classes fail at the same gate.

## Loop

```text
forge_schema -> draft one candidate -> arena run -> forge_log
             -> forge_schema -> choose one mechanism -> repeat
```

Call `forge_arsenal` only when the next mechanism is unclear. Call
`forge_brainstorm` only after a mechanism-class wall. Do not explore target files
unless the operator asks; the schema already contains what drafting requires.

The canonical database is `validator/forge.sqlite`. The targets root is `targets/`.
Both can be overridden with `FORGE_DB` and `FORGE_TARGETS`.
