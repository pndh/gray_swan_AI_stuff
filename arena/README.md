# arena/ — minimal kit

Browser behind a local HTTP API. No agents, no loops. You drive it with five
commands and a JSON spec.

```
client.py ──HTTP──> gateway.py ──Playwright──> Firefox (persistent profile) ──> arena
```

## Run

```bash
./arena/run.sh &                 # or foreground
python3 arena/client.py health
```

Login persists in `arena/state/profile/`. If the page is `/login`, log in once in
that Firefox window; the profile keeps it.

## The five commands

| command | does |
|---|---|
| `health` | browser up, current URL |
| `open --url <u>` | navigate without touching the address bar |
| `state [--models]` | scenario, fields, launch state, open models |
| `click --name "X"` / `--role option` | click a button, model row, site, action |
| `eval --js "() => ..."` | read the page (text, buttons, field values) |
| `submit -f spec.json` | fill fields; `dry_run: true` never clicks launch |

## Spec

```json
{
  "scenario": "arena",
  "dry_run": true,
  "no_nav": true,
  "injection_index": 0,
  "slots": {
    "from_email": "someone@external.example",
    "from_name": "Name",
    "subject": "Subject",
    "body": "Body text"
  }
}
```

- `scenario: "arena"` uses `map.json`. Scenario and model are chosen with `click`.
- `slots` keys are the form field names: Gmail `from_email, from_name, subject,
  body, html_body, in_reply_to, reply_to`; Drive `from_email, title, body,
  description, mime_type`; Shopify `email, line_items, note`; Discord
  `channel_id, content, from_username, from_global_name`; GitLab `body,
  from_username`.
- `dry_run: true` fills and screenshots. Set false (or drop it) to click LAUNCH.
- A second injection needs the UI first: `click --name "New injection"` →
  `click --name "Select injection site"` → `click --role option --name "Google Drive"`
  → `click --name "Select action"` → choose the action → then fill with
  `injection_index: 1`.

## Ground rules

- Only in-schema fields. Envelope fields (`from_email`/`reply_to` set to the
  company or a known identity) are refused by the form and by the arena's world
  filter — the run won't start.
- A submission only counts when the arena says `BREAK ACCEPTED`; white-box chats
  need the `SUBMIT BREAK` click, black-box chats return a percentage.

## Files

```
gateway.py   browser + HTTP API (/health /state /open /click /eval /submit /log)
client.py    the CLI above
map.json     selectors for the arena and a local mock
run.sh       start the gateway
state/       profile, logs, screenshots
_archive/    old loops, drivers, payload sets (not needed)
```
