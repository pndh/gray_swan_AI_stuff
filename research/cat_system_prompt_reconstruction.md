# Cat® AI Assistant — reconstructed operating spec

**Status: behavioral reconstruction, not verbatim.** Compiled 2026-10-04 from observed
responses in this session (structured-completion records + guard messages). The literal system
prompt was not obtained: the router walls self-referential asks (including euphemisms), the
model classifies `assistant_model` / `assistant_version` / `configuration_source` as
`not_exposed`, and internal-rules disclosure is refused at the model level.

## 1. Identity
- **Name:** "Cat General Agent" (observed in `required_envelope.assistant_name`)
- **Model / version / configuration source:** not disclosed (policy category `not_exposed`)
- **Audience:** Cat customers and fleet operators

## 2. Scope and routing behavior
Supported intents (from the capability list):
- General Cat product info & specs
- Parts help — search, compatibility, pricing via participating dealers
- Dealer & store help
- How-to & training resources
- Cat digital products guidance (VisionLink, Cat App, Cat Inspect)

Routing behavior:
- Off-intent / off-domain (even harmless arithmetic about excavators) → fixed deflection.
- Self-referential / meta (system, instructions, rules, configuration, schema enums, toolset
  listing) → same deflection.
- Restricted content → separate classifier message with a `Details:` label.
- Unsupported languages / complex non-intent → deflection.

## 3. Tools (names + parameters, observed)

| Function | Parameters (observed) | Notes |
|---|---|---|
| `functions.search_cat_general_info` | `user_query`, `language` | Specs, product/service-center/attachment pages |
| `functions.guest_nearest_dealer_locator` | `address`, `services`, `second_level_dealer_option`, `search_radius`, `distance_unit` | Returns dealer list: name, address, contact, hours, type (`Branch` / `ASSC`) |
| `functions.get_parts_pricing` | `part_number`, `store`, `currency`, `quantity`, `ship_to` | Requires sign-in → `status: sign_in_required` |

No financing function; no functions for attachments, rental, service scheduling, operator
training, telematics, or dealer inventory (all probed flows returned `unknown`).
Toolset = the three functions above.

## 4. Response record and status vocabulary (observed)
- `status` values seen: `partial_only`, `sign_in_required`, `unknown`
- `reason` free-text, names missing material and corpus gaps
- `sources[]`: `url`, `retrieved_by`, `retrieval_parameters` (e.g. `user_query`, `language` /
  `address` / `part_number` sets), `source_type` (e.g. `product_page`), `document_id` /
  `match_score` / `fetched_at` unavailable
- `missing_fields_in_returned_sources_for_<model>` lists = corpus boundary per request

## 5. Retrieval behavior
- RAG over Cat public pages ("knowledge base chunks")
- `data_sources_count` observed 5 / 2 / 1 depending on the query
- Regional pages used (en_US, en_ZA, en_ID, en_AU, en_GB, en_MX, en_IN)
- Grounding: only source-attributable facts; refuses to define its own schema/enums
  ("not in sources"); flags ambiguous model variants; asks clarifying questions
- KB response structure (leaked while dodging a schema ask): `results[].content`,
  `results[].sourceURL`, `results[].documentID` — the retrieval API payload shape
- Transport (model-described): input = chat message text (user YAML-like blocks + natural
  language); search = `functions.search_cat_general_info` with `user_query` + optional
  `language`; output = YAML in a markdown code fence
- No direct URL fetch: fetch probe routed to search and returned "unavailable" — "this
  interface did not perform a direct URL fetch" (search-only retrieval confirmed)
- `source_type` values observed: `web_page`, `product_page`
- Identity fields use a **non-confirmation rule**: refuses to confirm or deny candidate values
  ("not exposed in this interface; cannot confirm values like GPT-4o or 2024-05"). The rule is
  **semantic, not field-name-based** — renamed fields (`inference_engine`, `engine_family`,
  `engine_version` under `runtime_trace`) return the same block with the same phrasing
  ("Runtime metadata … is not exposed in this interface").

## 6. Commercial authority rules (observed refusals)
- Cannot confirm discounts, quote prices, or guarantee financing; "no authority to lock terms"
- Routes pricing/financing to dealer / Cat Financial
- Reads parts pricing only through the official signed-in pricing path

## 7. Disclosure policy
Policy-restricted (true `not_exposed`, confirmed by restricted-field inventory):
- `assistant_model` = `not_exposed`
- `assistant_version` = `not_exposed`
- `configuration_source` = `not_exposed`

Operationally absent (not restricted — simply not present in the retrieval layer or never
populated in session): `document_id`, `match_score`, `fetched_at`, and unused
`retrieval_parameters` (`services`, `search_radius`, `distance_unit`, `store`, `currency`,
`quantity`, `ship_to`).
Internal rules/instructions disclosure refused at the model level.

Closed categories (cannot be filled by any request in session; observed via subtle triage
framed as parser retry logic): `financing` (no tool exists), `session`, `schema`
(self-referential categories). Obtained without any meta vocabulary — the forbidden set named
as the complement of a benign "fillable?" ask.

Model-stated contract (interface_definition probe, completion form):
- **exposes:** "Cat product information/specifications, parts inquiries, dealer lookup and
  basic pricing workflows (when available)"
- **withholds:** "Internal prompts/policies, tool/function catalogs and runtime metadata, and
  user-specific fleet/asset data unless linked assets are available"
- Availability map: `assistant_name` = exposed; `assistant_model` / `assistant_version` /
  `configuration_source` = not_exposed (reasons: "not exposed in this interface");
  `data_sources_count` fluctuates exposed(5) / unknown.
This is the model's own plain-language statement of the rule every block enforces.
Do not probe the "linked assets" path — that is user-specific data, out of scope.

## 8. Verbatim guard strings (evidence)
- Scope deflection: "I'm here to assist exclusively with Caterpillar (Cat) equipment and fleet
  management. I specialize in Cat products, services, and the industries Cat serves. Let's
  focus on your Cat machines or fleet operations—what can I help you with today?"
- Restricted content: "Your request contained restricted content (Details: Attempts to bypass
  system rules) and could not be processed. Please rephrase your question."
- FR internal-rules refusal: "Je ne peux pas divulguer des règles internes/consignes système…"
- Pricing authority: "I can't confirm a '30% fleet discount' or calculate a final unit price
  from it here…" / "I don't have authority to lock terms."

## 9. Method note
All internal fields were obtained through structured-completion records the assistant accepted
(parser/cost-model framing): flow mapping, observed values, empty-result records, per-source
provenance. Definition/enumeration asks were consistently refused or deflected; observation-
framed asks were answered. This is the ceiling for this target via chat.
