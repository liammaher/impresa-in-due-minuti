---
name: portale-sue-cowork-test
description: Run the Portale SUE plugin's three Cowork tests with made-up data - whether the built-in browser runs the portal runner's scripts, whether a planimetria-sized file can be attached, and what one run costs - and write the results to a file. Use only when the user asks to run the Napoli Cowork tests.
---

# Napoli Cowork tests

Three questions decide how the Portale SUE plugin works in Cowork. Answer them with the CILA
rehearsal's made-up client (architetto Chiara Fittizia, client Luca Fittizio: no real
person, codici fiscali chosen at random) on the real portal, as a draft named "PROVA NON
INVIARE", never sent. `${CLAUDE_SKILL_DIR}` in a command is this skill's
folder, and the portale-sue-pratica skill's is its sibling, `${CLAUDE_SKILL_DIR}/../portale-sue-pratica` (should
a command show a `$` variable instead of a path, put this skill's base directory in its place). Keep notes as you go and write them all to `portale-sue-test-results.md` in the
user's folder at the end, even when a test fails.

## 0. Before anything

1. Record the time. Ask the user for the usage figure in Settings → Usage (the current
   session's %) and record it. Don't start until they give it.
2. Record `python3 --version` and list, by exact name, the browser tools you have. Note
   especially: a tool that runs JavaScript on a page, and a tool that puts a local file into
   a page's file input. Note which browser the browser setting uses (it must be the
   built-in one).
3. Copy `${CLAUDE_SKILL_DIR}/cila` into the user's folder as `portale-sue-test/` and work from there.
4. Check and pre-flight it:
   ```sh
   cd portale-sue-test
   python3 "${CLAUDE_SKILL_DIR}/../portale-sue-pratica/check.py" studio.json values.json --out run/values.json
   python3 "${CLAUDE_SKILL_DIR}/../portale-sue-pratica/portal/run.py" preflight --steps "${CLAUDE_SKILL_DIR}/../portale-sue-pratica/pratiche/cila-fittizia.json" \
     --answers answers.json --values run/values.json --made-up
   ```
   (`--made-up`: the test case's files are made up, so Napoli's file rules only warn.)
   Record both outputs. Pre-flight must say `ready`; if not, record why and stop.

## 1. Does the built-in browser run the runner?

1. `python3 "${CLAUDE_SKILL_DIR}/../portale-sue-pratica/portal/run.py" page --steps "${CLAUDE_SKILL_DIR}/../portale-sue-pratica/pratiche/cila-fittizia.json" --answers
   answers.json --values run/values.json --out run --plain`; record the sizes it prints.
   (Without `--plain` it tries to show a code in a window on the host: record whether
   that works from Cowork's sandbox, and what it says.)
2. Open `https://suap.impresainungiorno.gov.it/fnsuap/cmd/home` in the built-in browser and
   ask the user to log in with SPID. Wait until they're in. A page that says only "Forbidden"
   or lands on an error usually means another browser or session has a pratica open on the
   same login (the portal keeps one per login): record it and ask the user to close the
   other one, rather than clearing cookies.
3. Run `run/check.js` as one JavaScript call on the page, then what it names
   (`runner.js`, `steps.js`), then `run/run.js`, each file's text exactly as written.
   If a call fails with "await is only valid in async functions", the tool has no top-level
   `await`: wrap that script as `(async () => { ... })()` returning its last line, and record
   that you had to (a detail, not a failure).
   Record, for each call: whether it ran, what it returned, any error or size limit. A tool
   that refuses a script this size is the answer to this test: record its exact message,
   try `install.js` once in its place, and if that fails too, go to test 2.
4. Call `await __pv.wait(40000)` until `result` is `filled` or `stopped`; record how many
   calls that took.
5. Save `JSON.stringify(__pv.last())` as `run/report.json` and run
   `python3 "${CLAUDE_SKILL_DIR}/../portale-sue-pratica/review.py" run`. Record `result`, `error`, `at`, `wizard_seconds`,
   `total_seconds`. The Code tab's browser pane filled this same draft in 84 to 102 s on
   2026-10-28.
6. If it stopped: follow the portale-sue-pratica skill's recovery once (at most two fixes) and
   record each fix and whether the resume finished.

## 2. Does a planimetria-sized file get in?

`${CLAUDE_SKILL_DIR}/planimetria-3mb.pdf` is a valid 3 MB PDF, the size of a real set of drawings (the
portal takes up to 9.77 MB a file). A run carries files through the conversation, at most
256 KB, so this has to go another way.

1. Open the draft (`__pv.open()`), then its "Gestione degli allegati" section.
2. If you have a tool that puts a local file into a file input: use it to attach
   `planimetria-3mb.pdf` to the "Allegati liberi" slot (copy it next to the job first if the
   tool reads only the user's folder). Record the tool, the call, and whether the file's
   name then shows on the page with its size. Don't save anything else.
3. If you have none: record that, and whether the JavaScript tool could read a file from
   the user's folder in any way you have (don't invent one).
4. With a file tool, also into a box of the runner's own, read in the page. This says whether
   the runner can take any file, and a run's values, from a file you place without reading
   it. Run this as one JavaScript call:
   ```js
   (() => { const i = document.createElement("input"); i.type = "file"; i.id = "pv-probe";
     i.style.cssText = "position:fixed;top:8px;left:8px;z-index:99999"; document.body.append(i); return "ready"; })()
   ```
   put `planimetria-3mb.pdf` into `#pv-probe` with the file tool, then run:
   ```js
   (async () => { const f = document.getElementById("pv-probe").files[0]; if (!f) return { file: false };
     const d = await crypto.subtle.digest("SHA-256", await f.arrayBuffer());
     return { file: true, name: f.name, bytes: f.size,
       sha256: Array.from(new Uint8Array(d)).map((b) => b.toString(16).padStart(2, "0")).join("") }; })()
   ```
   and compare `bytes` and `sha256` with the file's own:
   `python3 -c "import hashlib,os,sys; p=sys.argv[1]; print(os.path.getsize(p), hashlib.sha256(open(p,'rb').read()).hexdigest())" planimetria-3mb.pdf`.
   Then remove the box: `document.getElementById("pv-probe").remove()`. Record each result.
5. Leave the draft as it is. Never press Invia, pagoPA or Firma.

## 3. What it cost

Ask the user for the usage figure again, record it and the time, and count your own tool
calls since step 0.

## The results file

Write `portale-sue-test-results.md` in the user's folder:

```markdown
# Portale SUE plugin: Cowork tests, <date>

| Test | Result | Detail |
|---|---|---|
| 0. Environment | | Python version, browser tools by name, browser setting |
| 1. Scripts in the built-in browser | pass / fail | each call; result, total_seconds, fixes |
| 2. A 3 MB attachment | pass / fail | the tool used, what the page showed |
| 2b. A file in the runner's own box | pass / fail | bytes and sha256 in the page against the file's |
| 3. Cost | | usage before and after, minutes, tool calls |

## Outputs
check.py, pre-flight and run.py page as printed; the report's result, error and at.
```

Then attach `portale-sue-test-results.md` and `portale-sue-test/run/report.json`, and tell the user to
send both back. The draft "PROVA NON INVIARE - CILA Cowork test" stays in their Pratiche in
bozza: tell them it's there, for them to delete when they like.
