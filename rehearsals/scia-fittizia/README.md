# SCIA edilizia: works on structures, and every protection the asseverazione names

The SCIA for the CILA rehearsal's job: the architect with a procura designs and presents, the
tenant client, the owner company, two firms, and for works on structures Davide Esempio, the
structural engineer (`s:`). Made-up data (an invented 1965 licenza, PRG zone and article,
FAC-SIMILE documents in `files/`); each draft is "PROVA NON INVIARE" and stops before the
declarations, signing and sending.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`, the crawl of an empty draft
(`catalogue/F839/sections/scia.json`: 36 sections, 319 choices) and `dictionary/fnsuap.yaml`.
The wizard's required Si/No (sanatoria) is answered No (`si_no` in the recipe).

## What it maps

- **What it files** (quadro c) and the asseverazione's tipologia): manutenzione straordinaria,
  restauro e risanamento conservativo or ristrutturazione edilizia (art. 22 c. 1 a) to c) DPR
  380/2001), each changing the use or not (one unit within its category, one unit in zone A, B
  or C to another category, a whole building within its category: art. 23-ter as the 2024 Salva
  Casa changed it); a variant in corso d'opera to a permesso di costruire or to a SCIA (essential
  or not), naming the title it changes; or a change of use alone, of a unit or a whole building,
  with no works or CILA works (art. 6-bis).
- **The contributo** (quadro g): free (the rule why), or due: paid (its receipt), before the
  works, in instalments or during the works, worked out on the architect's prospetto or by the
  SUE (the documents it needs). Each adds its slot.
- **With a landscape authorization**: the SCIA and the semplificata or the ordinaria in one
  pratica are their own recipes (`rehearsals/scia-paesaggistica-*-fittizia`), the asseverazione
  naming the procedure.
- **Structures.** The structural designer, another technician, in h1)'s block under the
  architect's (their albo, residence and studio); concrete or steel works and their art. 65
  denuncia; the seismic filing (Napoli is zone 2: L.R. Campania 9/1983, Reg. 4/2010): a
  deposito, an authorization, or a non-substantial variant to a project already filed (its
  protocol and date). Each filing's documents go in their own slot.
- **Protections**, one answer each, as the asseverazione's four quadri ask them: the
  landscape (none, or protected with works that need no authorization), the building as a
  bene culturale (the Soprintendenza), a protected natural area, the vincolo idrogeologico and
  idraulico, a VINCA, a cemetery's fascia, major-hazard plants (RIR), other ecological vincoli,
  and the fasce di rispetto (road, rail, power line, gas, military, airport, another).
- **Systems, energy, barriers, acoustics, fire, asbestos, hygiene** (the asseverazione's
  technical quadri, shared with the SCIA alternativa): every kind of system installed (one
  project per system where DM 37/2008 asks one, "altre" with its name); the energy report
  (art. 125), the renewables obligation (D.Lgs. 28/2011) and the energy incentives (art. 14 D.Lgs.
  102/2014, the 5% bonus); the barriers rules (art. 77 with its requirements, art. 82 for a
  building open to the public, or a deroga asked); art. 8 L. 447/1995 (each acoustic document
  it attaches) and the passive requirements; excavated earth; fire prevention (rules met, a
  deroga, or the Vigili del Fuoco's assessment of the project); asbestos (the piano di lavoro);
  hygiene (conforming, under art. 24 c. 5-bis with its cases, or a derogation); a cemetery's
  fascia where the works aren't allowed (the deroga). Each "si allega" adds a required slot.
- **A SCIA condizionata.** When any of those needs an assent or a deroga, the request's
  documents go in the slot the answer adds, and section b) gets no start date: the works start
  once the SUE says the assents are in (the section's own text; the date isn't required).
- **The attachments screen** changes with the answers: each "si allega" adds a required slot,
  one per fascia for the tutela funzionale, one per system's project. All take plain PDFs
  (recipe `attachments`, `on_page`).

Refused at pre-flight: what the rules table gives to another pratica (a landscape
authorization: the SCIA with it is its own recipe). Not mapped: the fire-safety variant of a
project the Vigili del Fuoco already approved (the form's last fire option, never offered), and
the excavated earth as by-products or under a VIA/AIA. The architect as structural designer
too isn't mapped (her studio is the business's).

## Cases from the schema table (2026-10-30)

Written from `docs/schema-branches.md`, one answers file per group of options of the national
form no case took. Each passes pre-flight offline; **none has been run on the portal yet**.

- `answers-senza-impianti.json`: the P6 works with no systems touched.

Planning instruments (quadro 3, 2026-10-31): the PRG is always ticked; any other instrument
in force or in salvaguardia is one checklist behind one yes/no, each found by the block its
box opens. Ready offline, **not yet run on the portal**:

- `answers-strumenti.json`: a PUC adopted, a PUA, a piano particolareggiato and a piano di recupero over the area, each with its zone and article, beside the PRG.

## Runs

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-28 | pane | P6 (plain) | several legs on one draft; 198 values and 7 attachments kept, every value read back on a fresh load |
| 2026-10-29 | pane | structures (deposito, art. 65, road fascia self-certified) | every section filled first time; stopped at Allega documenti on 3 required slots the answers add (read there, then mapped) |
| 2026-10-29 | pane | every protection needing an assent (restauro, seismic authorization) | every section filled first time, no start date accepted; stopped on 15 new required slots (read, mapped) |
| 2026-10-29 | pane | seismic variant, RIR area not mapped, self-certified vincoli (ristrutturazione) | every section filled first time; stopped on 4 new slots (read, mapped) |
| 2026-10-29 | pane | structures, from scratch | **filled** in 150 s with 10 attachments; fresh load 23 s, every value read back |
| 2026-10-29 | pane | every protection, from scratch | **filled** in 167 s with 22 attachments; fresh load 26 s, every value read back |
| 2026-10-29 | pane | seismic variant, from scratch | **filled** in 153 s with 11 attachments; fresh load 23 s, every value read back |
| 2026-10-29 | pane | P6 (plain), from scratch | **filled** in 136 s with 7 attachments; fresh load 23 s, every value read back |
| 2026-10-29 | pane | variant to a PdC (contributo paid, prospetto), then a change of use alone (unit, CILA works, between categories; contributo worked out by the SUE) | every section filled first time; each stopped at Allega documenti on the slots quadro g) adds (the prospetto, the receipt, the SUE's calculation documents), read and mapped |
| 2026-10-29 | pane | batch of all six cases from scratch, the three earlier ones now also changing the use (whole building, same category, between categories) | **5 of 6 filled** (P6 206 s, structures 166 s, every protection 218 s, seismic variant 168 s, change of use 155 s), each read back on a fresh load; the PdC variant stopped once on the firms' section, a box not yet on the page |
| 2026-10-29 | pane | PdC variant, rerun unchanged (after one more stop on the portal's "errore inatteso" page) | **filled** in 205 s, read back on a fresh load (31 s) |
| 2026-10-29 | pane | batch of the five cases not yet run, from scratch, with the runner that retries the portal's own errors: a variant that is a variazione essenziale; a change of use alone, of a unit with no works (within its category, between categories) or with art. 6-bis works (within its category), and of a whole building with 6-bis works | **4 of 5 filled** (essential variant 275 s, unit without works within its category 207 s, unit with 6-bis works 202 s, whole building 307 s), each read back on a fresh load, none needing a retry; the unit between categories stopped on Localizzazione, a street's suggestion list still fading out over "scala" |
| 2026-10-29 | pane | unit without works between categories, rerun with the runner that takes a fading list off the page | **filled** in 227 s, read back on a fresh load (62 s) |
| 2026-10-29 | pane | P6 as now (manutenzione straordinaria that changes the facades, since internal works alone are a CILA's under the SUE rules table), `bench/rerun.py` with the CIL and the SCIA with its ordinaria | **filled**, read back on a fresh load (24 s); the portal's error page once at DOMICILIO ELETTRONICO, resumed by the runner (47.5 s after the resume) |
| 2026-10-31 | pane | the planning instruments (`answers-strumenti`), and the P6 again with the PRG rows found by label (`anchor: PRG`), `bench/rerun.py` bundle | **filled** both (137 s, 135 s), nothing moved or loose |

What the 2026-10-28 stops taught (each fixed for every pratica):

1. The wizard reported "filled" while the portal refused its CONFERMA (the required Si/No):
   its screen check read the whole page, whose menu lists every screen. It now checks the
   title and answers Si/No questions (`answers`).
2. The licence number box takes 8 characters: the crawler now records each box's maximum
   and `run.py` refuses a longer value before the run.
3. The safety quadro's "e allega alla presente segnalazione la notifica" shows only with the
   notifica answer: `on_page` in the dictionary (by label, skipped where absent).
4. Surface and volume came back as "85.00": decimal boxes are compared as numbers.
5. After a resume the fresh-load check read a moved id: read-back now finds it by label too.
6. One regression of mine, caught by the run: a label-reader change let the box to the left's
   label count (the firms' block). Narrowed to skip only leading validation messages.

Still the person's: the "Documentazione dimostrativa dello stato legittimo" slot (signed
files only, `.p7m`), the procura and the "Quadro riepilogativo - SCIA DSC" (portal
documents), naming the direttore dei lavori (and the structures' one), the declarations,
signing and sending.
| 2026-10-29 | pane | the technical quadri (answers-tecnici: a shop open to the public, systems with their projects, energy report, renewables, art. 14 c. 6, barriers art. 77 and 82, acoustics art. 8 and DPCM, VVF assessment, asbestos, art. 24 c. 5-bis) | every section through fire and acoustics filled first time; stopped on the 5-bis's three cases the crawl never saw (read, mapped); resumed past it, stopped on 13 new required slots (read, mapped) |
| 2026-10-29 | pane | every deroga (answers-deroghe: barriers, fire, hygiene, a cemetery's fascia; gas and another system) | stopped on the other system's required "specificare" (mapped), then on 8 new required slots (read, mapped) |
| 2026-10-29 | pane | every deroga, from scratch | **filled** in 153 s with 16 attachments; fresh load 22 s, every value read back; no start date accepted |
| 2026-10-29 | pane | the technical quadri, from scratch | stopped on art. 24 c. 5-ter's conditions, which each 5-bis case opens below it (read; mapped, one case per pratica) |
| 2026-10-29 | pane | the technical quadri, from scratch, with the 5-ter conditions | **filled** in 149 s with 20 attachments; fresh load 23 s, every value read back |
| 2026-10-29 | pane | P6, structures and every protection, from scratch after the technical quadri's dictionary change (one batch) | **filled**: 186 s / 147 s / 161 s, every value read back; no retry |
| 2026-10-30 | pane | P6, from scratch after the sanatoria choice (`sanatoria_titolo`) replaced `scia_sanatoria` (one batch with the PdC P6 and the SCIA sanatoria) | **filled** in 138 s; fresh load 24 s, every value read back |
| 2026-10-30 | pane | Quadro f)'s stato legittimo, one batch of six (`answers-stato-*.json`, `bench/rerun.py scia-fittizia:<answers>`) | **filled**: all 13 kinds of title (148 s), sanctions with the payment's details (129 s), tolerance declarations (132 s), every value read back. **Stopped**, nothing wrong saved: built before titles and title lost on the primo impianto line's date ("covered by" its calendar: switched off), because two boxes with no text the crawl never saw choose its details (they switch n. and del on) or its copy, uploaded inside the quadro: both now refused until mapped. Sanctions with the receipt filled the form and stopped on Allega documenti's new required slot "Ricevuta/e di versamento a titolo di sanzione": now mapped (`ask.sanzione_ricevuta`), not yet rerun. |
| 2026-10-30 | pane | every protection (`answers-tutele`) after gen.py's offset fix (the fasce's second "Specificare:" `r16c1p16reg:txt` → `r14c1p14reg:txt`), `bench/rerun.py` bundle | **filled** in 180 s, read back on a fresh load (25 s), nothing moved or loose: the new id is the box's |
| 2026-10-30 | pane | asseverazione tolerances (`answers-tolleranze-asseverate`: 1-bis at 6% and c. 2, under 60 m², zone 2, not structural), `bench/rerun.py` bundle | stopped on "Asseverazione SCIA - Stato legittimo": the sanatoria's si/no left empty ("il valore è obbligatorio" twice). The runner's label "no" (nth 3) had matched "non ha rilevanza strutturale", which the tolerances show above it |
| 2026-10-30 | pane | the same, rerun with a yes or a no read as a whole word (`startsLabel`) | **filled** in 152 s, read back on a fresh load (28 s), nothing moved or loose |
| 2026-10-30 | pane | Quadro f)'s two former refusals after #129, one `bench/rerun.py` bundle of five: two titles of one kind (`answers-stato-titoli-ripetuti`: a second DIA, a second condono and a CILA on three "altro" lines, two "+"), built before titles and title lost, each with the primo impianto's details and with its copy (`answers-stato-{epoca,prova}[-copia]`) | **filled**, all five (137 s, 146 s, 136 s, 143 s, 132 s), read back on a fresh load, no retries, nothing moved or loose. The unlabeled boxes went by label and nth as mapped: the details box switched n. and del on, the copy box opened the upload in the quadro; the title-lost line's boxes, never crawled, were found on the page |
| 2026-10-30 | pane | A structurally relevant tolerance's art. 94-bis class (boxes read on the page: the crawl stops at the three class radios), `bench/rerun.py` bundles: relevant with the Genio Civile's authorization (`answers-tolleranze-autorizzazione`) and with its silenzio assenso (`answers-tolleranze-silenzio`) | silenzio assenso **filled** (201 s). The authorization filled every section and stopped on Allega documenti's new required slot "Autorizzazione sismica" (plain PDFs taken): mapped (`ask.toll_sismica_doc`) in the 8 recipes that fill that screen, rerun **filled** (137 s), read back on a fresh load, nothing moved |
| 2026-10-30 | pane | another technician appointed (`answers-altri-tecnici`: H2, the CILA's G2 block) | **filled** in 140 s, read back on a fresh load (22 s), nothing moved or loose |
| 2026-10-31 | pane | two other technicians (`answers-altri-tecnici-due`: H2 repeated by "+", the first a firm's employee) | **filled** in 169 s after the employer's boxes were mapped, read back on a fresh load (24 s), nothing moved or loose |
| 2026-11-01 | pane | `answers-altri-tecnici-otto` and `answers-stato-titoli-dieci` (eight other technicians, ten "altro" title lines: limits raised from three and five), `bench/rerun.py` bundle | **filled** both (707 s, 152 s) |
| 2026-11-01 | pane | `answers-direttori` (another architect directs, `d:` above the structural designer's block, which is then the second; the structural designer directs the structures; a firm with its Cassa edile; more technicians to come) **filled** (189 s); `answers-impresa-dopo` (the architect directs, the structural director and the firm named later, d.lgs. 81 "si riserva") **filled** (142 s), `bench/rerun.py` bundle, read back on a fresh load, nothing moved or loose |
| 2026-11-02 | pane | `answers-progettista`: another architectural designer (`p:`), another director (`d:`) and the structural designer (`s:`), `bench/rerun.py` bundle | **filled** in 191 s; h1 read on the draft after: the designer's block first, then the director's, then the structural designer's (blocks 1, 2, 3); the asseverazione's progettista is the designer. `answers-direttori` rerun unchanged: **filled** |
