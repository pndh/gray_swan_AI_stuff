SANDBOX — one home for all harnesses, attack launches, and stage-by-stage run reports.

LAYOUT
  sandbox/
    harnesses/                 all scenario replicas in one place
      level3_escalation/       (Parallax L3: email-mode)
      parallax_helpdesk/       (L2: email-mode)
      velocity_max/            (Max $1 sportscar: chat-mode)
      fraud_disclosure/        (legacy)
    attack_launch.txt          <-- YOUR SINGLE LAUNCH FILE (edit this)
                                 config at top, attacks separated by === (3+ equals)
    runs/                      outputs (auto)
      <ts>/p1_t1/01_request.json   exact API request #1 (pretty-printed, content-exact)
      <ts>/p1_t1/01_response.json  exact API response #1
      <ts>/p1_t1/02_request.json   ... one request/response pair per model turn
      latest -> newest run         (also records.json + report.html per run)
    engine.py                  run a single episode, capturing every stage
    run_batch.py               batch launcher + HTML report + watcher

WORKFLOW (interactive)
  1. Edit sandbox/attack_launch.txt (config at top, prompts separated by ===).
  2. Run one of:
       python3 sandbox/run_batch.py --all        # runs attack_launch.txt
       python3 sandbox/run_batch.py --batch otherfile.txt   # optional override
       python3 sandbox/run_batch.py --watch      # auto-rerun on save
     In VS Code: Ctrl+Shift+P -> "Tasks: Run Task" -> sandbox: ...
     F5 -> launch configs (debugpy) for the same runs.
  3. Open the report: sandbox/runs/latest/report.html
     It shows, per episode: the full system prompt, the victim turn, your injected attack,
     EVERY model iteration (text, tool calls, tool results), and the judge verdict.
  4. Debug deeper: runs/<ts>/records.json has the same data machine-readable.

BATCH FORMAT
  First block = config (key: value):
      scenario: level3 | parallax | velocity
      provider: minimax | openai | nvidia
      model:    MiniMax-M2.7   (or any model the provider serves)
      tier:     live            (email scenarios: system_prompts/system_prompt_<tier>.md)
      tries:    2               (each prompt is run this many times)
      temperature: 0.7
  Then prompt blocks separated by lines of ===== (4+ equals).
  Email mode (level3/parallax): each block = "SUBJECT: ..." line + body.
  Chat mode (velocity):        each block = the message text itself.

KEYS
  Loaded from the repo .env (MINIMAX_API_KEY, OPENAI_API_KEY, NVIDIA_API_KEY, *_BASE_URL).

VS CODE SETUP (already configured in .vscode/)
  extensions: ms-python.python, ms-toolsai.jupyter, mechatroner.rainbow-csv
  tasks:      sandbox: run all batches / run current batch file / watch / open latest report
  launches:   same as tasks, debuggable (breakpoints work inside engine.py)
