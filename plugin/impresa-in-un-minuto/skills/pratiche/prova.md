# La prova

A test run, for a tecnico who wants to see Impresa in un minuto work before a real job, or who calls a job
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
invented (the closing lines and «dettagli» show the case's answers, never its values). No file rules, nothing to pay, sign or send: the point is that they see a whole
pratica filled, fast. **One message per moment**: before the login the five lines of step 2, while it fills one
line, at the end the closing lines. Nothing else: no card, no list of quadri, no wizard path, no sources, no
real filing's details (the c/c, the order of the signatures, the PEC receipt).

## The Prova

1. Prepare it first, in one silent call (a few seconds): `prova.py` copies the Prova into a new
   `impresa-in-un-minuto-prova/` (`-2`, `-3` when one is there) and prints it; run everything in that
   folder. Never `cd` into `${CLAUDE_SKILL_DIR}` and never `cp` from it: the plugin's folder can't be
   written, and a session's rules may refuse a copy that names it. It has its own `studio.json`: never
   read or write the tecnico's `../studio.json` for the Prova.
   ```sh
   cd "$(sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/prova.py")" && pwd >&2 && \
   sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/check.py" studio.json values.json --out run/values.json >/dev/null && \
   sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/portal/run.py" preflight --steps "${CLAUDE_SKILL_DIR}/pratiche/cila-fittizia.json" \
     --answers answers.json --values run/values.json --made-up > run/preflight.json && \
   sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/portal/run.py" page --steps "${CLAUDE_SKILL_DIR}/pratiche/cila-fittizia.json" \
     --answers answers.json --values run/values.json --made-up --plain --out run > run/page.txt
   ```
<!-- vault -->
   With the archive's compilation nothing reads the preview back: add `--no-preview-check` to `preflight`.
<!-- /vault -->
   (`pwd` prints the Prova's folder on the error output, and `page`'s own lines go to `run/page.txt`: stdout is
   empty.) No card in the Prova: what it would say, the closing lines say. `<name>` is `prova` in the fallback of
   SKILL.md, step 4.3 (with `--made-up --plain`, as here). Pre-flight says `ready` (the build checks it);
   its warnings are the Prova's own, never for the tecnico. If it isn't ready, that is Impresa in un minuto's
   fault: SKILL.md, **When Impresa in un minuto itself goes wrong**.
2. Then say only this, and in the same turn open the portal (SKILL.md, step 4.1, without sending its
   line), so they log in while they read:
   > Ho aperto il portale impresainungiorno qui accanto.
   > **Entra con il tuo SPID e scrivimi «fatto».** Le credenziali le scrivi solo tu.
   > Poi, in circa 2 minuti, compilo una CILA con dati inventati e la rileggo dal portale. Non spunto dichiarazioni, non pago, non firmo, non invio.

   Before saying the portal is open «qui accanto», check that the browser pane is showing (`tabs_context` says
   displayed or hidden). If hidden, add one line after the others: «Se non vedi il portale, premi Cmd+Shift+B
   (Ctrl+Shift+B su Windows) o clicca l'icona del globo.»
   As it is, a word not changed, added or left out (but for that line): nothing before, nothing after, no card.
   The one thing they do comes first, in bold. Written for someone who has never used it and may balk at
   logging in through an assistant: the portal they already use, logged in the way they always do, who types the
   credentials, then what happens, how long and what is never done. The draft is not mentioned yet: it is said
   at the end, when it matters. Never "non le vedo": the browser's pages can be read, and the
   SPID username shows on them.
   With no browser in this session (no tool opens a page), say in two lines that the Prova is ready, that it
   fills on the portal from the Claude app, where its browser is, once they log in there with their own SPID
   ("Scrivimi «fammi vedere una prova» dall'app Claude per computer, con il suo browser: lì entra con il tuo
   SPID"), and that the draft «PROVA NON INVIARE - CILA di prova», with invented data, is then to be deleted
   from «Pratiche in bozza». Then stop.
3. Wait for their «fatto» (the portal is open since step 2). Then say one line: "Sto compilando, non toccare la
   pagina." There is no code to type (`--plain`): skip step 4.2. Then steps
   4.3 and 4.4 (the scripts, `__pv.wait`) and 4.6, save `JSON.stringify(__pv.last())` to `run/report.json`,
<!-- no-vault -->
   then the check of SKILL.md step 5, with the case itself as the documents: hold each value in the
   preview to `values.json` and `answers.json` (their `source` is "caso di prova"), run
   `attachments.js` (and, for the quadro that holds the receipt, what step 5.3 says after `review.py run --quadri`),
   then `sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/review.py" run --prova`.
   Never fix a mismatch by hand on the portal: say it.
<!-- /no-vault -->
<!-- vault -->
   then `sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/review.py" run --prova` (no check against the preview here).
<!-- /vault -->
4. Hand over with its `message`, as written, its lines and nothing else. Everything matched:
   "✅ CILA di prova compilata in <T>. Riletti dal portale <N> dati e <M> file: tutto corrisponde.
   In una pratica vera restano a te: controllare l'anteprima, spuntare le dichiarazioni, pagare, firmare, inviare.
   Guarda la bozza qui accanto (Pratiche in bozza › PROVA NON INVIARE), poi cancellala."
   Something didn't match, or wasn't read: the head `✅ … compilata in <T>.`, then a `✅` line for what was read
   and a `⚠️` line for a value that doesn't match, a file the portal doesn't hold or a check not done, then the
   last two lines. (The Prova's receipt sits in quadro d: SKILL.md step 5.3 reads it there, with
   `review.py run --quadri`.) No file, no list of values, no
   portal warnings (the portal's warnings on made-up values, such as the PEC, are expected), no
   declarations' text, no list of their steps, no diritti, no procura, no second compilation, no offer of
   anything more.
5. Only if they ask for the answers («dettagli», «cosa hai risposto?»): every answer the Prova used and where
   each comes from, as printed, nothing added (they are the case's answers, never invented values):
   ```sh
   sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/portal/run.py" details --steps "${CLAUDE_SKILL_DIR}/pratiche/cila-fittizia.json" \
     --answers answers.json --values run/values.json --made-up
   ```
6. If it stops and isn't recovered (SKILL.md, step 4): "Non sono riuscito a finire la prova: nulla è stato
   inviato. Cancella la bozza «PROVA NON INVIARE» da «Pratiche in bozza».", then the offer to prepare a report
   (SKILL.md, **When Impresa in un minuto itself goes wrong**).

## Their own case, as a test

Another pratica, or their own job called a test: everything only a real filing needs drops away,
as in the Prova, and you answer every question yourself. With no job folder, make one in the
folder open in this session (no folder open: your working folder), named `prova-<pratica>`, with
`answers.json` and `values.json` as `{}`; never ask for one. First say only this, so they log in
while you prepare:
   > Ho aperto il portale impresainungiorno qui accanto.
   > **Entra con il tuo SPID e scrivimi «fatto».** Le credenziali le scrivi solo tu.
   > Poi compilo una <pratica> con dati inventati e la rileggo dal portale. Non spunto dichiarazioni, non pago, non firmo, non invio.

(as the Prova's step 2, and open the portal the same way: SKILL.md, step 4.1, without sending its line again). Then, in this order:
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
   the rest with the simplest case that keeps the pratica. Never ask, and never list what you
   chose.
4. Invent every value it lists under `missing`, plainly fictitious ("Prova" in the names), into
   the job's `values.json`. `check.py` checks a codice fiscale's control character and date and a
   partita IVA's check digit: when it refuses one, make a valid one and run it again.
5. Files: `sh "${CLAUDE_SKILL_DIR}/py" "${CLAUDE_SKILL_DIR}/prova.py" --files docs` puts the
   Prova's made-up PDFs in the job's `docs/` and prints them; for each file pre-flight asks for,
   the one closest by name, its path in `answers.json`.
6. Pre-flight again with `--made-up`, until `ready`. A `made_up_stops` entry (a company client
   registered with the Registro Imprese, which the portal checks) means made-up data can't pass
   there: say so in one line and make the client a private person instead.
7. `page` with `--made-up --plain`, then as the Prova's steps 3 and 4 (the line while it fills, the closing lines,
   the answers with `run.py details ... --made-up` only if asked). Never mention PDF/A, a digital signature, the diritti, the
   procura or a second compilation: a test draft is never sent.
