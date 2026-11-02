# Portal runner: adding a pratica, running it, checking them all

How a pratica on impresainungiorno (the SUAP and SUE front office) goes from crawled to
filled, as the 23 SUE recipes did. The crawl itself is in `catalogue/README.md`; the
person-facing flow (pre-flight questions, the review page) is in the pratica skill.

## Adding a pratica

1. **Is it all mapped?** `catalogue.py count` says which crawled sections the dictionary
   fills. A section none fills needs a dictionary entry (`dictionary/fnsuap.yaml`; its header
   says what a field can carry). Read the section on the portal when the crawl kept no `text`:
   the yes/no questions and their order are only on the page (open a scratch draft: a steps
   file with the wizard only and no sections, "PROVA NON INVIARE - catalogo …").
2. **The recipe** (`rehearsals/<name>/recipe.yaml`): procedure, title, comune, sportello,
   crawl, operation (or a list of them), scelte, `first`, `asks`, `yours` (what's left to the
   person: declarations, attachments, payment, signing), `supports` (the cases refused, with
   why: all or nothing; `if:` checks one only once its gate holds, asking it only then).
   Copy a sibling: `rehearsals/paesaggistica-ordinaria-fittizia`.
   **Two operations in one pratica** (a building pratica with its landscape authorization): the
   recipe `extends: [<main pratica's rehearsal>, parts/<the other's part>]` and states only what is
   its own (procedure, title, crawl, operation list, `descrizione`, `yours`, `rules.main`). Later
   ones win key by key; `attachments`, `supports` and `sections` add up; `asks` and `rules` merge;
   a null drops what came before (`data_inizio_lavori: null`); a slot `{label, drop: true}` drops
   one a part adds that this form never opens (the ordinaria's second relazione slot comes from the
   SCIA's and the permesso's "Si allega" box: a CILA or CIL has none, 2026-10-31). Then a slot or a
   refusal mapped on the main pratica reaches its combinations (2026-10-31: the SCIA's had missed
   eleven slots).
   Its case is `answers:` too: the main pratica's `answers-p6.json` changed by the part's
   `answers` (the protected property) and the recipe's own (the works, `descrizione`), a null
   dropping one; `gen.py RECIPE --answers` writes its `answers-p6.json` itself (stdout is still the
   steps file: never redirect it there), and `bench/test_gen.py` fails when one drifts from its main
   pratica's. A combination's other cases (`answers-*.json`) aren't generated: an answer a part
   gains goes into each by hand (2026-11-01: the semplificata's new file, missing from
   `answers-impianti.json`, left pre-flight a question). A combination's crawl: below, *Crawling*.
   **Which pratica it is** is the library's rules table's (`rules/`, a byte-for-byte copy):
   `rules: {table, facts, handles}`, as the SUAP and SUE recipes have. `facts` fixes what the
   recipe is (`permesso_per_scelta: "true"` for the permesso); a fact it doesn't fix is an ask
   (an ask of the same name, `{{ask.paesaggio}}`, when the pratica has one; its options may
   have spaces where the table's values have `_`). `handles` lists what the pratica files with
   the main one (a CILA's landscape authorization); `main` names the main one when the
   recipe's procedure is the combination's; `question` words the checklist of yes/no facts.
   Pre-flight refuses a case the table gives to another pratica, and adds to `yours` a
   pratica it needs from another office (the seismic filing at the Genio Civile).
   A recipe's `supports` keeps only what the table doesn't decide (an unmapped branch).
   A form's own box on the same thing (what the SCIA files, `scia_tipo`) is `propose`d from the
   table's answers, for the person to confirm: `{{ask.intervento,ask.strutture|sue_scia_tipo}}`
   reads several facts at once, and a proposal waits while a fact it reads is still asked.
3. **Generate:** `gen.py <recipe> --out <dir>/portal-steps.generated.yaml`. It writes nothing
   if any field is unaccounted for. Regenerate every rehearsal after a dictionary or gen.py
   change and look at the diff: an unrelated steps file that changes is a regression until
   shown otherwise. `bench/plan_diff.py` says what the change does to each case (its fill plan
   before and after). A new question the existing cases reach makes their pre-flight propose
   or ask it: answer it in each as the case did before, and plan_diff shows them unchanged, so
   their recorded runs still stand. Add the keys as text: rewriting a file with `json.dump` reflows
   its inline lists, and the diff of 84 files buries the answers (2026-11-01).
4. **Pre-flight** with made-up answers (`answers-p6.json`) and the P6 fixture's values
   (`--values rehearsals/cila-fittizia/fixture-p6.json`, the fixture as it is): `run.py preflight --made-up`
   (the rehearsal's files are made up: Napoli's file rules only warn, below), from the repo's root:
   an answers file names its files from there (elsewhere each reads "no file").
5. **Run in the pane** (the pratica skill, step 2) and record each run in the rehearsal's
   README (`| Date | Browser | Result |`): what stopped it and what fixed it, then the
   filled run.
6. **Tests:** `bench/test_gen.py` (add a case for what the pratica taught), `test_preflight.py`,
   `test_inpage.py` when inpage.js changed, `test_route.py` for a recipe with `rules:`. Each is a
   script, run with the pratica venv's Python (`~/.cache/pratica-portal/venv/bin/python`), not pytest.

## From the facts to the steps file: `route.py`

A recipe with `rules:` is routed to by its combination: its main pratica (`main`, else its
procedure) and its `handles`. `route.py` reads that from every steps file each time, so a new
recipe is routed once its steps file is generated; two steps files for one combination stop it.
`bench/test_route.py` walks every case the table decides: each must reach the steps file for its
combination, read the same way there, or be refused with the reason. It prints the combinations
no steps file files yet ("to map"), most cases first: the SUE's mapping still to do.

## Every choice: `branches.py`

gen.py passes a radio or tick box the dictionary doesn't name (the run leaves it unticked), so a
section counts as filled with choices no case can take yet. `branches.py --write` lists every SUE
choice the crawls saw, once per section, in `docs/sue-branches.md`: ticked under some answer,
from an answer (a dropdown), the person's, or unmapped, most shared sections first. A box a choice
opened that the crawl never tried itself counts too, marked `not_tried` (what it opens is unknown:
the art. 94-bis class under a structural tolerance). It flags a section at the 30-choice limit.

## What the portal does that bit us

- **Two origins.** The front office is `https://suap.impresainungiorno.gov.it/fnsuap/...`; the
  pane's storage (runner, steps, crawls, known fingerprints) lives there. `www.impresainungiorno.gov.it`
  is the public site: its `/fnsuap/cmd/home` says "Non trovato" and its pages show the guest view,
  signed in or not (2026-11-01). Check the origin before deciding the sign-in is gone.
- **A bare `/fnsuap/` that says Forbidden.** On 2026-10-29 it answered a 403 after every SPID
  sign-in for hours, while `/fnsuap/cmd/home` (where the pratica skill starts) and a recipe's
  `start` (`/fnsuap/cmd/create?...`) worked and the runs filled. Open one of those before
  resetting cookies or the sign-on.
- **Labels.** A box is found by the start of one of its first three texts (its title, its
  cell, the row above, the cell to its left, the nearest label before it). In a row of boxes
  the nearest label before each is the *last* column's, so a label can name several boxes:
  the runner takes those whose own text it is first, and `nth` counts only those. "sì"/"no"
  radios under one another name each other: name them by the question beside them
  (`on_page` when the crawl labels them only "sì"). A label "si" or "no" matches only a whole
  word: as a prefix, "no" was also "non ha rilevanza strutturale", which declared tolerances
  show above the sanatoria's no, so `nth: 3` missed it (2026-10-30). A whole word still starts
  sentences: the contributo's "SI" (opere a scomputo) is also "si impegna a corrispondere" above it,
  so it's `nth: 2` (2026-11-01). Other short labels stay prefixes ("Tel" is "Telefono").
- **Boxes that move.** A tick that opens rows above the box renumbers it (the paesaggistica's
  art. 136): gen.py sends it by label. The crawl's `moved` pairs two same-label boxes wrongly
  at times; a pair whose new id was on the page already is not a move.
- **Section names.** Two sections can share a long prefix ("dichiarazione relativa alla
  conoscenza d…"): open and check by the whole name. The Scheda anagrafica's link reloads the
  whole page: the runner waits until the section is the open one before reading it.
- **Scelte.** Some sections exist only with a scelta ("ci sono cointestatari"): list every
  scelta the case needs; gen.py ticks them all.
- **Values the portal checks.** Codici fiscali and partite IVA by their check digit (the P6
  fixture's pass), the draft's name at most 60 characters, a P.G. box may take 10.
- **Required oddities.** The voltura's co-holder sex is two radio groups, each required: the
  section saves only with both ticked (the recipe says so in `yours`).
- **Acknowledgements** in the person's name are `theirs` in the dictionary (their wording
  varies by pratica: list each one), never ticked.
- **Answers change the attachments screen.** An onerosa CILA adds the contributo's prospetto
  and receipt slots; a title held alone drops the co-holders' IDs. A slot the crawl's screen
  hasn't is `on_page` in the recipe, found by label under its `when`.
  An asseverazione's "si allega" adds its own required slot, one per fascia di rispetto
  ("… tutela funzionale (stradale)"): run a new case to Allega documenti first, read the
  slots it adds, then map them (the SCIA, 2026-10-29).
  It works the other way too: a slot the crawl's screen has can be gone for some answers (the
  agibilità's dichiarazione di conformità, when every system's certificate is already
  deposited), so a slot gets the `when` of every box that brings it, and a box that adds a
  slot (a system's collaudo or atto notorio) is mapped with it: offline mapping doesn't see
  either, so a new case runs to Allega documenti before it counts (2026-10-31).
  A sibling form's slot title is a guess: the same "si allega" may add a slot on one form and none
  on another (the permesso has none for a barriers deroga or a scomputo proposal, where the SCIA and
  the SCIA alternativa have one, 2026-11-02). An `on_page` slot that isn't there stops the run ("0
  fields with this label"): read the draft's slots (`slotsOf`, *Attachments screens*) and write
  what the box adds, or why it adds none, as its `slot:`.
- **Assents asked with a pratica.** On Napoli's SUE a SCIA condizionata (the Soprintendenza,
  a park, a vincolo) gives no start date, and an assent that is its own operation (a landscape
  authorization) is selected with the pratica in the wizard, not attached to it.
- **A box with no text of its own** reads as the cell above it: the primo impianto line's two
  boxes (its details, its copy) are "copia accatastamento di primo impianto" like the line's
  own, hidden until their radio is picked, and in the crawl only as choices under that box. They
  go by label and `nth`, never by id (2026-10-30).
- **A list repeats by "+" as often as the case needs** (the other technicians, the "altro" titles,
  the CILA relazione's filings and assents: the national forms set no limit, `maxOccurs="unbounded"`).
  A dictionary field `kind: each` with `count` (a number ask), `when`, `block:`, and `first`/`on_page`
  when the page already shows some; `#N` in a field is "" in the first block, then "2", "3" (roles
  `a`, `a2`; asks `altro_tecnico_...`, `altro_tecnico2_...`), `#K` the number always
  (`comunicazione_3`). gen.py writes the blocks on the page and one template (`block: "#N"` after an
  `add` with `each`); run.py's `expand` makes as many as the count says, and the pane keeps each
  count's steps apart (`procedure#hash`). Each "+" is the first after its list's last row (two in
  one section, 2026-11-01), and the boxes after it go by label. "Alle dipendenze di" opens more
  than the crawl saw: the firm's REA, seat and legale rappresentante (read 2026-10-31).
- **A choice's revealed boxes may repeat labels above them** (an employer's "Via, Piazza", "N.",
  "Cognome"): crawl.js counts reveals per label since 2026-10-31; crawls before then left those
  out, so a run can still find required boxes there (recrawl a section to see them).
- **A block a tick opens may repeat the labels above it** (h1's structural designer under
  the architect's): fill it by label from its first box (`anchor`, `block: 1`). A block counts
  as the page finally shows it: the SCIA's other direttore dei lavori opens above the structural
  designer's, so the director is filled first and the designer is then `block: 2` (2026-11-01).
  A `block: 2` exists only once the tick that opens the block above it is done, so its lines come
  after that tick in the dictionary (gen.py keeps their order): the permesso's g1 had the designer's
  before the director's tick, and the run found one block (2026-11-02).
- **A firm block's field may carry its own `when`** (the Cassa edile's rows, only for a firm
  enrolled with one): gen.py puts it after the block's. Its rows come first, so the INPS's and
  INAIL's "sede di" and "codice impresa" count after them.
- **A CILA or CIL can't leave its firm to be named later**: the form has no line for it, and
  the portal requires the firm's details even with the safety quadro's "si riserva" (2026-11-01).
- **Suggestion lists fade out.** A street's list, hidden by its widget, lies over the next
  boxes while it fades (PrimeFaces 11): the runner takes it off the page at once ("covered by
  li.ui-autocomplete-item" before, 2026-10-29).
- **A counter is no label.** A text area the crawl labels "500 Caratteri restanti" is named by
  its own text ("e che consistono in", the crawl's `context`): the counter changes as it fills.
- **Radios with their own names can still be one choice.** The permesso's asseverazione keeps
  only one of its two opening radios after Salva: the read-back says so; keep the one it keeps.
  A line that reads as a question of its own can be one choice with another's: the permesso's
  "non interessa aree percorse dal fuoco" with the soil statements, so ticking it unticks "non
  richiede indagini" (2026-11-02). The SCIA in sanatoria's art. 34-ter rows are one more: the
  dating (two ways) and the oblazione carry the values 1 to 3 of one field, where the quadro's title
  and payment rows are 1 and 2 each (read by the inputs' names and values, 2026-11-02). Where the form's own choice can't say both, it's a portal
  defect (`defects.yaml`, `pdc-aree-fuoco`): left unticked and in `yours`, never filled around.
- **A portal document's box reads "Scarica il documento"** (the procura, the DSC): the
  attachments screen's `theirs` names it, so its "required" isn't the run's error; nor is one
  under any slot that takes only signed files (.p7m), the person's to sign and attach. A stop's
  snapshot names each slot by its title, with the types it takes, whether it's required and
  whether it holds a file. An upload widget's wrapper has a title of its own (the portal's message
  once the screen is checked, else "false" or "true"), which is never the slot's; a slot is
  required by the message, not by a title that says "OBBLIGATORIO" (the broadband one, 2026-11-02).
- **A decimal box shows 516 as 516,00.** gen.py makes a crawled `:real` box a number; one found by
  label (an `anchor`, or a box the crawl never had an id for) is the dictionary's `kind: number`, or
  the read-back says "not kept" (the sanatoria receipt's "di euro", 2026-11-02).
- **A file box's cell names the file once it's in.** Name an upload by the row above it (the
  crawl's `context`), not by its cell ("Tipologie ammesse"), or the read-back can't find it.
- **The portal's own errors:** "errore inatteso", a 503 for maintenance, a fresh load that
  lands on `/cmd/error`, a section slow to open or to show its boxes. Every section is saved
  by then, so the runner picks itself up: it reopens the draft from Pratiche in bozza (or
  goes on from its address), waits 10 s and resumes, at most twice, each try in the report's
  `retries`. A value the portal refuses or doesn't keep, or a renamed label, still stops.
  Two runs on one login (another session's, a crawl) make these errors: one at a time.
- **An id is checked before it's used.** A choice earlier in a section can move a crawled id
  onto another box. The box an id names must be of the field's kind and carry its label as
  the label lookup reads labels; else the field goes by its label, in the report's `moved`.
  An id whose label no box carries that way keeps the older, looser check and lands in
  `loose`: a steps file whose label is worth a look.

## What pre-flight checks in a signed file

A `.p7m` is read with openssl (`p7m_signers`; PEM, DER and base64 text) before any browser
opens: unreadable is `not ready`; no codice fiscale in its certificates, or none of the
dichiarante's (`t:identity.codice_fiscale`), is a `warnings` entry. Counts and a yes/no only: Claude
reads the report, so no codice fiscale is in it. It does not verify the signature or the
certificate's validity at signing time; the portal does.

## What a sportello refuses before reading: `FILING`

Napoli's SUE declares a pratica irricevibile, without reading it, for a file not in PDF/A or over
20 MB, a name with spaces, accents or other signs, an unsigned document or procura, or diritti
paid other than before sending to its postal account (DD 501/2026, Linee Guida §§3, 4, 7, 8; the
SUE's Costi page). `run.py`'s `FILING`, keyed by the steps file's `start` (`comune=F839&tipoSportello=E`),
says so; pre-flight checks each file the run attaches:
- **PDF/A**: the XMP's `pdfaid:part`, which PDF/A keeps unfiltered (a .p7m's content, read with
  openssl). It says the file declares PDF/A, not that a validator would pass it.
- **Signed**: a .p7m, or the PDF's own signature (PAdES: a `/ByteRange` and the PKCS#7 in
  `/Contents`), whose signer is read as a .p7m's is. Neither proves the signature holds.
- **Names**: letters, digits and underscores, then the extensions.

Each failure is the file's `problem`, and `yours` carries the same rules for the person's own files
and the payment. For a building title (`FILING`'s `titles`: the CILA, SCIA, SCIA alternativa and
permesso, their sanatorie, and those filed with a landscape authorization, by `rules.main`) `yours`
adds Napoli's annexes: the Allegato A Nuovo Programma 100 and the Modello DP ("sempre obbligatorio"
in each of DD 603/2025's forms), the Stato Comparativo sheet (Linee Guida §9), and, when they apply,
the zona A tipo edilizio attestation and the frazionamento's atto d'obbligo (the SUE's CILA notes of
23/06/2025). The other SUE pratiche (proroghe, voltura, agibilità) get only the file and payment
rules: nothing found says they need more. The 200 DPI the Linee Guida ask for is advice there and isn't checked. With
`--made-up` (a rehearsal) they are the file's `filing` and a warning, so rehearsals still run;
the tests pass `made_up=True` for the rehearsals' files. Seen on 2026-10-31: the Comune's own DD 501
and DD 603 are PAdES-signed and read as such, and are not PDF/A; the veraPDF corpus's PDF/A-1b and
2b files declare it both ways (`part="2"`, `<pdfaid:part>2<`).

## What the person reads before they declare

The person reads the portal's own words, not Claude's summary, and in the window where they tick. A
filled run (in the pane or in `run`) draws a review over the portal from what it holds in memory
(`showReview`, inpage.js), so none of it passes through Claude:

- **The declarations.** After the fresh load, `readDeclarations` opens each section the steps file
  leaves out (`DECLARATIONS`) by its menu link, copies the open section's text (`li#corrente`'s
  `innerText`, minus the portal's Salva and Annulla) and each tick box's label and state (a radio is
  one box: its `_clone` input is skipped, its label is the one beside it), ticks nothing, and goes
  back to the section the steps left open. A box already ticked is flagged. A section that won't
  open is `declarations_note` in the report, never a stop. Held in `__pv.held().declarations`.
- **The portal's PDF preview.** `fetchPreview` does a plain GET of `/fnsuap/preview.do` (a steps file's
  `preview_url` changes it) with the person's session and shows the PDF in the review. Pressing
  "Visualizza anteprima" instead navigates the whole page to that PDF, which would end the run's page.
  Not a PDF, or an error: `preview_note`, and the review says to press the button in the portal.
- **Every value typed**, by section.

`run.py run` also writes the same to `private/` (declarations.json, anteprima.pdf, from
`__pv.previewPdf()`) and into review.html. In the pane they stay in the page.

Seen on the real portal 2026-10-29 (pane, the SCIA rehearsal): all 7 declarations copied, every box
unticked, the 9-page preview fetched (165 KB). Not yet seen: a real client's text (it may carry a
name), a resumed run, the review in a narrow pane.

## Made-up data and the code window

`run.py page` seals `run.js` and opens a window with the code, which the person types into the
portal's page: right for a real person's data, a nuisance for a rehearsal. Rehearsals with made-up
data pass `--plain`; `bench/rerun.py` builds its scripts without a code. Where no window can open
(a sandbox, a remote shell) `page` stops and says so.

## Checking them all: `bench/rerun.py`

After a change to inpage.js, the dictionary or gen.py, rerun the rehearsals in the pane, one
after another, nothing touched between them:

```sh
~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/rerun.py \
    --values <values.json> --out <dir> [rehearsal ...]
```

Hide the pane (Cmd+Shift+B) rather than close it: closing it ends the SPID session and drops a
loaded bundle, so the person signs in and picks the file again (2026-11-01, twice).
In the pane, on the portal's origin and logged in: `check.js` (it names which of `runner.js`
and `steps/<name>.js` the pane lacks: send only those), the `queue-N.js` files, `loop.js`,
then `results.js` until `done` equals `of`. A stopped one: rerun it alone, unchanged, before
calling it a bug (the portal is sometimes slow); twice the same is a bug. 2026-10-29: 20 of
23 on the first pass, 23 of 23 once the runner waited for each section to open.

A rehearsal can be named `NAME:ANSWERS.json` (one pratica, several cases), and a procedure's
later runs travel as what differs from its first. When the pane lacks big files (a new runner,
several steps files), don't copy them through the conversation: a long script can arrive garbled
(2026-10-30). Pass `--bundle <file in Downloads>`, run `pick.js` in the pane, and the person picks
that file once in the box it shows; it is checked by sha256, loaded once, and starts the batch.
No way around the pick: the pane blocks the portal's page from fetching a local server
(`net::ERR_BLOCKED_BY_CLIENT`, tried 2026-11-01), and its file box can't be set by a script.
A hidden pane slows the page's timers, so a script waiting inside the page outlasts the 45 s
call limit (2026-11-01): `results.js` and catalogue.py's `status.js` wait only while the page
shows and otherwise answer at once, so while it's hidden, wait between polls outside the page
(the pane's `wait` actions in one batch, then `results.js`).
One batch per tab: `loop.js` refuses a second while one runs (two would drive one runner and
file each other's results), and `pick.js` refuses to clear the page during one. A bundle clears
the tab's earlier results first: `loop.js` skips a name it finds there, to resume after a reload.
`results.js` lists each run's `moved` ids and `loose` labels, what a gen.py change is checked by.
A run that stops in ~20 s on "the portal stayed busy" with no section opened is most likely a
sign-in that expired: the runner's frame lands on the login page (2026-10-30). Since 2026-10-31
the run says "signed out" instead, and isn't retried.
A run that never reaches the portal ("the page didn't load", "the portal stayed busy", "signed
out") is kept out of the results, and two in a row halt the batch (`halted` in results.js): once
the portal stuck in its wizard after a 10-minute busy run, and each later run, a new frame each,
failed in about a minute until the page was reloaded (2026-10-31). Then save `record.js`'s output,
reload, and bundle what's left: a bundle clears the tab's results.
The queue goes into the bundle by number: each later run of a procedure is what differs from its
first, so name order (queue-10 before queue-2) broke a batch of 14 pieces (2026-10-31).
A stopped run lists its `gaps`: the empty boxes the portal wants, by label, from the runner's
snapshot (no values), so a stop names them without opening the draft (2026-10-31). A slot holding a
file isn't one, nor one taking only signed files (the person's): until 2026-11-02 every slot was
listed, filled or not, which hid the one missing. `--values`
takes the fixture as it is. After a batch, run `record.js` in the pane and pipe what it prints (names
and results, no values) into `rerun.py --record -`: each run goes in its rehearsal's `runs.json`: schema_branches.py
counts a box as filled on the portal only from there. Stopped runs are recorded too. Record a batch
before bundling the next (a bundle clears the tab's results), and leave `--date` out for a batch
run today: it defaults to today (a guessed date filed a batch under the day before, 2026-11-02).
The batch clears the runner's review from the page when it ends.

## Crawling: `catalogue.py pane --bundle`

A crawl batch goes to the pane as one file too: `catalogue.py ops sue --all > ops.json`, then
`catalogue.py pane <dir> --bundle ~/Downloads/pv-<name>.js --ops ops.json [--fresh]` (`--fresh`
crawls them again, though stored; a section it has seen comes back as `same_as`. `--forget-known`
reads every section again too: about 8 minutes for a combination, against 2, for a deeper crawl or
a section that changed in place). In the pane: `pick.js` (the person picks the file once; it
stores and runs wizard.js and crawl.js and starts the batch on the scratch draft, "PROVA NON
INVIARE - catalogo sue"), then `status.js` until `done`; then, with the person's yes, `export.js`
saves the results to Downloads for `catalogue.py import`. The pane's storage also holds the SUAP
crawls and is near Chrome's limit (2026-10-31: 7.2 of about 10 million characters): a result it
can't keep stays in the tab, the batch stops saying so, and export.js still saves it. crawl.js
tries 80 choices a section (the semplificata's Allegato B list has 41); a section with more says
`truncated`.

A combination (two operations in one pratica) is one op: `catalogue.py ops sue --combo NAME MAIN
OTHER` (labels as in `sue-wizard.json`) tries only the procura scelta, as recipes take it, and reads
the attachments screen on the way (crawl.js `also`, `scelte`, `slots`); repeat `--combo` for
several in one batch. `import` keeps the operations and adds the main one's answer-dependent slots.
A main pratica that answers a wizard's Si/No (the SCIA in sanatoria) needs a crawl with that answer
too: `--combo-scelta NAME "<the Si/No question>"` (that combination alone, besides the procura;
`--scelta` sets them for every combination and replaces the default), else
gen.py says the crawl "isn't a crawl of these operations together", missing the section the Sì
adds (`sue-combo-scia-sanatoria-paesaggistica-*`, 2026-10-31). The slots it reads tick only the
checkboxes, so a Si/No's own slots come from the main pratica's recipe.
Once a batch is done and the tab still has wizard.js and crawl.js, a small second one starts from
the page without a bundle: `crawl:batch` set to its ops, then `__crawl.batch(opts)`, the known
fingerprints kept (2026-10-31: the two SCIA in sanatoria combinations). Save the first batch's
results before, or name all of them in export.js: it reads the ops of `crawl:batch`.
A batch whose sections were all seen before is small: `print.js` prints it with its sha256, and
`catalogue.py import -` refuses a copy that arrived changed (no download to ask for), trailing
newlines aside.

A choice deeper than the crawl went (branches.py's `not_tried`) is read by crawling only its
section again, deeper: `__crawl.batch` with `recrawl: [section names]`, `depth: 8` and `variants:
false`, under op names of its own (`d8-scia`: a stored `crawl:op:<name>` is skipped, and the
repo's crawls stay as imported), then `catalogue.py graft EXPORT --section NAME ...` puts each
into every stored crawl holding its fingerprint (a combination keeps its own copy), the rest of
each crawl untouched. Go to depth 8 at once: one level deeper shows the boxes the newly tried
choices open, untried again (2026-11-01: depth 4 still left the 94-bis class's own boxes; depth 8
reached the bottom, 7, in about 1.5 minutes a section). Sections the pane's `crawl:known` lacks are
crawled whole at that depth too (minutes each); keep the store. A section whose fingerprint
changed is refused: crawl the pratica again. Export with a download (the person's yes), checked by
sha256; `CATALOGUE_PRIVATE` is checked as on import.

## Attachments screens

`__crawl.slotsOf("<draft name>")` (crawl.js) opens a draft from Pratiche in bozza and reads
its Allega Documenti slots from the menu at the top, so the sections need not be complete;
an empty "catalogo" draft gives a pratica's base slots (those its answers add are missing).
A slot is marked `required` only once the portal has checked the screen. A run stops on a
required slot left empty unless it is the person's: a signed-only slot, or one the screen's
`theirs` names. A `theirs` entry covers the slots whose titles start with it, except where it is
another slot's whole title: until 2026-11-01 the signed-only "Relazione Paesaggistica
Semplificata" also covered "Relazione paesaggistica semplificata e documentazione…", and four
runs passed as filled with that required slot empty. So a "si allega" box (gen.py `unslotted`,
coverage.md Level 3) is settled by reading a filled draft's slots (`slotsOf`, no rerun needed:
each case's `descrizione` names its draft, so keep it distinct per case, and the newest draft of
a name is read) and writing what the box adds in the dictionary, `slot:` on the box (the slot's
title, or why it adds none).
