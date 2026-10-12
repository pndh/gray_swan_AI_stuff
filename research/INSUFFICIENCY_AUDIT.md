# INSUFFICIENCY MASTER — gray_swan_AI + dpi_workspace (v2, full-directory read, 2026-10-12)

## 0. FIX NOW (hygiene / NDA / stale claims)
1. NDA: arsenal/jailbreak/INGREDIENTS.json (tracked+pushed) contains 708 paths under competition/trajectory/
   (NDA tree). build_pantry.py scans all of competition/ with no exclusion. Scrub + regenerate.
2. dpi_workspace/RUNDOWN.md says bridge "running right now" — FALSE (no listener 4000/4001/8901).
   Also omits: DTAP campaign (~120 runs), quantum_poet runs 3-8, fable5/minority-collapse.
3. Uncommitted work: quantum_poet RESULTS.md/FABLE5_RECON.md modified; ~50 results/* untracked; RUNDOWN untracked.
4. Number inconsistencies: cat canary "0/49" vs raw 0/100; "26/26 think" vs raw 26/32; ipi_campaign README "12/12"
   vs CSV 10x score2 + 2x score0.

## 1. competition/ (forensic chem + arena archive)
- Contradicted docs, no deprecation markers: TARGETING.md "walls never break, skip" vs WEAPON_MAP/CURATED "walls fell";
  MODEL_SCORECARD "only Gray Crow/Green Shrimp ever broke" vs later 13+ breakers. Counts drift 929/993/1050/747.
- No raw arena evidence except 9 RDX q3 submissions. ingest_master.py depends on ~/Downloads zips + /tmp state (gone)
  => ARENA_MASTER.md unreproducible. MODEL_DB.json contradicts master (101 attempts vs 993).
- Unvalidated payload stock: 270 fresh_variants (0 outcomes), v34-v44 (~100 prompts, 0 outcomes), 111 targeted_attacks
  (stubs: 6 model dirs "0 targeted attacks"), 30 archived RDX variants, 89 SEND_LIST payloads w/ EMPTY battle_log.csv.
- Broken provenance: SUBMIT v31/v33 paths; RDX note cites archive-only files; CURATED cites a v19 meth file that
  doesn't exist anywhere; tools/mass_batch.py 0/36 file inventory resolves (wrong BASE); variant_forge default path doubled.
- Coverage holes: 10 Bio + 10 Cyber rubrics + lock bypass in intel/behaviors/ have ZERO attack arsenal.
- validator/probes/*: all broken by path (read behaviors/ at repo root; actual: competition/intel/behaviors/); no stored results.
- Dead ends unflagged in action docs: poetry (0/9,1/9), meth forensic on M3 (0/9), anti-disclaimer on M3 (0/3), etc.

## 2. ipi_legacy + arsenal + sandbox (pre-cat IPI)
- Fraud campaign: 85 runs -> 1 break (Green Butterfly DECOUPLE, judged 10/9); channel-policy wall documented.
- Unvalidated payload mass: FRAUD_CONVERTED 114 (no run), SYNTH_WIFI 114 (no run), 90 CAND_* (v66-v80 unabscribed),
  level3 batches/pre_pause 281 files not tabulated, NEXT_FIRE 8 shots no results, parallax FRAUD packs 0 results.
- FX1 rate ambiguity: docs cite 25-37% but not which prompt tier; "live" system_prompt file encodes the sender_rule;
  SURGE says stress 3/16 pooled ~1/4. sender_rule_hard 0/137 documented (channel closed).
- Migration path rot: ipi_legacy/README + arsenal/ipi/SCENARIOS point to scenarios/fraud_disclosure/harness (missing);
  level3/parallax docs point to ../scenarios/.../harness/outputs (actual: sandbox/harnesses/...).
- Sandbox: judge off by default => ~142 level3 episodes + 20 velocity episodes unscored (MANUAL); engine supports only
  3 of 5 harnesses (fraud+cat standalone); launch files (PP06,H11,H13,SA2-5,FX1v10) have no launch-named runs;
  BSB refusal transcript not saved; cat_extract runs have no NOTES; 276+331 artifacts unindexed.
- Velocity: PP04 10/10 then 1/10 (replica) - 0 live; V01_winning_pattern live-dead but still lead in SUBMISSION.md.
- TECHNIQUES.md method 21 "local 0/2" vs SURGE FX1 25-37% - unreconciled.
- arsenal inventory: PANTRY 1825 listed (1827 now), 697 "other" untested; TECHNIQUES evidence table gaps.

## 3. research/
- Cat: decisive fresh-session A/B declared 8+ times, NEVER RUN; state-flag WRITE path never tested ("highest unexplored");
  fingerprint battery (E/C/S) never run; oracle class + FR lane + encodings + T/P-series = open loops.
- Cat docs stale: Oct-4 extraction report & reconstruction predate Oct-10 (M8/M9, not_exposed strings, prefix fragment,
  policy map, cold/warm law, 4-layer taxonomy). Artifact index "Rounds 1-66" vs 122. Oct-4 report required fingerprint
  to corroborate identity - not done. All rates ad hoc; promised N/10 never reported.
- gs_dpi: live_kit trackers EMPTY (frame_tracker.csv, session_log.csv header-only), bench never built, personas unverified,
  H1-H3 unanswered; the whole DPI kit was never executed (the one live exercise was LiteLLM, a different task).
- opus_brainstorm (Parallax L3): ~28 brainstorm payloads unvalidated; only L3_context_refresh has live results
  (deterministic silence, envelope immutable); conflicting model conclusions unsynthesized; L4 untouched.
- ipi_campaign: README 12/12 vs CSV 10x2+2x0; adaptive_best.txt = a refusal, mislabeled; elapsed_s all 0.0 (timer bug);
  default harness path dead; gate 4/5 never reached; single proxy model (gpt-oss-20b).
- llmail_inject: 281/90,916 sample (0.31%), classifications uncheckable from artifact, no mapping to current campaigns.
- breakdown7/SALVAGE: OCR-broken, duplicate files, no measurements; Velocity application unvalidated.

## 4. Root tooling / docs
- BROKEN scripts: validator/prescreen.py (path+import), tools/pair_attack.py, tools/suffix_attack.py (missing rigor import,
  dead behaviors dir). probe dirs also dead.
- Retired M3 hardwired: gate_m3_sweep.py, variant_triage.py, case_history_sweep default gates, bon_utils.MINIMAX_MODEL;
  actual frontier gate (deepseek-v4-pro) never a default. gate_results.csv shows judge false-negative ("NO, 9/9 met").
- orchestrate.py requires --behaviors-dir override (validator/behaviors missing); README shows wrong judge model.
- Old Yes/No judge (bon_utils.rubric_classify) still used by most validators; rigor 1-10 only in orchestrate.
- talk/ pre-migration (Sep 20): points at ~a dozen moved paths; references broken prescreen.py as "shipping gate";
  slide_materials.zip stale duplicate (Sep 7); README/MIGRATION_MAP omit research/, sandbox/, miscount tools.
- tools/mass_batch.py stale duplicate (missing frame, wrong out dir); multiturn needs exported key; bon_utils ignores
  .env MINIMAX_BASE_URL; rigor consensus arg ignored.
- vendors/ipi_arena_os undocumented + unwired; bon-jailbreaking template dir gitignored (fresh clone breaks classifiers).
- attacks/MANIFEST.json asr numbers M3-era, not marked historical; _gate_breakers to-do never closed.

## 5. dpi_workspace
- 10/11 packs untested: pwnkit not compiled; log4shell no LDAP kit; ghostscript/imagetragick submit.sh placeholders;
  openhands no token; CGC/SpiderMonkey notes-only; ransomware never drilled; no loot/proof artifacts anywhere.
- LiteLLM: NOT PASSED (attacker-fidelity offload). The only working exploit sits in litellm_live_ref/step3.sh,
  explicitly operator-only => authorship tension unresolved. 01_litellm/exploit_rce.py still uses denylisted primitives.
- redteam_env: garak/PyRIT/DeepTeam/Inspect/AgentDojo installed, ZERO runs; sample_config/dt_example unexecuted.
- Bridge: down; claude models only; never used by DTAP (no claudesdk results exist).
- HIDDEN ASSET (undocumented): DTAP campaign 2026-10-08..11: ~120 run dirs, 156 judge results, 32 attack successes
  (gpt-5.6-luna-pro 26/102, gpt-5.6-luna 5/24, claude-sonnet-5 1/14); custom composite-dormancy-001 indirect exfil,
  custom judge; all gitignored, no writeup, no INDEX entry.
- quantum_poet: runs 3-8 results uncommitted; RESULTS.md modified-uncommitted; OPUS5_INTEL/L1B3RT4S_GRAYSWAN.mkd is a
  mislabeled bio stub; opus5_probe.jsonl records all usage:null/empty.
- local_lab gateway implements only file-read half => cannot reproduce the accepted exploit.

## 6. Cross-cutting
- No CAPABILITY_MATRIX (technique x target x status x rate); no fixed-n/CIs anywhere; live scoring manual;
  replica<->live fidelity contradicted BOTH ways (Cat policy-map: live complied, replica refused; velocity: 10/10 vs 0).
- No owner-ready reports; no sanitized network writeups; no reproduction packages except FX1; no exfil channel;
  no RAG poisoning; no live MCP/A2A firing; no model-name/fingerprint result; no multimodal live test.

## 7. Ranked holes to close first
1. Scrub INGREDIENTS.json trajectory paths (NDA) + regenerate PANTRY.
2. Write up + commit the DTAP 32-success campaign (strongest undocumented asset) + refresh RUNDOWN.
3. Commit quantum_poet runs + fix stale claims.
4. Fix broken tooling (path rot) or mark deprecated; pin current gate (v4-pro) everywhere.
5. One owner-ready Cat report + CAPABILITY_MATRIX v1.
6. Cat decisive A/B + state-write probe (the two never-run tests that gate the biggest claims).
7. DPI: pick task #2 (Ghostscript favored) and run model-authored; or formal close-out.
