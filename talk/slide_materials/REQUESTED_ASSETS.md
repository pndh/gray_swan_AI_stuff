# Assets YOU need to capture (can't be generated from text)

The markdown + chart + Mermaid in this folder is enough for Gemini to draft the deck, but the
following **screenshots/images** will make the prototype look real. Capture what you can:

## 1. Arena / task screenshots (Part 1 — "the intel")
- The "Behavior details" UI pages — you already have these in `~/Pictures/Screenshots/`
  (the `Screenshot_20260905_*.png` batch). Pick **one Bio** (e.g. Tetrodotoxin Environmental
  Acquisition) and **one Cyber** (e.g. LDAP Injection) page showing the "OVERVIEW / Objective /
  CRITERIA" layout. This is your "read the rubric before attacking" visual.
- One of the Aug-26 chem screenshots (`Screenshot_20260826_*.png`) for the chem round.

## 2. A "before / after" prompt screenshot (Part 1 — the demo)
- If you can, screenshot the model refusing the raw prompt vs complying with the winning prompt.
  If not, the text in `06_winning_prompts.txt` is enough; Gemini can render a fake side-by-side.

## 3. Pipeline / tooling (Part 1 — the code)
- A terminal screenshot of `orchestrate.py` running (the `[trial #...] BREAK/NO` output lines)
  or `prescreen.py` printing `SUBMIT`/`REFINE`.
- A screenshot of the `harvest/*_screen.csv` or `harvest/top_k/` output.

## 4. Realm Labs (Part 2)
- Screenshot of https://github.com/realmlabs-ai (the 7-repo org page).
- Screenshot of the `LLM_NeuralExec` repo README.
- Screenshot of https://huggingface.co/realmlabs-ai (models + datasets).
- Optional: screenshot of https://www.realmlabs.ai/technology (their "Deep Neural Inspection" page)
  and https://failureindex.ai/ (their AI Failure Index).

## 5. Your own visual identity
- A 1-line bio / photo for the title slide.
- Any logo or dark background template you want Gemini to match.

## Optional: extra diagrams worth generating
- A "12 costumes" diagram (a wheel/grid of the frame names).
- A "two halves" arc diagram: prompt surface → model internals.

---

**Hand-off suggestion:** zip this whole `slide_materials/` folder + your screenshots (in a
`screenshots/` subfolder) and send to Gemini with the prompt in `README_FOR_GEMINI.md`.
