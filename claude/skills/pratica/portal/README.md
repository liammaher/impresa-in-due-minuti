# Portal runner: adding a pratica, running it, checking them all

How a pratica on impresainungiorno (the SUAP and SUE front office) goes from crawled to
filled, as the 23 SUE recipes did. The crawl itself is in `catalogue/README.md`; the
person-facing flow (pre-flight questions, the closing lines in the chat) is in the pratica skill. How far the
SUE's five most common cases fill, and why each part that doesn't is refused: `docs/sue-common-cases.md`.

## Adding a pratica

Before mapping anything, look at the other worktrees' branches (`git worktree list`, `git log --all
--since=yesterday`): on 2026-11-02 two chats mapped the same three choices twenty minutes apart.

1. **Is it all mapped?** `catalogue.py count` says which crawled sections the dictionary
   fills. A section none fills needs a dictionary entry (`dictionary/fnsuap.yaml`; its header
   says what a field can carry). Read the section on the portal when the crawl kept no `text`:
   the yes/no questions and their order are only on the page (open a scratch draft: a steps
   file with the wizard only and no sections, "PROVA NON INVIARE - catalogo …"). Read it on a
   fresh draft: a draft saved under other answers keeps their traces (the Scheda anagrafica's
   sede Stato empty after PERSONA, 2026-11-02). The crawl tries only dropdowns of up to 12
   options: what a longer one opens is found by choosing one on the page (the Camera di
   commercio opens "Numero REA" and "Data", a foreign Stato of birth "Località estera").
   Where a choice puts its boxes (which block comes first) is the page's layout, not a value: any
   saved draft of the pratica shows it, ticked there and left without Salva (the designer's block
   above the director's, read on three rehearsals' drafts 2026-11-02). A section of a draft reads
   with `__crawl.sectionOf(draft, section)`; what its "+" adds with `__crawl.plusOf(draft, section,
   {choice, nth})` (the choice ticked first, the nth "+" pressed, default the last; each row's boxes
   after it, new and required ones marked; Annulla, nothing saved). A `new` box can be one the
   portal draws only on the next request: on a freshly opened landscape tecnico, "non è colui" leaves
   the first technician's studio Provincia and C.A.P. undrawn until the "+" (2026-11-05).
   So is every box below a row the "+" adds, which it renumbers: the cambio's title "+" read 6 new,
   3 of them the holders under "presentata da" (2026-11-05). The crawl's `plus` saw those 6 under
   the holders' label, though the "+" it counts adds a title: where a section has two (`of` 2, or a
   crawl without `of`), read each on a draft by `nth` before mapping either.
   To try a crawl.js change in the pane without another file pick: apply the same small edit to
   the pane's stored copy (`localStorage` `pv-crawl`), check its sha256 against `catalogue.py pane`'s
   `load.js`, store it and eval it. Each eval starts its own portal frame and leaves the earlier
   ones over the page: remove every `iframe` first, or a script reads an older frame's state.
2. **The recipe** (`rehearsals/<name>/recipe.yaml`): procedure, title, comune, sportello,
   crawl, operation (or a list of them), scelte, `first`, `asks`, `yours` (what's left to the
   person: declarations, attachments, payment, signing), `supports` (the cases refused, with
   why: all or nothing; `if:` checks one only once its gate holds, asking it only then).
   What the tecnico reads (questions, items, `else`, `yours`) is Italian, as tu (never Lei: bench/test_voice.py), one idea a
   sentence, with no path, library id or software word; an `else` names the exact case in at
   most 300 characters, an end step at most 350 (test_gen). A refusal behind a portal defect
   names it (`defect:`), and `defects.yaml` says the rest: what still fills, the choices.
   A scelta only some cases take is `{option, when}` (co-holders, a new direttore, the others'
   assent): run.py ticks it, and keeps the sections it adds, only when its `when` holds. Until
   2026-11-02 every scelta was fixed, so a voltura always had a co-holder and a cambio
   d'intestazione never did, whatever the case said.
   Copy a sibling: `rehearsals/paesaggistica-ordinaria-fittizia`.
   **Two operations in one pratica** (a building pratica with its landscape authorization): the
   recipe `extends: [<main pratica's rehearsal>, parts/<the other's part>]` and states only what is
   its own (procedure, title, crawl, `descrizione`, `yours`, its case's `answers`). The rest follows
   from the two (gen.py `resolved`, since 2026-11-04): its operations are the main pratica's then
   each part's `operation`, its rules table's `main` is the main pratica's, its comune and sportello
   the main one's. Later ones win key by key; `attachments`, `supports` and `sections` add up;
   `asks` and `rules` merge by key, each replaced whole but `rules.handles`, which adds up (a third
   operation's part adds its pratica to the two before); `yours` is replaced,
   so a recipe restates its main pratica's (2026-11-03: without it the draft's name, whose ask only
   the main pratica's `yours` used, wasn't asked, and pre-flight stopped);
   a null drops what came before (`data_inizio_lavori: null`); a slot `{label, drop: true}` drops
   one a part adds that this form never opens (the ordinaria's second relazione slot comes from the
   SCIA's and the permesso's "Si allega" box: a CILA or CIL has none, 2026-10-31). Then a slot or a
   refusal mapped on the main pratica reaches its combinations (2026-10-31: the SCIA's had missed
   eleven slots).
   A part can say on its own what a box of the main form also says: the terre e rocce's
   dichiarazione and the asseverazione's materiali di risulta (by-products, the small or the large
   site). The fills don't catch a contradiction, so the dictionary's `supports` hold the two to one
   answer and the box is `propose`d from the rules table's fact (2026-11-03: nine combinations filed
   a dichiarazione while their asseverazione said "no excavation", every one "filled").
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
   A `supports` entry whose refusal is a case the map can't fill yet (not one the law makes, not a
   portal limit) carries `unmapped: true`: that marker, not the wording, is what coverage.md's
   Level 2 counts (`scoreboard.unmapped_refusals`; test_gen checks the markers still count).
   A new fact multiplies the table's cases by its values: with `terre_rocce` (three) the library's
   validator walks 34 million combinations (8 minutes; it built them as one array and ran out of memory
   until 2026-11-03). `bench/test_rules.py` walks only the cases `route.cases()` reaches, each fact as
   the table asks it (30,635, seconds; it took 45 minutes as the product until 2026-11-04), and checks
   each leaf leaves no rule open, so the two hold the same cases; the existing cases then answer it as
   they did before (`bench/add_answer.py`), and test_route's hand-written cases too. In the library a
   rule's `regime` is a closed list (`contract/rules.schema.json`: a filing is `comunicazione`), its
   procedures one folder per ente name (the site test), and every entry must parse with PyYAML as well
   as the library's own parser: the vault's tools read them (an unquoted `ask: …?` in a flow mapping
   broke portability.py, 2026-11-03). Work on the library in a worktree of its own: its Desktop
   checkout is shared, and was switched back to main under a branch in progress (2026-11-03).
   A form's own box on the same thing (what the SCIA files, `scia_tipo`) is `propose`d from the
   table's answers, for the person to confirm: `{{ask.intervento,ask.strutture|sue_scia_tipo}}`
   reads several facts at once, and a proposal waits while a fact it reads is still asked.
3. **Generate:** `gen.py <recipe> --out <dir>/portal-steps.generated.yaml`. It writes nothing
   if any field is unaccounted for. The steps files are build outputs, never committed (since
   2026-11-04; they were 70,000 lines): `rehearsals/steps.lock` is, one sha256 per steps file
   (`cd rehearsals && shasum -a 256 -c steps.lock` checks the ones on disk). `gen.ensure()` writes
   any that is missing or isn't the lock's (a fresh clone, a pull): route.py, the bench tests and
   tools call it, and `make steps` runs `bench/regen.py`. After a dictionary, recipe or gen.py
   change run `bench/regen.py` (every steps file, the lock and each combination's answers; test_gen
   fails while the lock is stale, and `plugin/build.py` refuses to build) and commit the lock: its
   diff names the pratiche the change touches, and an unrelated one is a regression until shown
   otherwise. `bench/plan_diff.py` says what the change does to each case (its fill plan
   before and after). A new question the existing cases reach makes their pre-flight propose
   or ask it: answer it in each as the case did before, and plan_diff shows them unchanged, so
   their recorded runs still stand. A new list's count with only a `propose` (`titoli_quanti`,
   2026-11-05) makes every existing case ask the second block's own boxes, not just the count,
   since a block waits for its count: give them the count (`bench/add_answer.py`).
   Add the keys as text: rewriting a file with `json.dump` reflows
   its inline lists, and the diff of 84 files buries the answers (2026-11-01). `bench/add_answer.py KEY
   VALUE` does it for every rehearsal whose steps ask KEY, puts it in a part's `answers` where a
   combination's main pratica doesn't ask KEY (the CIL with its landscape authorization: regenerated
   from the CIL's, it lost the key, 2026-11-02), and writes the combinations' answers again.
4. **Pre-flight** with made-up answers (`answers-p6.json`) and the P6 fixture's values
   (`--values rehearsals/cila-fittizia/fixture-p6.json`, the fixture as it is): `run.py preflight --made-up`
   (the rehearsal's files are made up: Napoli's file rules only warn, below), from the repo's root:
   an answers file names its files from there (elsewhere each reads "no file"). A box the portal
   checks against a real register warns too (`made_up:` in the dictionary: a registered company's
   codice fiscale, looked up in the Registro Imprese): that case's run stops there by design.
5. **Run in the pane** (the pratica skill, step 2) and record each run in the rehearsal's
   `runs.json`, the one run record: `rerun.py --record` adds the date, answers file, result and
   seconds; add a `note` (what stopped it and what fixed it) and a `case` where the words help.
   coverage.md's "Run on the portal" and schema_branches.py both read it, and the README's run
   table is drawn from it (`runs.py --write`, which `--record` runs; test_gen fails on a table
   that differs). Until 2026-11-04 the READMEs' rows were a second record, and ten rehearsals
   recorded only in runs.json read as never run. Where a case fills blocks that share labels (technicians, firms), read its draft's
   section after (`__crawl.sectionOf`): the read-back finds each box the way it was filled, so two
   blocks swapped read back as kept.
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

The SUE has two tables (2026-11-04): `sue-napoli` for new works (the title, and what goes with it:
the landscape authorization asked, extended or renewed, the terre e rocce) and `sue-napoli-adempimenti`
for what is filed on a title held (start and end of works, agibilità, proroghe, voltura, direttore dei
lavori, impresa, DAU). A steps file reads one table, so the landscape proroga and rinnovo filed alone are
`sue-napoli`'s (works with no title); filed with a title's extension they are the adempimenti's. A
combination's `rules.facts` replace its parents' whole (`rules` merges by key), so a combination of two
rehearsed pratiche restates its main pratica's facts. A title's landscape quadro states `proroga` and
`rinnovo` as the semplificata (the dictionary), as the combinations were filled on the portal.

## Operations filed together: `catalogue/F839/sue-pairs.yaml`

Which of the wizard's pairs a case files in one pratica, and why, is `sue-pairs.yaml` (catalogue/README.md);
`bench/test_pairs.py` lists any filed together with no steps file. A combination of two pratiche each
rehearsed alone (a proroga with the landscape proroga) `extends` both: the first is the main pratica, and
gen.py's `combo_answers` fills from the other's answers what the main's don't say (its own section's), the
people of both kept. Its `scelte` are only those the combination's crawled wizard offers (gen.py refuses
another: filed with a title, the landscape proroga's third-party assent isn't there, 2026-11-04). A recipe
built on a combination's recipe states `first` and `after` itself: copied as null from a recipe that inherits
them they drop the payment and attachments screens (twenty did, 2026-11-04; `test_gen.py` checks every
SUE steps file opens with the Scheda anagrafica and has its payment and attachments screens). Its `yours`
takes the main pratica's payment lines (diritti, bollo): another's "no bollo on this form" contradicts a main
pratica that has a bollo section. Its `diritti_euro` is the main pratica's too, copied where the other part's
would win the merge (a null where the main has none): the Comune's table (G.C. 239/2026) charges a landscape
authorization only "quando oggetto di autonoma istanza" and has no line for the terre e rocce or the DAU
(`test_preflight.py` checks every combination). The diritti's facts no box holds (the contributo's amount
for SUE 7-9, a car park's area for SUE 4-6) are asks with their own `when`, read only by the diritti's
`propose`: pre-flight asks them where that `when` holds and the diritti aren't answered. Every combination has a rules table since 2026-11-04; `rules:` with `main`
and `handles` and no `table` is still accepted, for a combination mapped before its table (pre-flight then
decides nothing and the person names the pratica).

## Every choice: `branches.py`

gen.py passes a radio or tick box the dictionary doesn't name (the run leaves it unticked), so a
section counts as filled with choices no case can take yet. `branches.py --write` lists every SUE
choice the crawls saw, once per section, in `docs/sue-branches.md`: ticked under some answer,
from an answer (a dropdown), the person's, or unmapped, most shared sections first. A box a choice
opened that the crawl never tried itself counts too, marked `not_tried` (what it opens is unknown:
the art. 94-bis class under a structural tolerance). It flags a section at the 30-choice limit.

## National or Napoli's: `portability.py`

A rough split of the SUE mapping for another comune or region, in `docs/portability.md`: each
of branches.py's choices as a national form's alternative, a choice naming a Campania law or
Napoli, or neither; each rule of `rules/sue-napoli.yaml` by where its cited sources are published
(the library's URLs: `PRATICHE_NAPOLI_DIR`, needed for `--write`). Counted, not read: a rule
that also cites a Comune page may only confirm a national one there.

## What the portal does that bit us

- **Street types.** The Scheda anagrafica's "Toponimo (DUG)" offers only ALTRO, CORSO, LARGO,
  PIAZZA, VIA and VIALE; ALTRO opens "Dettaglio DUG" ("da compilare obbligatoriamente nel caso si
  sia selezionato 'ALTRO'"), a list of 190 street types that the crawl recorded only as a count:
  run.py takes it to be InfoCamere's national toponimo list (194, `schema/`), never read option by
  option. So a Vico is ALTRO + VICO + the name after it, and a type in neither list (Naples' CUPA,
  GRADINI, FONDACO, RAMPE, SUPPORTICO) is named by pre-flight. The location's "Via, Viale, Piazza"
  lookup lists the comune's streets each starting with its type, whatever it is. Until 2026-11-04
  both knew only the five: 1,240 of the 3,508 streets in Naples' stradario (`internal/napoli`)
  would have stopped a run, and every rehearsal's address was a Via, so none did. Seen on the
  portal 2026-11-04 (`rehearsals/cila-fittizia/answers-comproprietaria-negozio`, filled): the
  property on VICO CACCIOTTOLI, a street whose name the stradario also gives a Salita, a
  Piazzetta and Gradini (the type tells them apart), and the client's home on a Vicoletto saved as ALTRO + VICOLETTO + "2° AVVOCATA", so
  "Dettaglio DUG" takes the national list's words. The fixture's `marta`, `bruno` and `dario` live
  and own on such streets (a Vicoletto, a Piazzetta; a Vico, a Cupa, a Traversa) to keep it tried.
- **A section's text past 3,000 characters isn't in its crawl** (crawl.js keeps that much), so a
  long section's own wording, not just its box labels, is read on a draft: the CILA relazione's
  two lists were filled for a week as filings "already made" and assents "already obtained", and
  their words, past that point, say filings "che si presentano contestualmente alla CILA" and
  "atti di assenso da acquisire" (2026-11-03). From Pratiche in bozza, APRI opens the draft on
  Allega documenti (its `.content-title` "GESTIONE DEGLI ALLEGATI"); the "COMPILAZIONE PRATICA"
  breadcrumb goes back to the sections, a section's title link opens it, ANNULLA leaves it unsaved.
  The draft's step menu is a list of `li.title-list` items, Compilazione Pratica, Dati
  Dichiarazioni, Allega Documenti (each an `a` link; the open one `selected`, an unfinished one
  `complete-false`), then Firma and Invio with no link until everything is in. The address is
  `/fnsuap/cmd/home?execution=eNsM`, a key that moves on with every page, so a draft is reached
  again by its name in Pratiche in bozza, never by an address kept from an earlier visit.
- **A calendar left open.** A date box opens jQuery UI's calendar (`div#ui-datepicker-div`), which
  a person's click elsewhere closes and a script's `click()` doesn't: it covered the next box (the
  permesso's sanatoria quadro, 2026-11-02). `closeLists` closes it, with the suggestion lists,
  before every box and before Salva (`bench/test_inpage.py`, `?calendar=1`).
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
  A dropdown the portal has flagged required takes "Il valore è obbligatorio" as its title, and its
  cell lists its options: neither is its label. The Scheda anagrafica's Forma giuridica re-renders the
  company block and flags the sede's empty boxes, so its Provincia counted as no "Provincia" until
  2026-11-02 ("2 fields with this label", three runs).
- **Boxes that move.** A tick that opens rows above the box renumbers it (the paesaggistica's
  art. 136): gen.py sends it by label. The crawl's `moved` pairs two same-label boxes wrongly
  at times; a pair whose new id was on the page already is not a move.
- **Section names.** Two sections can share a long prefix ("dichiarazione relativa alla
  conoscenza d…"): open and check by the whole name. The Scheda anagrafica's link reloads the
  whole page: the runner waits until the section is the open one before reading it.
- **Scelte.** Some sections exist only with a scelta ("ci sono cointestatari"): list every
  scelta the case needs; gen.py ticks them all. A section a scelta drops for a case takes its asks
  with it (run.py `chosen`): the co-holders' count, with no co-holders (2026-11-05: pre-flight
  stopped on "no field reads asks.cointestatari_quanti").
- **Values the portal checks.** Codici fiscali and partite IVA by their check digit (the P6
  fixture's pass), the draft's name at most 60 characters, a P.G. box may take 10. The landscape
  pratiche's other technician's PEC is looked up at Salva: kept, but "Indirizzo Pec non valido" under
  any address that isn't a real one, `@pec.it` included (a real public PEC cleared it, 2026-11-02).
  That warning is an `.alert-message-text` beside the box, not the `.error-message-text` the runner
  read, so every run passed without a word about it. A scan of a filled SCIA draft's 35 sections found
  three: the domicilio's PEC too ("Indirizzo Pec non valido": every rehearsal's, `made_up`), the
  property's street ("Attenzione! Indirizzo sconosciuto.", which the Comune's own Piazza Municipio 1,
  80133 got as well, with no scala or interno), and foglio, particella, subalterno and categoria
  ("Attenzione! Dati catastali sconosciuti", not tried with a real parcel). The portal keeps each
  value, and a person couldn't clear the address one, so a warning never stops a run: the report's
  `alerts` lists each by section and the box's label (no value), results.js counts them, and
  review.py's closing lines name each for the person to check (none in a Prova: made-up data
  raises them).
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
  the SCIA alternativa have one, 2026-11-02), or one under another title (the sanctions receipt is the
  SCIA's "Ricevuta/e di versamento a titolo di sanzione" and the permesso's "Ricevuta di pagamento
  della sanzione": a run stopped on it, the stop's `gaps` naming the real one, 2026-11-03). An `on_page` slot that isn't there stops the run ("0
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
  one section, 2026-11-01), and the boxes after it go by label; an `add` with `nth` presses a
  later one (a list of lists: Dati catastali's group "+", below). The `each` may take `anchor`,
  `add_when` (the "+" only where it holds, per block) and `free` block fields (found in the whole
  section, not in the block); `#P` is the block before's `#N`. A field key inpage.js reads must
  also be in the keys run.py sends the page (`page_bundle`'s list): `last` wasn't at first, and
  the run ticked the first group's radio. A filter a steps file names stays in run.py once
  renamed (`one_catasto`): plan_diff and a patch run main's steps through this run.py, and an
  unknown filter reads as a missing value, never an error (test_gen checks every name, main's too). "Alle dipendenze di" opens more
  than the crawl saw: the firm's REA, seat and legale rappresentante (read 2026-10-31).
- **Dati catastali is a list of lists** (read on a CILA draft 2026-11-04, cancelled unsaved): the
  NCEU/NCT radios once, then the units, each foglio, particella/mappale, subalterno and the rest
  under the same labels; the first "+" after a unit's boxes adds one more (with a "-" beside it),
  and the "+" below that adds another group with its own radios. The units are the client's
  `immobile`, `immobile2` ... (`unita_catastali`: unasked while the vault holds no `immobile2`,
  else proposed from how many it holds), each with its own catasto (`catasto_terreni#N`, from its
  categoria, asked when it has none). Units count across groups (unit n is the n-th "foglio"), so
  one list of blocks fills both groups: within a catasto the unit's "+" (`add_when` on the
  `each`), and where the catasto changes the group's "+" (a block field `kind: add`, `nth: 2`:
  the second "+" after the last unit) and that group's radio (`free`, found in the whole section,
  `last`: it sits above the group's first unit). The radios' long names ("Nuovo Catasto
  Terreni") are only their titles: once the portal has checked the section (any "+" does) every
  radio, the first group's too, is titled "Il valore è obbligatorio" and reads NCEU or NCT, so
  the new group's is the page's last "NCT" (by its long name, none found: the first run stopped
  there, 2026-11-04). The first group's keeps its crawl id, which the run trusts when its label
  has gone (`loose` in the report). Filled on the portal 2026-11-04: a flat and its garden plot. `#P` in a block is the
  block before's `#N`. After the second group's last unit come the same three buttons (unit "+",
  group "+", "-"), so a third group back to the first catasto is the group's "+" again (read on a
  draft 2026-11-05): units in any order of catasti. The first run with three groups stopped after
  Salva on "not kept NCT: empty" though the draft saved NCEU, NCT, NCEU and all four units: the
  read-back found the `last` NCT again as the page's newest, by then the third group's. A `last` box
  is now pinned where it was filled (inpage.js `at`; a resumed run's `kept` carries it). On the fake
  portal the same case also ticked the third group's NCT for its NCEU, a radio's texts including the
  cell to its left: `last` now prefers boxes whose own cell starts with the label (the portal's own
  radios weren't misread that way). A vault read must name each copy (`*:immobile2.*`: a scope
  matches a category whole).
  The crawl's own "plus" pressed the last "+", the group's, which is why its `adds` looked odd
  (crawl.js now notes how many "+" it saw, `of`). By label "subalterno" the first run typed the
  subalterno into the particella box and left its own empty: the runner reads a box's first three
  distinct texts, and the particella's title said twice (its own, the header above) lets the next
  column's "subalterno" in, as near as the subalterno's own (whose title is "se non presente
  indicare il numero 0"). The dictionary field's `title` is the text the run finds a block's box by,
  its `label` still the crawl's (gen.py accounts for the box by it). The stop read "not kept:
  particella/mappale different, subalterno different": two neighbouring boxes "different" after
  Salva means one label found its neighbour; open the draft and read the boxes' values. The fake
  portal's `?catasto=1` (test_inpage) keeps both: by title it fills, by label it doesn't; and a
  flat then two plots: the group's "+", its own radio, then the second group's own unit "+".
- **Holders and co-holders repeat too** (read on drafts 2026-11-05, pressed and cancelled with Annulla):
  the titles' "Titolarità dell'intervento" (one section for the CIL, CILA, SCIA, SCIA alternativa,
  permesso and agibilità) adds another holder's whole row by the "+" after the last one (27 boxes,
  the company tick and its three boxes too), and the voltura's and cambio d'intestazione's "Informazioni
  su eventuali altri aventi titolo" another co-holder's 14 boxes, with its own two required sesso
  groups. Each is an `each` (`altri_titolari`, `cointestatari_quanti`: unasked while the job names no
  `r2:` or `a2:`), the people `r:`, `r2:` ... (`o#N:` a company holder) and `a:`, `a2:` .... The
  coholders-one defect (no "+", from the 2026-10-28 crawl) was wrong and is withdrawn: the 2026-10-31
  crawl had recorded the "+" (`plus`), unread. A missing "+" is read on a draft before it's a defect.
  Two cases of one pratica with other counts take other steps: page_bundle keys each by its blocks
  (`procedure#hash`) also for steps rerun.py has expanded already; until 2026-11-05 those shared one key
  and the second case of a batch ran on the first's steps.
- **So do firms, previous holders and landscape technicians** (read on drafts 2026-11-05, cancelled
  with Annulla). Every "+" a crawl saw is an `each` or a `plus:` reason (test_gen). The building firms
  (Impresa esecutrice, the CIL's f, the CILA's and permesso's h, the SCIA's i) are `f1:`, `f2:`,
  `f3:` ... (`f#K`, `imprese_quante`): the fixed two-firm `firms:` mechanism is gone from gen.py. The
  cambio d'intestazione's "estremi della CILA / SCIA / DIA" has two "+": the title's (one title is
  mapped) and, below "presentata da", the previous holders', each three boxes under their own labels
  (`precedente#N_cognome`, `_nome`, `_cf`; `precedenti_quanti`, proposed 1). The landscape form's "dati
  relativi al nome del tecnico" adds a whole technician (name, codice fiscale, studio, phone, PEC, albo)
  under "non è colui che presenta la pratica" (`p:`, `p2:` ...; `progettisti_quanti`); under "è colui"
  the same "+" shows only an unnamed albo row, so a second technician there is refused
  (defects.yaml `paesaggio-altri-tecnici`). An existing case that names `f2:` answers
  `imprese_quante: 2`, so its plan and recorded runs stand.
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
- **A choice can open a block above the others.** The architectural designer who isn't the architect
  presenting the pratica ("non è colui che presenta la pratica", which the crawl names "tecnico
  incaricato") opens a whole block of their own, the first Cognome of G1, h1 and g1, above the other
  director's and the structural designer's (read on drafts of each 2026-11-02). The entry's `shift`
  says so: under that answer every other block of the anchor counts one more, and gen.py writes each
  of their fields twice. A radio isn't an anchor: it is two inputs (the real one and its `_clone`).
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
  and payment rows are 1 and 2 each (read by the inputs' names and values, 2026-11-02). A run shows
  it as "not kept … hidden by a later choice": the section's read-back can't find a box it filled, as
  the next row's tick hid it (until 2026-11-02 that stop read as a lookup's "fields with this label",
  which the runner retried twice as a slow portal, filing the draft wrong each time). Where the form's own choice can't say both, it's a portal
  defect (`defects.yaml`, `pdc-aree-fuoco`): left unticked and in `yours`, never filled around.
  `defects.yaml` is the one defect record: each entry's `page` is its section of
  `docs/portal-defects.md`, which `defects.py --write` draws (test_gen fails on a page that differs).
- **A portal document's box reads "Scarica il documento"** (the procura, the DSC), once the
  declarations are ticked: before, the slot is an empty upload box like any other, "Tipologie
  ammesse: jpg.p7m;pdf.p7m Allega Max: 9,77 MB Il valore è obbligatorio" for the procura, the same
  with every type for the CIL's "Quadro riepilogativo della documentazione C.I.L." (2026-11-03). The attachments
  screen's `theirs` names it, so its "required" isn't the first run's error, and the second run
  attaches it (below, Signed files and the second run); nor is the "required" under a slot that
  takes only signed files (.p7m), which the person signs and Claude attaches. A stop's
  snapshot names each slot by its title, with the types it takes, whether it's required and
  whether it holds a file. An upload widget's wrapper has a title of its own (the portal's message
  once the screen is checked, else "false" or "true"), which is never the slot's; a slot is
  required by the message, not by a title that says "OBBLIGATORIO" (the broadband one, 2026-11-02).
- **A decimal box shows 516 as 516,00.** gen.py makes the crawled box it finds a number when its id
  ends `:real`. Two choices of one radio group whose `when`s start with the same term are looked up in
  one state, both opened, and labels compare without case: the sanatoria receipt's "di euro" (a `:real`)
  was found as the estremi row's "di Euro" (a text box), so it went as text and the read-back said "not
  kept" (2026-11-02). Such a box is `kind: number` in the dictionary; an `anchor` field, never looked up
  in the crawl, too.
- **A file box's cell names the file once it's in.** Name an upload by the row above it (the
  crawl's `context`), not by its cell ("Tipologie ammesse"), or the read-back can't find it.
- **The portal's own errors:** "errore inatteso", a 503 for maintenance, a fresh load that
  lands on `/cmd/error`, a section slow to open or to show its boxes. Every section is saved
  by then, so the runner picks itself up: it reopens the draft from Pratiche in bozza (or
  goes on from its address), waits 10 s and resumes, at most twice, each try in the report's
  `retries`. A value the portal refuses or doesn't keep, or a renamed label, still stops, and so
  does a lookup that finds some boxes with the label but not the nth: only "0 fields with this
  label" is a section still showing (2026-11-02: the sede's Provincia, retried twice for nothing).
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

## Signed files and the second run

The portal checks every file on upload and refuses it in a PrimeFaces warning growl
(`.ui-growl-item-container.ui-growl-warn`: `.ui-growl-title` "Il documento non è stato accettato",
the reason in its `<p>`) that fades in about two seconds and leaves the slot empty, no message under
it. Seen 2026-11-03 on a made-up CIL draft, in its signed-only "copia attestazione versamento":
a `.p7m` signed with a self-signed certificate, "Una o più firme digitali presenti sul documento non
sono valide"; bytes that aren't a PKCS#7 named `.pdf.p7m`, "Il tipo di documento non corrisponde
alle tipologie ammesse". So the portal reads the envelope and validates the certificate at upload,
not only at Firma.
So a slot that takes only signed files gets the person's own signed file: gen.py maps it where an
entry names it, with the slot's `accepts`, pre-flight refuses a plain copy and reads who signed, and
inpage.js `attach` watches for the growl and stops on it, naming the slot and the portal's words. A
rehearsal can't fill such a slot: `--made-up` (preflight, page, run; `bench/rerun.py` always) leaves
every one out and says how many.

What the portal makes from the pratica only once the declarations are ticked (gen.py marks a slot
the crawl calls a `portal_document`: the procura, the DSC, the Relazione Paesaggistica Semplificata,
the terre e rocce forms) and the diritti receipt (paid before sending; the dictionary marks it) carry
`after_declarations`. The first run leaves them, and its `yours` says what to download, who signs, and
that Claude attaches them. The second run, `run.py preflight|page|run --after-declarations` with the
same answers and those files, reopens the draft by its name from Pratiche in bozza (the person's
clicks have moved its address on), goes to Allega documenti by the menu's "Allega Documenti" step
(the dictionary's `step`) and attaches those alone: no section, declaration or other slot is touched.
Napoli's own annexes go with it: the Allegato A Programma 100 and the Modello DP, which fill.py fills
from the library's CILA entry (the same Comune forms for every title; a recipe sets `napoli_allegato_a`,
`modello_dp`), have no slot, so they go under Allegati liberi. There each file takes the slot's first
empty box, or a new one ("+"): an upload into a box that holds a file replaces it (2026-11-03, the
Allegato A lost under the Modello DP on a first try), and a file the slot already shows is left, so a
retry attaches nothing twice. A slot of one box with no "+" takes the new file in place of the old.
Checked on the portal 2026-11-03 with made-up files on the CILA P6 draft: reopened by its name,
Allega Documenti reached by its step, the annexes in Allegati liberi after the first run's relazione,
the DSC in its slot. The receipt slot ("copia attestazione versamento oneri, diritti e spese") refused a
plain PDF ("Il tipo di documento non corrisponde alle tipologie ammesse"): it takes only signed files,
which the CILA's crawl, made on an empty draft, hadn't recorded (`accepts_read` in its slot now).

## What InfoCamere's manuals say (read 2026-11-04, not yet seen on today's portal)

Two public editions of the front office's user manual: *Manuale Operativo Funzioni di
compilazione pratica* version 9 (December 2013, the portal's own "Manuale utente" link,
`https://www.impresainungiorno.gov.it/dispatcher/help/manuale_utente.pdf`) and version 21 (April 2018,
the I-SUAP front office the SUE uses; a copy at
`https://benevento.ordingegneri.it/wp-content/uploads/sites/74/2022/03/Manuale_SUAP_Funzioni_di_compilazione_pratica.pdf`).
Written for the SUAP; the SUE runs on the same front office. What they add, to check on the portal
before any code relies on it:

- **After Invio (v21 pp. 52-58).** "Vai alla Scrivania" on the sportello's home page opens MyPage,
  "Le mie pratiche inviate": every open pratica and those closed less than a year ago, searchable by
  the codice pratica the confirmation and the receipt give. A pratica's page has "Nuova
  Comunicazione": "Seleziona un tipo di richiesta" (comunicazione, sent of one's own accord;
  conformazione dell'attività or integrazione, when the office asked for one), files by "Sfoglia" and
  "Salva Allegato", "Note di compilazione" up to 4,096 characters, then "Invia Comunicazione" (the
  person's). The same file types as the pratica's. It makes an event on the office's Scrivania and a
  receipt for the sender. Only the dichiarante, who signed the pratica (the procuratore), may send;
  with a weak login every file must carry the dichiarante's signature. Not on a pratica the office
  has put in "Archiviata". Integrations go this way, not by PEC. Mapping it needs a sent pratica:
  none exists with made-up data.
- **"Copia pratica" (v21 pp. 26-28).** At the start, "importa dati da pratica precedente" fills a new
  pratica from one of one's own, sent or in bozza, searched by comune, codice pratica, the
  dichiarante's codice fiscale or date; everything but the attachments, every section editable.
- **Address and catasto checks (v21 pp. 24-25).** The orange "Indirizzo sconosciuto" and "Dati
  catastali sconosciuti" are the office's stradario and catasto, checked when it has loaded them, and
  never blocking. Made-up data always raises them (`alerts`); on a real case they say the address or
  the cadastral data don't match the office's archive, which the person should see.
- **The asseverazione is its own document (v21 pp. 29-30).** The front office writes the Relazione
  Tecnica di Asseverazione from its sections and shows it on the signing page beside the pratica's
  PDF (the MDA); the two may be signed by different people (the designer, the procuratore).
- **Attachments (v21 p. 49).** The procura only as `pdf.p7m`; a document of several files by the
  slot's "+"; one file per type of attachment, never several required documents in one file;
  Allegati liberi only for documents no slot names.
- **Drafts (v9 p. 43).** A draft signed but not sent reopens at its attachments and must be signed
  again; a sent pratica leaves Pratiche in bozza (v21 p. 51).
- **Signing (v9 p. 40).** The 2013 edition accepts the signed pratica only as `.p7m`, not a signed
  PDF; the 2018 one doesn't repeat it.

## Firma e invio: the person's

The runs stop at Allega documenti, and the last screens stay the person's for a reason the portal
makes. Its menu's "Firma" and "Invio" are not links until Compilazione Pratica and Allega
Documenti are complete: the declarations ticked (the dichiarante's) and every required slot in,
each digital signature checked for validity, the procura's by the procuratore too (InfoCamere's
*Manuale funzioni di compilazione pratica*, pp. 55-62, the portal's "Manuale utente"; seen
2026-11-03 on a made-up draft). So they can't be reached on made-up data. On them the procuratore
signs the pratica's PDF and then a "distinta" (online, with a firma digitale device, InfoCamere's
signing client and the PIN; or offline: download, sign unopened and unrenamed, upload), then
sends; the result page gives the codice pratica and the receipt goes to the PEC. Every one of
those is signing or sending, so nothing there is the runner's: `FILING`'s `yours` says it, and
`FORBIDDEN` keeps the runner off any control named firma, invia or paga.

## What the person reads before they declare

The person reads the portal's own words, not Claude's summary, on the portal, where they tick: its
preview ("Visualizza anteprima") and each declarations section. A filled run leaves the draft open
in its frame and draws nothing over it. Claude then says three things in the chat (`review.py`,
`bench/test_review_check.py`): it worked, what to check (the `alerts`, and in the skill's check a
value or file that doesn't match the documents), and what is left on the portal, numbered: the
preview, the declarations, the second compilation when the case has one, signing, paying, sending.
A Prova says two lines: done in so many seconds with made-up data, and delete the draft.

Until 2026-11-07 a filled run drew a review over the portal (the declarations' text, the PDF, every
value) and `review.py` wrote review.html. Both repeated what the portal already shows where the
person ticks and signs, and were noise in a test; keeping values out of Claude, their reason, was
dropped on 2026-11-05. The run still reads both, kept only in the run's private folder:

- **The declarations.** After the fresh load, `readDeclarations` opens each section the steps file
  leaves out (`DECLARATIONS`) by its menu link, copies the open section's text (`li#corrente`'s
  `innerText`, minus the portal's Salva and Annulla) and each tick box's label and state (a radio is
  one box: its `_clone` input is skipped, its label is the one beside it), ticks nothing, and goes
  back to the section the steps left open. A section that won't open is `declarations_note` in the
  report, never a stop. Held in `__pv.held().declarations`, never in the report.
- **The portal's PDF preview.** `fetchPreview` does a plain GET of `/fnsuap/preview.do` (a steps file's
  `preview_url` changes it) with the person's session. Pressing "Visualizza anteprima" instead
  navigates the whole page to that PDF, which would end the run's page. Not a PDF, or an error:
  `preview_note`. The skill reads it as text (`preview_text.js`, below) for the check.

`run.py run` writes both to `private/` (declarations.json, anteprima.pdf, from `__pv.previewPdf()`).
In the pane they stay in the page.

Seen on the real portal 2026-10-29 (pane, the SCIA rehearsal): all 7 declarations copied, every box
unticked, the 9-page preview fetched (165 KB). Not yet seen: a real client's text (it may carry a
name), a resumed run.

### The preview as text, for a check against the documents

Spike of 2026-11-05 (pane, the CILA rehearsal "quattro gruppi e quattro titolari", made-up data),
for a check that doesn't trust the mapping: read what the portal will send, under its own labels,
and hold every value to the source documents.

- **Text with no Python and no pdf.js.** `preview_text.js`, one JavaScript call on any
  page of the open draft (the file's text as it is: the pane awaits it), returns the preview's
  text using the browser's own `DecompressionStream`. The preview is iText 2.1.7: Flate streams,
  no object streams, WinAnsi fonts with no ToUnicode, and pages drawn only with `BT/ET/Tm/Td/Tj/q/Q`
  (no `TJ`, `cm` or form XObjects; 95 objects, all read). 13 pages, 103 KB, 23k characters (one
  tool result). Rows come out as label line, then value line ("Nome  Cognome  Cod.Fiscale" /
  "Ugo  Fittizio  FTTGUO71D08F839S"), tick boxes as `[ X ]` / `[  ]`. It also reads what another
  writer may use (`TJ`, `'`, `"`, `T*`, `TL`, `cm`, hex strings, an indirect or wrong `/Length`);
  what it can't read faithfully (object streams, encryption, CID or remapped fonts, a form
  XObject drawn on a page, another filter) returns `{error}`, never a wrong or partial text.
  `bench/test_preview_text.py` holds it to both. Its XMP metadata stream is not compressed:
  decompressing every stream fails, and Chrome reports that as "TypeError: Failed to fetch",
  which reads like a network error but isn't.
- **What it holds:** every section of the form but one, the procuratore, each "+" row (4 catasto
  groups, 4 titolari, the firm with INPS/INAIL), the declarations unticked, the diritti total.
  About half the text is the portal's boilerplate (privacy notice, domicilio digitale).
- **What it leaves out:** the "Relazione Tecnica di Asseverazione C.I.L.A." section. The form's
  "Visualizza anteprima" is the same `/fnsuap/preview.do` (same 102,912 bytes from the form and
  from Allega documenti), and the portal has no other preview. That section's values read from
  the page itself (14 set fields after opening it from the menu), so a check covers it there.
- **Its quirks:** a long cell wraps onto its own line ("edil.fittizia@pec.exampl" / "e.it": the
  portal's two strings, each placed by its own Tm), the portal writes its own wording ("Maschile"
  in the dichiarante, "Maschio" in TITOLARI), and its boilerplate has its own typos ("D.lgs lgs.",
  "professionist i": one string each, as the portal wrote them). Compare values, not lines.
- **The attachments come back byte for byte.** Each slot's `/fnsuap/download.do?id=…` (a GET with
  the session) gives the stored file. Its sha256 matched the rehearsal's file for all 8 slots
  (`relazione-tecnica.pdf` c760ad6d…, `prospetto-contributo.pdf` f7536169…). `attachments.js`
  returns each file's slot, name, size and sha256 (from "Allega documenti", which it opens if
  another screen is up); a slot's title is the nearest row above its files that is no file, no
  "+", no blank and not the "Tipologie ammesse" line. Run on the rehearsal: 8 files, every slot
  named right.
- **A file in a quadro.** A file attached in a quadro of the form (the receipt of a sanction, quadro d
  of the CILA) is not on Allega documenti: its `download.do?id=…` is on the quadro's own page, which
  the JSF accordion opens by a click that reloads the page (checked 2026-11-10: 894 bytes, the file's
  own hash). `run.py page` records each attached file with its section (`private/shown.json`,
  `attached`); `review.py OUT --quadri` names the quadri whose files no list read so far holds; the skill
  opens each (menu «Compilazione Pratica», then the quadro's link) and runs `attachments.js` there,
  saved as `portal-files-2.json`, `-3`… (review.py merges them). A file no list holds is a `⚠️`.
- **The check.** The skill (step 5) holds each value of the preview to its document in
  `run/check.json` and saves `attachments.js`'s answer as `run/portal-files.json`; `review.py`
  makes a `⚠️` line of each mismatch and of each portal file whose bytes no file of the job has
  (`bench/test_review_check.py`).

Not yet seen: a SCIA or permesso preview (other forms, maybe other writers), a draft with
accented values (the labels' "Località", "è" decode right; no value here had one), a real client's.

## Made-up data and the code window

`run.py page` seals `run.js` and opens a window with the code, which the person types into the
portal's page: right for a real person's data, a nuisance for a rehearsal. Rehearsals with made-up
data pass `--plain`; `bench/rerun.py` builds its scripts without a code. Where no window can open
(a sandbox, a remote shell) `page` stops and says so.

## Large files: the person picks them

In the pane run.js carries at most 16 KB of files (`PAGE_FILES_LIMIT`; 256 KB until 2026-11-07, which no pane call of about 40 KB could take, and run.js stays under 30 KB, `RUN_JS_LIMIT`). Over that, `run.py page`
puts each of the run's files in run.js as `{name, type, size, sha256, picked: true}`, and pre-flight
lists them under `pick`. The runner starts by drawing a box over the portal's page (`askFiles`,
beside the code's `askCode`) that names them with their sizes, takes the files or the job's folder
(`webkitdirectory`: its other files are passed over), and keeps a file only if its size and sha256
are the ones pre-flight read: one with the right name and other bytes is named as "not the file
pre-flight checked". Nothing is filled until every file is in; meanwhile the report says
`waiting`. The bytes stay in the runner's memory, keyed by sha256, never in the tab's storage, so a
runner loaded again asks again; Stop in the box ends the run before anything is filled. A batch
(`bench/rerun.py`) passes `pick=False` and still refuses files over the limit: no one is there to
pick for each run. On the portal 2026-11-04 (`rehearsals/cila-fittizia`, README runs): a CILA with a 5 MB
and a 2 MB file filled in 127 s from a folder picked once; the browser asks before it hands a
folder to the page. Offline tests: `bench/test_inpage.py` (a 3 MB file, a wrong one, a folder,
Stop). The choice and its alternatives: docs/design/large-attachments.md.

A pane without the runner can't take it in one call: it is about 80 KB and a call about 40 KB
(2026-11-04), and a long script copied through the conversation can arrive garbled (2026-10-30).
From an installed plugin, `run.py page` writes `fetch.js` (9 KB for the Prova, 18 KB at most over
the rehearsals' 315 cases), and check.js names it: the page downloads inpage.js and the pratica's
steps file from the plugin's release on GitHub (`plugin-v<version>`, raw.githubusercontent.com,
then cdn.jsdelivr.net; both let any page fetch them), checks each by sha256, and rebuilds this
case's steps from the file: fetch.js carries only the sections that differ from it (choices,
"+" blocks), each field the file has as a reference, and stores the result only if it is run.py's
byte for byte. Nothing of the job's is fetched or sent. `published()` finds the release from the
plugin's `.claude-plugin/plugin.json`; the repo's own copy has none, so it writes no fetch.js.
When fetch.js says `fetch failed` (no network, a host down, bytes other than released), the
bundle below. Offline test: `bench/test_inpage.py` (`fetched`). On the portal (2026-11-07, the
pane, logged in) both hosts answered the page's fetch and the Prova filled with nothing picked.
To try it before a release: the URLs name `plugin-v<version>`, which exists only once released,
so build with plugin.json's version still at the last release (its inpage.js and steps files must
be the same bytes, or fetch.js says `fetch failed`); and the pane keeps the runner and steps
across sessions, so remove `pv-runner` and the case's `pv-steps:` key from the portal's
localStorage first, or check.js names only run.js and nothing is fetched. The pane's storage
held 223 of our keys (8.6 MB) that day, with room for 20 MB more: nothing to prune. run.js in the clear (`--plain`) carries the
sha256 of what it starts with and starts nothing on other bytes (`run.js arrived changed`): on
2026-11-07 a 14 KB run.js copied into the pane lost four of its `false`, and the run looked for a
box the case hasn't. A sealed one needs no check: its seal refuses any change.

The fallback: `run.py page --bundle FILE` writes runner.js, steps.js and run.js as one
file (in the person's Downloads) and `pick.js`, a box on the portal's page where the person picks
it once; it is checked by sha256 and evaluated, which starts the run (then, with big files, the
files box). The batches' `bench/rerun.py --bundle` does the same for many runs.
The skill passes `--bundle ~/Downloads/impresa-in-un-minuto-<name>.js` only after fetch.js failed, and asks the app for the
Downloads folder when it can't write there (`could not write`, e.g. Cowork's sandbox): a tecnico
never downloads or saves a file by hand (2026-11-06, a test where Claude sent files to download).
The box names the file without its extension, and the skill deletes it after the run (it holds
the values).

## Writing new cases: `bench/new_case.py`, `bench/fake_pdf.py`

A branch no case takes (schema_branches.py's "mapped, no case" and "Portal-only boxes untaken")
gets a case: read the box's condition in a steps file (its `when`), then `bench/new_case.py
REHEARSAL BASE NAME '{overrides}'` from a base answers file near the case, answering what
pre-flight asks back until it says ready, and `--write`. A checklist group takes a list of its
items' keys (`"fasce_funzionali": ["fascia_stradale"]`); the other items are then false. A use, a
title or an address the fixture's people don't have is a new made-up person in
`rehearsals/cila-fittizia/fixture-p6.json` (appended in its own one-line style, a codice fiscale
with a valid check letter: the portal checks it). A file a new answer asks for is
`bench/fake_pdf.py rehearsals/<r>/files/<name>.pdf "Title"`, in the layout of the others. The
number boxes of the permesso's previous titles take 8 characters (pre-flight says so). 31 cases
written this way on 2026-11-04 closed 150 of 159 untaken boxes; the nine left can't be a case: five
are the SCIA's sanatoria rows the permesso's stato legittimo inherits by `same_as` and doesn't
show (catalogue/README.md, Limits: a crawl of that section on a permesso draft would drop them),
three the SCIA's whole-building change of use (it goes to the SCIA alternativa), one the agibilità
director's sex (the made-up architect's own).
A fixture person with a second property (`immobile2`) makes every case naming them ask how many
cadastral units the pratica has: give such a property to a new person (2026-11-04: `gemma`, two
flats being merged), never to one the existing cases use. The fixture is plain text, a blank line
between people: append to it as text, never by loading and dumping the JSON (that rewrote 4,000
lines once). A list of several units' values joined by "/" breaks on a categoria (A/2): run.py's
`_categorie` reads them whole.

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
then `results.js` until `done` equals `of`. Where a steps file differs from main's in a few
sections, check.js names `steps/<name>.patch.js` (run.py `patch_script`): only those sections, a
few KB in place of 40-90, the rest taken from the pane's copy when it is main's; it stores the
result only if its sha256 is the new file's, else it says to send the full `steps/<name>.js`
(2026-11-04: the CILA's and the permesso's Dati catastali went this way, by hand, the first time).
The patch is main's steps run through this run.py, so none is written when they no longer plan
here (a filter they name was renamed, a case they refused): then the whole file, or the bundle.
A stopped one: rerun it alone, unchanged, before
calling it a bug (the portal is sometimes slow); twice the same is a bug. 2026-10-29: 20 of
23 on the first pass, 23 of 23 once the runner waited for each section to open.

A rehearsal can be named `NAME:ANSWERS.json` (one pratica, several cases), and a procedure's
later runs travel as what differs from its first. Don't copy files through the conversation, the
queue's either: a long script can arrive garbled (2026-10-30), and so did 13 KB of one case's values
(2026-11-02, an element too many). Each queue piece checks its own length and hash before it joins
the batch and throws if it changed. A case whose made-up data the portal can't save (a company in
the Registro Imprese: the dictionary's `made_up_stops`) isn't written into a batch at all. A case
on other values than the fixture's (an architect born abroad, from a copy of it) goes in the same
batch as `NAME:ANSWERS.json:VALUES.json`; its result is `NAME/ANSWERS@VALUES` and isn't recorded. Pass `--bundle <file in Downloads>`, run `pick.js` in the pane, and the person picks
that file once in the box it shows; it is checked by sha256, loaded once, and starts the batch.
A batch has no fetch.js (its steps aren't a released plugin's): it needs the pick. The pane blocks the portal's page from fetching a local server
(`net::ERR_BLOCKED_BY_CLIENT`, tried 2026-11-01), and its file box can't be set by a script.
A hidden pane slows the page's timers, so a script waiting inside the page outlasts the 45 s
call limit (2026-11-01): `results.js` and catalogue.py's `status.js` wait only while the page
shows and otherwise answer at once, so while it's hidden, wait between polls outside the page
(the pane's `wait` actions in one batch, then `results.js`).
The pane's profile, and so the SPID session, is the same for every session of the app: before a
batch, check that no other chat is running the portal (2026-11-03: one was, with its own batches).
Check the sign-in too, and that the pane shows: a hidden pane on InfoCamere's sign-in page is one the person
can't see to sign in on (2026-11-05: the pane's `tabs_context` says hidden; ask them to show it). An old page
keeps showing Pratiche in bozza after the session has ended, and a
fresh load of `/fnsuap/cmd/home` lands on InfoCamere's "Apache Syncope Login" (`iasu.infocamere.it`)
when it has (2026-11-03, after about three hours; a `fetch` of it from the page fails outright). The
person signs in again; nothing else is needed. When InfoCamere's sign-in itself is down, every route
answers "Application Not Authorized to Use CAS" (the SUE's client `ic.suap.old` and impresainungiorno's `ic.impg`
alike), then "503 Service Unavailable" (2026-11-04 evening, back the next morning): wait, nothing on this side
fixes it. Never open `iasu.infocamere.it/syncope-wa/login` directly: without the `service` a portal sends, its script
fails and the providers never show (a blank SPID tab); start from `/fnsuap/cmd/home`. A new session of the app closes
the pane and may clear the scratch folder: the bundle in Downloads stays, `rerun.py --bundle` with the same names
writes its `pick.js` again, and the `runs.json` already recorded stay. A closed pane reopens on that sign-in page, but the
runner and steps stay in the portal's storage: read it only once the page is back on
`suap.impresainungiorno.gov.it` (2026-11-04: read on the sign-in's origin, it looked empty). Times to plan by (2026-11-03): a CIL or CILA 1½-2 min, a
SCIA 3-4, a SCIA alternativa or permesso 3-8 (one tolerance case 10); 27 runs took 2 h 10 min.
One batch per tab: `loop.js` refuses a second while one runs (two would drive one runner and
file each other's results), and `pick.js` refuses to clear the page during one. A bundle clears
the tab's earlier results first: `loop.js` skips a name it finds there, to resume after a reload.
`results.js` lists each run's `moved` ids and `loose` labels, what a gen.py change is checked by.
A run that stops in ~20 s on "the portal stayed busy" with no section opened is most likely a
sign-in that expired: the runner's frame lands on the login page (2026-10-30). Since 2026-10-31
the run says "signed out" instead, and isn't retried. A load can also pass through the sign-in's
origin on its way back to the portal: a run stopped on "Blocked a frame with origin" (2026-11-03).
The runner now waits for the load that brings the frame back, and says "signed out" if none comes.
A run that never reaches the portal ("the page didn't load", "the portal stayed busy", "signed
out") is kept out of the results, listed apart (results.js `unreached`, since 2026-11-03, when a batch
ended "done" at 26 of 27 without a word), and two in a row halt the batch (`halted` in results.js): once
the portal stuck in its wizard after a 10-minute busy run, and each later run, a new frame each,
failed in about a minute until the page was reloaded (2026-10-31). Then save `record.js`'s output,
reload, and bundle what's left: a bundle clears the tab's results.
One stop on a section the case's answers don't touch, which the batch's other runs of that pratica
filled ("0 fields with this label" after its retries), is the portal's: rerun it before reading the
mapping (2026-11-03: the SCIA's `answers-scavo-vvf` on the Scheda anagrafica; filled unchanged the next day).
The queue goes into the bundle by number: each later run of a procedure is what differs from its
first, so name order (queue-10 before queue-2) broke a batch of 14 pieces (2026-10-31).
A stopped run lists its `gaps`: the empty boxes the portal wants, by label, from the runner's
snapshot (no values), so a stop names them without opening the draft (2026-10-31). A slot holding a
file isn't one, nor one taking only signed files (the person's): until 2026-11-02 every slot was
listed, filled or not, which hid the one missing. `--values`
takes the fixture as it is. After a batch, run `record.js` in the pane and pipe what it prints (names
and results, no values) into `rerun.py --record -`: each run goes in its rehearsal's `runs.json` and its README's run
table: schema_branches.py counts a box as filled on the portal only from there. Stopped runs are recorded too. Record a batch
before bundling the next (a bundle clears the tab's results), and leave `--date` out for a batch
run today: it defaults to today (a guessed date filed a batch under the day before, 2026-11-02).
The batch clears the runner's frame from the page when it ends. A run "unreached" is retried by nobody: bundle the
batch's unreached names (results.js lists them) once it ends. "The page didn't load" on the big SCIA and SCIA
alternativa combinations was the portal composing the pratica past act()'s 60 s ("Composizione della pratica",
2026-11-05). The runner and the crawler now wait on what the portal shows, not on a clock from the click
(inpage.js and crawl.js `until`): they keep waiting while a request is in flight, a page loads or the portal's own
"Attendere prego" / "Composizione della pratica" box shows, and give up only after 20 s (the crawler 15 s) with
none of those and the section still not open, or after a ceiling of minutes (the wizard five, `WIZARD_MS`).

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

Which two operations the wizard takes together is recorded in `sue-wizard.json` `pairs` (wizard.js
`pairs`, catalogue/README.md). Probed 2026-11-03, all 190: the wizard takes any two of different
groups (a title or other adempimento, a terre e rocce box, a landscape procedure, the exemption
parere) and the terre e rocce boxes with each other; two titles, or two landscape procedures, are one
radio group and can't be selected together. None was refused. The pratica's adempimenti are always
both operations' (a terre e rocce box adds two: the SUE's and ARPA Campania's), and its sections are
theirs with nothing new, but a section both have under another title is kept once: the location, the
land register, the diritti, the bollo (a CILA, SCIA, SCIA alternativa or permesso with a terre e rocce
box takes the box's lower-case "localizzazione dell'intervento" and "dati catastali", not its own;
`bench/test_gen.py` holds the rule). So a combination's sections come from its crawl, never from
joining the two operations' lists.

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
fingerprints kept (2026-10-31: the two SCIA in sanatoria combinations). In a new tab or session,
`start.js` (written with every bundle, a few KB) does the same: it checks the pane's stored
`pv-wizard` and `pv-crawl` against the repo's by sha256, removes older frames, and starts the batch
from them, so no file is picked; it says "stale" when a crawler change hasn't reached the pane, and
then pick.js's box is the way (2026-11-05: the SCIA in sanatoria with the landscape proroga and rinnovo,
crawled with no pick in 100 and 130 s, their sections all known). Save the first batch's
results before, or name all of them in export.js: it reads the ops of `crawl:batch`.
A batch whose sections were all seen before is small: `print.js` prints it with its sha256, and
`catalogue.py import -` refuses a copy that arrived changed (no download to ask for), trailing
newlines aside. Over 40 KB print.js packs it (`strings-v1`: each string once, used by index), which
import unpacks; past what that saves (ten three-operation crawls, 64 KB packed, 2026-11-03) it's
export.js and the person's yes to a download. Copy a print one combination at a time
(`window.pvPrintNames = ["<name>"]` before print.js, its own sha256) rather than by hand-split halves.
The pane's JavaScript tool returns the print as one JSON string, quotes and `\"` escapes in: save it as it
came and `import -` decodes it (2026-11-05: unescaped by hand once, a risk the sha256 only catches after).
`import` needs `CATALOGUE_PRIVATE`, a pattern for the portal login's name and codice fiscale, set in the
shell for that command only (never written to the repo): it refuses a crawl that holds them. The declarations
come back `skipped` (the person's, never crawled), not as new sections: a first look at a batch that
counts them as new misreads it. A section's `same_as` can name an op that only ever lived in the pane
(a deeper recrawl, `d4-scia-alt`): import names the repo crawl that holds its fingerprint instead.

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
In a tab where a rerun batch ran, `__crawl` isn't loaded: `catalogue.py pane`'s `load.js` loads the
stored wizard.js and crawl.js once their sha256 is the repo's (2026-11-02, after the receipts' runs).
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

A choice that opens nothing in its section can still add a required slot: the fine lavori's "in
forma parziale come da planimetria allegata" adds "Copia di elaborato planimetrico del progetto
con eventuali varianti [...] opere parzialmente concluse", and a first run with the planimetria
under Allegati liberi stopped on it (2026-11-03). Map a file under Allegati liberi only once a
filled draft shows its answer adds no slot. Every slot's "+" takes more files ("Il pulsante (+)
permette di allegare documenti suddivisi in file multipli", the screen's own note). A slot named
again in a recipe takes its next box: inpage.js `slotBox` finds the slot's boxes by the rows under
its title (`span.input-label`) down to its "+" row, presses "+" (it adds a box with no label under
the last one, and moves every later row down one) and attaches there. A file's "Descrizione" beside
its box is a `span.input-label` too, once a file is in (2026-11-03: a first run read it as the next
slot's title and found no "+"), so a slot ends at its "+" row or at a row holding only a title.
`slotsOf` names a slot's second box by the slot's title too, never by the row of the box above it
(a permesso draft's second Allegati liberi box read "relazione-tecnica.pdf Rimuovi Allega 716,00 B
Descrizione" until 2026-11-03).
Files are read back by name, never by box. The CIL's Allegati liberi takes plain PDFs (its
notifica preliminare, filings and the Soprintendenza's authorization go there, 2026-11-03), and so
does the CILA's (the made-up Allegato A and Modello DP of the second run, 2026-11-03); the landscape
authorizations' take only signed files (their crawls). A slot shows its types ("Tipologie ammesse")
only while it is empty, and its file box has no `accept` of its own: once it holds a file, the cell
shows the file. A slot whose crawl has no types counts as taking plain files; the old crawls of the
CILA and the SCIA lacked them, and a read of their filled drafts (2026-11-03, `accepts_read`) found
each receipt slot ("copia attestazione versamento oneri, diritti e spese") taking only signed files,
the SCIA's procura signed only and its DSC any type, and the slots holding the runs' plain PDFs plain.
