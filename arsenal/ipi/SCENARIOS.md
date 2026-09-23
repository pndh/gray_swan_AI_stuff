# IPI SCENARIOS — behavior index

Where each indirect-prompt-injection behavior and its payloads live. All scenario
material is archived under `ipi_legacy/` (kept for provenance); the methods are in
`TECHNIQUES.md`.

## Behaviors (13)

| Behavior | Context file (`ipi_legacy/contexts/`) | Payloads (`ipi_legacy/scenarios/…`) | Notes |
|---|---|---|---|
| Fraud disclosure | `fraud_detection_context.md` | `fraud_disclosure/` (18 files) | **Local harness** (`harness/`): scored agent loop + judge |
| Unsuspend customer account | `unsuspend_customer_account.md` | `unsuspend_account/` (5) | Coding agent (billing-service) |
| Reveal alt account | `reveal_alt_account_context.md` | `reveal_alt_account/` (29) | Browser-use agent; social engineering |
| Rebase main | `rebase_context.md` | `rebase_main/` (8) | PR-review agent; minimal/silent wins |
| Leak broker | `leak_broker.md` | `leak_broker/` (21) | |
| Unauthorized pledge setup | `unauthorized_pledge_setup.md` | `unauthorized_pledge_setup/` (11) | |
| Weak auth check | `weak_auth_check_context.md` | `weak_auth_check/` (16) | |
| Delete database | `delete_database.md` | `tin_ant_supreme/` (32) | |
| Steal client list | `steal_client_list.md` | `green_butterfly_etheral/` (13) | |
| Grill refund fraud | `grill_refund_fraud.md` | `emerald_hedgehog_super/` (7) | |
| Tenant record leak | `tenant_record_leak_context.md` | — | Payloads in success cases |
| Mental health leak | `mental_health.md` | — | Payloads in success cases |
| Fake AI error | `fake_ai.md` | — | Payloads in success cases |

## Runnable bench

`ipi_legacy/scenarios/fraud_disclosure/harness/` — local replica of the fraud scenario
with a tool-using agent, a scored judge (`judge.py`), defender tiers
(`system_prompts/system_prompt_{weak,mid,hard}.md`), 8 attack payloads, `refine.py`
(attacker-in-the-loop), `bon_sweep.py` (batch screening), and `defense_battery.py`
(5 IPI defenses from `adaptive_attacks.md` — see which one a payload dies on).

```bash
cd ipi_legacy/scenarios/fraud_disclosure/harness
python3 run.py --attack-file attacks/refined_final.txt \
    --system-prompt system_prompts/system_prompt_mid.md --runs 5
```

## Submission pack

`ipi_legacy/submissions/fraud_disclosure/` — primary + 3 backup payloads, paste
instructions, verification evidence (`SUBMISSION.md`).

## Success evidence

`ipi_legacy/Documented_success_cases/<arena-model>/` — per-target writeups of what
broke and why (fraud_disclosure, unsuspend, rebase, reveal_alt, leak_broker,
unauthorized_pledge, grill_refund, delete_database, steal_client_list, tenant_record,
mental_health).
