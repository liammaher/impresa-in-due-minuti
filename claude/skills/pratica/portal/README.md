# Portal runner: adding a pratica, running it, checking them all

How a pratica on impresainungiorno (the SUAP and SUE front office) goes from crawled to
filled, as the 23 SUE recipes did. The crawl itself is in `catalogue/README.md`; the
person-facing flow (pre-flight questions, the review page) is in the pratica skill.

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
   with `__crawl.sectionOf(draft, section)`.
2. **The recipe** (`rehearsals/<name>/recipe.yaml`): procedure, title, comune, sportello,
   crawl, operation (or a list of them), scelte, `first`, `asks`, `yours` (what's left to the
   person: declarations, attachments, payment, signing), `supports` (the cases refused, with
   why: all or nothing; `if:` checks one only once its gate holds, asking it only then).
   A scelta only some cases take is `{option, when}` (co-holders, a new direttore, the others'
   assent): run.py ticks it, and keeps the sections it adds, only when its `when` holds. Until
   2026-11-02 every scelta was fixed, so a voltura always had a co-holder and a cambio
   d'intestazione never did, whatever the case said.
   Copy a sibling: `rehearsals/paesaggistica-ordinaria-fittizia`.
   **Two operations in one pratica** (a building pratica with its landscape authorization): the
   recipe `extends: [<main pratica's rehearsal>, parts/<the other's part>]` and states only what is
   its own (procedure, title, crawl, operation list, `descrizione`, `yours`, `rules.main`). Later
   ones win key by key; `attachments`, `supports` and `sections` add up; `asks` and `rules` merge,
   each of their keys replaced whole (three operations state both `handles`); `yours` is replaced,
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
   A new fact multiplies the table's cases by its values: with `terre_rocce` (three) the library's
   validator walks 34 million combinations (8 minutes; it built them as one array and ran out of memory
   until 2026-11-03) and `bench/test_rules.py` about 45 minutes; the existing cases then answer it as
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
   if any field is unaccounted for. Regenerate every rehearsal after a dictionary, recipe or gen.py
   change (`bench/regen.py`: every steps file and combination's answers; test_gen fails while one is
   stale) and look at the diff: an unrelated steps file that changes is a regression until
   shown otherwise. `bench/plan_diff.py` says what the change does to each case (its fill plan
   before and after). A new question the existing cases reach makes their pre-flight propose
   or ask it: answer it in each as the case did before, and plan_diff shows them unchanged, so
   their recorded runs still stand. Add the keys as text: rewriting a file with `json.dump` reflows
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
   README (`| Date | Browser | Result |`): what stopped it and what fixed it, then the
   filled run. Both records count: coverage.md's "Run on the portal" reads the README's dated rows,
   schema_branches.py the `runs.json` that `rerun.py --record` writes (2026-11-03: ten rehearsals
   recorded only in runs.json read as never run). Where a case fills blocks that share labels (technicians, firms), read its draft's
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
  would have stopped a run, and every rehearsal's address was a Via, so none did. Neither has been
  seen on the portal with a Vico yet.
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
  scelta the case needs; gen.py ticks them all.
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
  `alerts` lists each by section and the box's label (no value), results.js counts them, and the
  person's review shows them to check.
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
later runs travel as what differs from its first. Don't copy files through the conversation, the
queue's either: a long script can arrive garbled (2026-10-30), and so did 13 KB of one case's values
(2026-11-02, an element too many). Each queue piece checks its own length and hash before it joins
the batch and throws if it changed. A case whose made-up data the portal can't save (a company in
the Registro Imprese: the dictionary's `made_up_stops`) isn't written into a batch at all. A case
on other values than the fixture's (an architect born abroad, from a copy of it) goes in the same
batch as `NAME:ANSWERS.json:VALUES.json`; its result is `NAME/ANSWERS@VALUES` and isn't recorded. Pass `--bundle <file in Downloads>`, run `pick.js` in the pane, and the person picks
that file once in the box it shows; it is checked by sha256, loaded once, and starts the batch.
No way around the pick: the pane blocks the portal's page from fetching a local server
(`net::ERR_BLOCKED_BY_CLIENT`, tried 2026-11-01), and its file box can't be set by a script.
A hidden pane slows the page's timers, so a script waiting inside the page outlasts the 45 s
call limit (2026-11-01): `results.js` and catalogue.py's `status.js` wait only while the page
shows and otherwise answer at once, so while it's hidden, wait between polls outside the page
(the pane's `wait` actions in one batch, then `results.js`).
The pane's profile, and so the SPID session, is the same for every session of the app: before a
batch, check that no other chat is running the portal (2026-11-03: one was, with its own batches).
Check the sign-in too: an old page keeps showing Pratiche in bozza after the session has ended, and a
fresh load of `/fnsuap/cmd/home` lands on InfoCamere's "Apache Syncope Login" (`iasu.infocamere.it`)
when it has (2026-11-03, after about three hours; a `fetch` of it from the page fails outright). The
person signs in again; nothing else is needed. A closed pane reopens on that sign-in page, but the
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
fingerprints kept (2026-10-31: the two SCIA in sanatoria combinations). Save the first batch's
results before, or name all of them in export.js: it reads the ops of `crawl:batch`.
A batch whose sections were all seen before is small: `print.js` prints it with its sha256, and
`catalogue.py import -` refuses a copy that arrived changed (no download to ask for), trailing
newlines aside. Over 40 KB print.js packs it (`strings-v1`: each string once, used by index), which
import unpacks; past what that saves (ten three-operation crawls, 64 KB packed, 2026-11-03) it's
export.js and the person's yes to a download. Copy a print one combination at a time
(`{"crawl:op:<name>": ...}` with its own sha256) rather than by hand-split halves. The declarations
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
