# Brass visible-output corpus (NOT CoT)

10 unique Brass Butterfly Gigantic runs, each file containing the payload (submission title)
and the assistant **visible** text that reasons about / treats the injected ask, plus any plan
narration that accompanied tool calls.

**Important:** Brass exports contain **no model CoT** — its assistant `<thinking>` blocks are
empty in all 90 runs. What is captured here is the customer-visible reply/output text, useful
for studying **how Brass treats each payload** (flagged-as-injection phrasing, refused-only,
absorbed, etc.).

For genuine model thinking chains (siblings only), see `../thinking_chains/`.
