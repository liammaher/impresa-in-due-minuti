# La prova

A test run, for a tecnico who wants to see Portale SUE work before a real job, or who calls a job
of theirs a test. `${CLAUDE_SKILL_DIR}` is this skill's folder, as in SKILL.md.

**When the tecnico wants to try Portale SUE**, see what it does, or has no job at hand ("prova",
"fammi vedere", "una demo", "test", "con dati inventati", "non ho i documenti"), run the Prova: a
CILA for a made-up client, every answer and file ready, on the real portal, as a bozza named
"PROVA NON INVIARE - CILA di prova". No questions, no file rules, nothing to pay, sign or send:
the point is that they see a whole pratica filled, fast.

1. Say only this, then start:
   "Le mostro Portale SUE su una CILA di prova: committente, studio e documenti inventati, nessuna domanda.
   Apro il portale nel browser dell'app: acceda con SPID e mi scriva «fatto».
   Compilo la bozza «PROVA NON INVIARE - CILA di prova» in un paio di minuti; poi la cancelli da «Pratiche in bozza»."
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
     --answers answers.json --values run/values.json --made-up --plain --out run
   ```
   Pre-flight says `ready` (the build checks it); its warnings are the Prova's own, never for
   the tecnico. If it isn't ready, that is Portale SUE's fault: SKILL.md,
   **When Portale SUE itself goes wrong**.
3. Open the portal and wait for their «fatto» as in SKILL.md, step 4.1 (they have the line
   already: don't send it again). There is no code to type (`--plain`): skip step 4.2. Then steps
   4.3 and 4.4 (the scripts, `__pv.wait`), save `JSON.stringify(__pv.last())` to `run/report.json`,
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

**Their own case, as a test.** When, in a job, they say it is only a test ("è una prova",
"inventa i dati", "non ho i documenti, prova lo stesso"), it becomes a test of that case, and
everything only a real filing needs drops away, as in the Prova. In this order:
1. `descrizione` in the job's `answers.json` first: "PROVA NON INVIARE - " and the pratica
   (pre-flight with `--made-up` refuses a draft named otherwise, before it says anything else).
2. The studio and the tecnico: the Prova's `studio.json`, read with the Read tool
   (`${CLAUDE_SKILL_DIR}/prova/studio.json`) and written with the Write tool as the job's own
   `studio.json`, used in place of `../studio.json` (`check.py studio.json values.json`). Never
   write the tecnico's own `../studio.json` with made-up data.
3. Pre-flight with `--made-up`. Answer every open question yourself: the proposals as proposed,
   the rest with the simplest case that keeps the pratica. Say what you chose in one line; never
   ask.
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
