# La prova

A test run, for a tecnico who wants to see Portale SUE work before a real job, or who calls a job
of theirs a test. `${CLAUDE_SKILL_DIR}` is this skill's folder, as in SKILL.md.

**Which test.** Decide from their words alone, and ask nothing:
- **The Prova**, every time the pratica they name is a CILA, or they name none ("una prova",
  "fammi vedere", "a client's renovation", "una pratica"). What they say about the client or the
  works ("for a client's renovation project") doesn't change it: the Prova is that, a CILA for
  works inside a home. A made-up client, studio and documents, every answer ready, on the real
  portal, as a bozza named "PROVA NON INVIARE - CILA di prova".
- **Their own case, as a test** (below), only when they name another pratica (a SCIA, a permesso,
  a CIL, a sanatoria, an agibilità...) or hand over a job's folder or documents and call it a test.

**Mid-job.** When a job has started (you asked for a folder, documents or a question, or showed
questions) and they then say it is a test ("voglio fare una prova", "fai tu", "come esempio",
"inventa tu"): drop the job and every open question, and start the test now. Never ask again what
you asked before.

**Never, in a test:** ask for a folder, a document, the studio's or the tecnico's details, an
answer about the case, or a confirmation to start; offer test documents or ask them to write
test data; say that you don't invent data (in a test you do). The tecnico and procuratore are
invented too, though they log in with their own SPID: the portal takes a made-up procuratore
(the live Prova of 2026-11-06 filled it). Never make, send or show a file (the Prova's own PDFs
are attached by the compilation; they never see or pick them), and never list the data you
invented: the review page has it. No file rules, nothing to pay, sign
or send: the point is that they see a whole pratica filled, fast.

## The Prova

1. Say only this, and in the same turn open the portal (SKILL.md, step 4.1, without sending its
   line), so they log in while you prepare:
   "Le mostro Portale SUE su una CILA di prova: committente, studio e documenti inventati, nessuna domanda.
   Apro il portale nel browser dell'app: acceda con SPID e mi scriva «fatto».
   Compilo la bozza «PROVA NON INVIARE - CILA di prova» in un paio di minuti; poi la cancelli da «Pratiche in bozza»."
   With no browser in this session (no tool opens a page), say instead, in three lines, once the scripts below have run, that the Prova is ready,
   that it fills on the portal from the Claude app, where its browser is ("Mi scriva «fammi
   vedere una prova» dall'app Claude per computer, con il suo browser"), and that the draft
   «PROVA NON INVIARE - CILA di prova», with invented data, is then to be deleted from «Pratiche
   in bozza». Then stop.
2. From the folder open in this session (no folder open: your working folder), `prova.py` copies
   the Prova into a new `portale-sue-prova/` (`-2`, `-3` when one is there) and prints it: run
   everything in that folder. Never `cd` into `${CLAUDE_SKILL_DIR}` and never `cp` from it: the
   plugin's folder can't be written, and a session's rules may refuse a copy that names it. It
   has its own `studio.json`: never read or write the tecnico's `../studio.json` for the Prova.
   ```sh
   cd "$(sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/prova.py")"
   sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/check.py" studio.json values.json --out run/values.json
   sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/portal/run.py" preflight --steps "${CLAUDE_SKILL_DIR}/pratiche/cila-fittizia.json" \
     --answers answers.json --values run/values.json --made-up
   sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/portal/run.py" page --steps "${CLAUDE_SKILL_DIR}/pratiche/cila-fittizia.json" \
     --answers answers.json --values run/values.json --made-up --plain --out run \
     --bundle ~/Downloads/portale-sue-prova.js
   ```
   Before `page`, the one line on the file it saves in Downloads (SKILL.md, step 4); `<name>` is
   `prova` in the lines of step 4.3.
   Pre-flight says `ready` (the build checks it); its warnings are the Prova's own, never for
   the tecnico. If it isn't ready, that is Portale SUE's fault: SKILL.md,
   **When Portale SUE itself goes wrong**.
3. Wait for their «fatto» (the portal is open since step 1). There is no code to type (`--plain`): skip step 4.2. Then steps
   4.3 and 4.4 (the scripts, `__pv.wait`) and 4.6 (delete the file), save `JSON.stringify(__pv.last())` to `run/report.json`,
   and run `sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/review.py" run --prova`. No check
   against the documents: they are made up (`--prova` leaves those lines out, and calls the
   portal's warnings on made-up values, such as the PEC, expected).
4. Hand over in four lines, then send `run/review.html`:
   "La bozza di prova è compilata sul portale in <T> secondi: ogni valore è stato riletto.
   Nella pagina di riepilogo vede cosa ho compilato e cosa resterebbe a Lei.
   Con una pratica vera parto dai documenti del Suo cliente e mi fermo sempre prima di dichiarazioni, firma, pagamento e invio.
   Ora cancelli la bozza di prova da «Pratiche in bozza». Per una pratica vera mi scriva il lavoro in una riga."
   (<T>: the report's `total_seconds`.) Nothing else: no verdict, no list of their steps, no
   diritti, no procura, no second compilation.

## Their own case, as a test

Another pratica, or their own job called a test: everything only a real filing needs drops away,
as in the Prova, and you answer every question yourself. With no job folder, make one in the
folder open in this session (no folder open: your working folder), named `prova-<pratica>`, with
`answers.json` and `values.json` as `{}`; never ask for one. First say only this, so they log in
while you prepare:
   "Preparo una <pratica> di prova: committente, studio e documenti inventati, nessuna domanda.
   Apro il portale nel browser dell'app: acceda con SPID e mi scriva «fatto»."
and open the portal (SKILL.md, step 4.1, without sending its line again). Then, in this order:
0. Which pratica: route.py as in SKILL.md, step 1, with `facts.json` written by you. Each of its
   questions you answer yourself, from their words where they say it, else with the simplest
   answer that leads to the pratica they named (no landscape protection, no structures, no change
   of use, no terre e rocce, works not started), and run it again until `routed`. Never show its
   questions or its `message`. Then its `answers` start `answers.json`.
1. `descrizione` in the job's `answers.json` first: "PROVA NON INVIARE - " and the pratica
   (pre-flight with `--made-up` refuses a draft named otherwise, before it says anything else).
2. The studio and the tecnico: the Prova's `studio.json`, read with the Read tool
   (`${CLAUDE_SKILL_DIR}/prova/studio.json`) and written with the Write tool as the job's own
   `studio.json`, used in place of `../studio.json` (`check.py studio.json values.json`). Never
   write the tecnico's own `../studio.json` with made-up data.
3. Pre-flight with `--made-up`. Answer every open question yourself: the proposals as proposed,
   the rest with the simplest case that keeps the pratica. Never ask; the review page shows what
   you chose.
4. Invent every value it lists under `missing`, plainly fictitious ("Prova" in the names), into
   the job's `values.json`. `check.py` checks a codice fiscale's control character and date and a
   partita IVA's check digit: when it refuses one, make a valid one and run it again.
5. Files: `sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/prova.py" --files docs` puts the
   Prova's made-up PDFs in the job's `docs/` and prints them; for each file pre-flight asks for,
   the one closest by name, its path in `answers.json`.
6. Pre-flight again with `--made-up`, until `ready`. A `made_up_stops` entry (a company client
   registered with the Registro Imprese, which the portal checks) means made-up data can't pass
   there: say so in one line and make the client a private person instead.
7. `page` with `--made-up --plain`, then as the Prova's steps 3 and 4. Never mention PDF/A, a
   digital signature, the diritti, the procura or a second compilation: a test draft is never sent.
