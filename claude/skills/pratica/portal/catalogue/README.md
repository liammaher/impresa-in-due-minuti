# Portal catalogue

What impresainungiorno offers a comune, crawled by program instead of walked by hand, so a
pratica nobody has mapped can still be filled. One folder per comune, named by its codice
catastale (`F839` is Napoli).

## Files

- `<comune>/sue-wizard.json`, `<comune>/suap-wizard.json`: the wizard of each sportello. Every
  operation the comune offers, and for each one alone: the screens after it, the pratica the
  portal generates (its adempimenti, the office each goes to, its sections in order), and
  each option of "Scelte eventuali" tried alone (a Si/No answered Si, a box ticked) with the
  sections it adds or drops. Sections are indices into `sections`.
- `<comune>/sections/<pratica>.json`: one pratica's sections, crawled by `crawl.js`: each
  section's fields (id, kind, label), each choice tried with what it opens, hides and shifts,
  its fingerprint, and the attachments screen's slots (`slots`, read on the screen). A batch
  crawl (`sue-*`, `suap-NNN-*` for sector NNN of `suap-wizard.json`) also holds the pratica the
  portal generated (`generated`: adempimenti and sections), the wizard's screens and each
  scelta's sections (`scelta`); a section seen before is only a reference (`same_as:
  "<pratica>#<section>"`), which `gen.py` follows. Every crawl is named as the batch names it,
  `sue-` and the operation's slug (`catalogue.py` `sue_name`) or `suap-NNN-` and the
  operation's, so its sportello is its prefix. The first seven, crawled one by one, had short
  names until 2026-11-04 (`cila` is `sue-comunicazione-inizio-lavoro-asseverata`; the
  hairdresser's `acconciatore`, with the procura scelta, is
  `suap-011-aprire-l-attivita-di-acconciatore-procura`).
- `<comune>/drift.json`: what the last drift check found changed, per pratica (below).
- `sue-wizard.json` `pairs`: which two operations the SUE's wizard takes in one pratica (wizard.js
  `pairs`, `catalogue.py pairs DIR --bundle FILE`, then `pairs-import` of print.js's text). Every two
  of different groups, both terre e rocce boxes, and one pair per radio group: `together` (the tree
  holds both: false for two radios of one group), then `accepted` with the generated pratica's
  adempimenti and sections, or `refused` with the screen it stayed on and the portal's words.

## How it's made

In the Claude browser pane, logged in, on a scratch draft named "PROVA NON INVIARE -
catalogo <sportello>" (Liam deletes it afterwards). If Pratiche in bozza hasn't it, make it:
`/fnsuap/cmd/create?comune=F839&tipoSportello=E` (the SUE), its name in the description box,
Conferma, then Conferma on the access screen; the draft is listed from then on.

`catalogue.py pane DIR` writes the scripts: on the portal's origin run `load.js` (it runs the
copies kept in the pane's localStorage), and `install.js` only when it says they're stale (it
checks each by sha256 before storing it). A page that navigates loses the scripts but not the
copies: run `load.js` again. A batch's options are worth keeping in localStorage too, so it can be
started again after a logout.

After a crawl.js change that sees more (the switched-on boxes, 2026-10-30): crawl the sportello
again (clear its `crawl:op:*` and `crawl:known`, keeping copies), import it, regenerate every
recipe and diff the steps files, recount (`branches.py --write`), and rerun the changed
rehearsals on the portal before trusting them.

- `wizard.js`: the wizard tree. Takes the defaults past the operations (the preselected
  destinatario, every Si/No answered No, no box ticked), steps back with "Pagina precedente",
  confirms only the portal's "Proseguire senza salvare?" box, and reopens the draft from
  `/fnsuap/cmd/home` when the portal shows its error page. About 8 s per operation, 15 s
  with the scelte tried.
- `crawl.js`: the sections. Tries each radio, checkbox and short dropdown and undoes it with
  the section's Annulla. Never presses Salva. `__crawl.batch({draft, ops, variants})` walks
  many pratiche on the one scratch draft with `wizard.js`'s moves (sector, operation, forward
  with the defaults, each scelta alone): a section whose fingerprint it has seen is not
  crawled again. Each pratica goes to the pane's `localStorage` as it's done (`crawl:op:*`),
  so a batch stopped by a logout resumes where it stopped. 20 to 60 s a pratica once the
  common sections are known (the first restaurant pratica: 140 s).
- `wizard.js` `pairs`: two operations at a time on the scratch draft, forward with the defaults to
  the generated pratica and back, as `start` does one (about 20 s a pair; 190 pairs for the SUE).
  Each result goes to localStorage `wizard:pair:<key>+<key>`, so a probe stopped by a logout
  resumes; `--only KEY` probes the pairs with that operation, `--fresh` probes again.
- `catalogue.py`: `ops sue|suap` lists a batch's operations, `known` the fingerprints the
  stored crawls have, `import` writes an exported batch here (refusing one that holds the
  login's name: `CATALOGUE_PRIVATE`, whole words: `\bname\b`, or a label's "ampliamento" matches a
  "liam"), `count` the distinct sections, how many pratiche use each
  and whether the dictionary fills it under each title the portal gives it (gen.py's own test;
  `names_missing` lists a title with no entry).

Neither fills a value, saves a section, ticks a declaration, pays or sends.

## Where it stands (2026-10-29, `catalogue.py count --summary`)

- **SUE**: all 27 pratiche crawled, and one combination (below); **128 distinct sections**,
  94 filled by the dictionary, 90% of section uses. 22 of the 27 pratiche have every section
  filled, and all 22 have run on the portal with made-up data; the other five (permesso di
  costruire, SCIA, SCIA alternativa, the accertamento di compatibilità paesaggistica, the
  parere for an exemption) need the asseverazioni, the sanatoria and the exemptions' own
  declarations: legal and technical choices more than mapping. Every SUE crawl has its
  attachments screen (`slots`): the four not yet fillable read on an empty draft, so slots
  their sections' answers add may be missing. A slot reads `required` only once the portal has
  checked the screen (after an upload or Prosegui), so a fresh read marks none.
- **A combination**: a CILA with an autorizzazione paesaggistica semplificata in one pratica
  (`sue-combo-cila-paesaggistica-semplificata`) has the union of their sections, each the same
  section as alone (fingerprints), in its own order. A recipe can name both operations
  (`rehearsals/cila-paesaggistica-fittizia`), run to the declarations; its attachments screen
  isn't read yet. Two more (2026-10-29): the SCIA with its semplificata, and with its ordinaria
  (`sue-combo-scia-paesaggistica-*`), every section one already crawled; their attachments
  screens are read on the empty draft, plus the SCIA's answer-dependent slots. Two more (2026-10-31): the
  permesso di costruire with its semplificata and with its ordinaria
  (`sue-combo-pdc-paesaggistica-*`, `catalogue.py ops --combo`), every section one already crawled;
  and the SCIA alternativa with each (`sue-combo-scia-alt-paesaggistica-*`), the same.
- **SUAP**: 278 pratiche crawled so far (the batch stands at about half of its 1,028 trips:
  the priority sectors, the common operations, part of the other sectors); **477 distinct
  sections**, 67 filled, 71% of section uses, counted under each title a section has. 107
  pratiche are filled end to end, 75 more lack one or two sections. The six proven openings were
  crawled again with each "interventi eventuali" tick (`-interventi`: alcohol, an outside sign,
  acoustic papers), and the shops' changes section three deep. The whole tree is 2,333
  sector-and-operation pairs plus 64 common operations, but only the sector's own operations
  (open, take over, move, suspend, close: 710 pairs) differ by sector. The batch in the pane
  (`crawl:ops:suap3`) crawls those in every sector, every other operation once and each of those
  again as a check in one or two other sectors (`like`), which `catalogue.py drift` turns into
  `same.json`. Each scelta is tried once (`variants: "new"`); `gen.py` takes a scelta's sections
  from the pratica where it was tried.
- **Clean reruns** (2026-10-29): every SUE recipe (22 pratiche and the combination), from
  run.py's install.js and run.js in the pane, one after another with nothing touched between
  runs. First: 20 of 23 filled; the three stopped on the fresh load, reading a section before
  it had opened (the Scheda anagrafica's link reloads the whole page), and filled when run again
  unchanged. With the runner waiting for each section to open: 23 of 23 filled, 40 to 150 s
  each.
- Each newly crawled section keeps its own words (`text`: its intro and notes, never a box's
  content), which say what a box means, for the drafter and for whoever checks a draft.
- Proven on the portal with made-up data, generated from a batch crawl: the openings of a
  restaurant, a non-food shop, a bakery and rooms to let, the takeover (subingresso) and the
  suspension of a shop and of a restaurant, a restaurant's new name, a shop's bigger sales area,
  a restaurant's alcohol notice, and a restaurant's closure (SUAP); on the SUE all 22 pratiche
  with every section filled and the CILA with its semplificata (the clean reruns above).

- **Terre e rocce** (2026-11-03): every pair of operations probed (`sue-wizard.json` `pairs`, 190,
  none refused), then each title with the dichiarazione di utilizzo (`sue-combo-*-dichiarazione-utilizzo`)
  and each title with a landscape procedure and the dichiarazione, three operations
  (`sue-combo-*-paesaggistica-*-dichiarazione-utilizzo`): 15 crawls, every section one already crawled,
  their attachments screens read on the empty draft and again on the filled one. All 15 filled on the
  portal with made-up data. A crawl's `same_as` naming an op the repo hasn't (a pane-only recrawl,
  `d4-scia-alt`) is renamed on import by fingerprint.

## Drift

A section's fingerprint is a hash of what it shows before any choice: ids, kinds, labels,
lengths, short dropdown lists. `__crawl.batch({..., check: true})` reads only those (about 1 s
a section) into `crawl:check:*`; `catalogue.py drift EXPORT.json` compares them with the
stored crawls and writes `drift.json`. A pratica with a difference is refused by `gen.py` and
by `run.py preflight` until it is crawled again (`import` clears it).

A check of the SUE: `catalogue.py ops sue --all > ops.json`, then `catalogue.py pane DIR --bundle
~/Downloads/pv-drift-sue.js --ops ops.json --check`, picked in the pane (about 10 minutes for the
27 operations). The batch's `since` is today, so a check another day left in the pane's storage is
done again (2026-11-02: six from 28 October were reused, unnoticed, until cleared by hand). Then
`digest.js` prints one short digest a pratica, sha256 first, for `catalogue.py drift --digests -`:
the same are recorded, and the others are named; set `window.pvCheckNames` to them, run
`check-print.js`, and give its text to `catalogue.py drift -`. 2026-11-02: 27 of 27 the same.

## Limits

- One comune's view on one day: the portal changes, so a drift check (above) stops runs of a
  changed pratica. Between checks, the runner's label checks still stop a run on a moved box.
- The fingerprint is the section before any choice: a change only inside a branch is caught by
  the runner, not by the check. The same holds for `same_as`: two pratiche's sections with one
  fingerprint are kept once, though a choice may open other rows in each. The permesso's "stato
  legittimo, dichiarazione tolleranze, sanatoria" is kept as the SCIA's, whose sanatoria choice
  opens the SCIA in sanatoria's rows; on the permesso those rows aren't there (2026-11-04, a run
  stopped on "un intervento soggetto a SCIA: 0 fields"), so its recipes refuse that answer. A
  section shared by `same_as` whose branches matter is read on the pratica's own draft first.
- Operations are crawled one at a time; combinations (two operations in one pratica, an
  intervento eventuale) are only what each adds on its own, except the five above.
- Crawls before 2026-10-30 didn't record switched-off boxes: a block greyed until its choice
  is made (quadro f)'s stato legittimo) read as a choice that opens nothing, and its own choices
  were tried while greyed, doing nothing. crawl.js now marks `disabled`, a node's `enables` and
  `disables`, and explores what a choice switches on; a SUE crawl from before misses such
  branches until crawled again (depth 3 for the stato legittimo's sub-choices).
- Names aren't identity: two sections with different titles can hold the same fields, which
  the section crawl settles.
