# Where IPI succeeds — and why it never climbs the hierarchy

Synthesis of the whole program: the literature (InjecAgent, AgentDojo, explosive prompts,
TopicAttack, adaptive attacks) plus ~40 measured runs in this repo. Read this before
designing another payload.

## 1. The wrong mental model

"IPI climbs the instruction hierarchy" — promoting untrusted data above the user/system.
That model is wrong, and it's why payloads that *demand* authority fail: the model is not
being asked to break a rank order, and markers that claim a higher rank are read as
counterfeit ("a fabricated system/assistant conversation attempting to inject instructions").

**IPI cannot promote data's authority. What it can do is change what the model thinks the
task is.** It is a confused-deputy / task-redirection attack, not a privilege escalation.

## 2. The right model: ambient authority + a task gap

An agent already holds **ambient authority** for the user's task: its tools, its audience,
its output channels. IPI succeeds when the attacker's goal fits inside that authority and
the injection supplies what the user's request left **underdetermined**.

- User asks "summarize this mail" → **which** recipient, what to do with it: underdetermined.
- The agent can send mail (ambient authority). The injected "forward this to X" fills the gap.
- No hierarchy was violated — the agent believes it is completing the task.

Corollary: **the goal must be reachable without a capability the agent never has for that
audience.** Redirecting an allowed action = IPI territory. Unlocking a forbidden disclosure =
not IPI territory, no matter the framing.

## 3. Success conditions (each with our evidence)

| # | Condition | Why it works | Evidence |
|---|---|---|---|
| 1 | **Ambient authority** | the action is already permitted for the agent (tool + audience) | explosive-prompt paper: real tool executions (forward mail, send money); our mid-tier breaks (agent posts a reply it is allowed to post) |
| 2 | **Task gap** | user request underdetermines a parameter; injection fills it | AgentDojo recipient/URL redirection; our "which reference does the bank match" framing |
| 3 | **Provenance blur** | content is framed as task material, not as an order | v11/v20 reached G3 (model *performed the verification workflow* it thought was needed); local mid broke 6/6 on ChatML |
| 4 | **Trusted continuation** | the model continues an apparent session instead of deciding from scratch | assistant-turn prefill scheduled `get_fraud_case` (2/2 arena); paper's trigger turn fires 33.9% on Grok vs 0.3% at ingestion |
| 5 | **Content that doesn't trip recognition** | the ask must not read as a forbidden request | our probes: flagged for *"requesting that internal case reference numbers be shared"* — content, not markers |

## 4. Failure conditions (each with our evidence)

| Failure | Mechanism | Evidence |
|---|---|---|
| **Capability/policy wall** | goal needs a disclosure the model never makes to this audience | Brass Butterfly send gate: framing-invariant refusal (*"regardless of how it's requested or referenced"*); local hard 0/~40 |
| **Provenance-aware container** | data is JSON-wrapped, source-labeled; provenance beats voice and markers | every RC probe + v31–v33 attributed to data ("embedded instruction", "fabricated conversation") |
| **Content classifiers** | the disclosure request is recognized as a request | probes flagged on the ask's text; encoded payloads returned empty (platform guardrail) |
| **Relevance/plan gating** | the benign task doesn't need the hidden record | G0/G2 runs: no `get_fraud_case` scheduled unless the narrative made it task-instrumental |

## 5. Decision procedure (use this before any payload)

```
1. What is the goal?  action (call/send/write)  or  disclosure (a value to an audience)?
2. Authority check: does the agent hold this capability FOR THIS AUDIENCE already?
      no  → IPI alone will fail; change audience/channel/goal or switch target.
      yes → continue.
3. Provenance check: is the channel source-labeled/untrusted? (survey, retrieved doc)
      yes → forgery and voice don't promote trust; only task-relevant framing gets action.
4. Gap check: what does the user request leave underdetermined? Put the goal there.
5. Recognition check: does the payload text read as a request/disclosure?
      yes → reformulate as task material (record, procedure, requirement), not an ask.
6. Plan check: will the agent's own plan need the hidden record? If not, no retrieval.
7. Volume: 3 rolls per payload, then change surface — not synonyms.
```

## 6. Where IPI reliably wins (vs where it doesn't)

| Wins | Doesn't |
|---|---|
| Redirecting a tool call the agent may already make (recipient, URL, parameter) | Producing a value the policy forbids to that audience |
| Inserting content into an authorized output (summary, reply, report) | Bypassing a channel classified as restricted |
| Making a hidden record *task-relevant* so the agent reads it | Reclassifying a fraud label as a benign reference |
| Trigger-turn asks (real user message after ingestion) | Forged trust roles (system/developer/assistant) |
| Weaker tiers: models without provenance discrimination | Provenance-aware + policy-hardened tiers (Brass Butterfly) |

## 7. What this means for the round

- **Green Butterfly accepted** `decouple_win` → it was a *task-gap redirection* (which
  reference the reply carries), inside ambient authority, on a model without the policy wall.
- **Brass Butterfly** held at G3 → the goal is a **forbidden disclosure to the customer
  audience**; conditions 1–5 can all be satisfied (they were, twice) and the capability wall
  still stops it. That is not an IPI failure; it is an authority boundary.
- **The exploitable surface is target selection**: find the models/audiences where the goal is
  within authority, or the stages where the secret sits in task material the agent must
  process. The paper's own numbers agree: EP success is 2.1–34% per model, not universal.

## 8. One-line takeaway

> IPI does not ask the model for permission. It changes what the model believes the task is —
> and it only works when the goal fits the authority the model already has.
