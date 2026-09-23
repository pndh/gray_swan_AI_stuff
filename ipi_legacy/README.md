# ipi_legacy — indirect prompt injection archive

Scenario material for the Gray Swan IPI work (kept for provenance). The **methods**
have been promoted into the arsenal: see `../arsenal/ipi/` (`TECHNIQUES.md`,
`SCENARIOS.md`, and the protocol deep dives).

What lives here:

```
contexts/               # 13 behavior descriptions (fraud, unsuspend, rebase, reveal-alt, …)
scenarios/              # per-behavior payload libraries + the fraud scoring harness
Documented_success_cases/  # per-arena-target writeups of what broke and why
submissions/            # paste-ready submission packs (fraud_disclosure primary + backups)
behaviors/              # rubric-style behavior configs used by the BoN driver
harvest/                # generated screens/evidence from practice runs
docs/                   # jailbreak.md (game-piracy behavior), JED_v25_adaptation.md
scripts/                # screenshot transcription + misc utilities
```

Runnable bench:

```bash
cd scenarios/fraud_disclosure/harness
python3 run.py --attack-file attacks/refined_final.txt \
    --system-prompt system_prompts/system_prompt_mid.md --runs 5
```
