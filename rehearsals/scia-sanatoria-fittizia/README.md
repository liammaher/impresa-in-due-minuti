# SCIA in sanatoria: generated and walked

The SCIA rehearsal's job (rehearsals/scia-fittizia: new shutters and railings of another design on
the facade, two partitions, a bathroom, the systems) found done without a SCIA. Same people and
made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations, signing and
sending.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`: the SCIA's crawl
(`catalogue/F839/sections/scia.json`, which tried the wizard's sanatoria scelta), `dictionary/fnsuap.yaml`,
and the wizard's "Le opere ricadono nell'ambito della Sanatoria ...?" answered Sì, which adds the
quadro "SANATORIA e regolarizzazioni per interventi già realizzati e in corso di esecuzione".

## What it covers (2026-11-01)

The SUE rules table (`rules/sue-napoli.yaml`) gives this pratica (`napoli/comune/scia-in-sanatoria`)
for works already done or under way that a SCIA needed: manutenzione straordinaria on the facades
or the structures, restauro on the structures, or a ristrutturazione, with no change of use,
outside a bene culturale. Interior works only are the late CILA's.

- **In corso** (art. 37 c. 5 DPR 380/2001): works still under way, the SCIA filed of one's own
  accord with the €516 sanction, paid and given by its reference and date; the asseverazione's
  start date.
- **Doppia conformità** (art. 36-bis c. 5 b): works done, conforming to the planning and
  building rules both then and now; the date, the oblazione the technician determines (€516 to
  €5,164) paid and given by amount and date, in both quadri.
- The asseverazione: the stato legittimo also from this sanatoria, the SCIA "presentata in
  sanatoria", the catasto (unchanged, DOCFA filed, or to file once it takes effect).
- **Works on structures** (2026-11-01): in Campania structural works begun without the seismic
  filing always need the autorizzazione sismica (art. 4 c. 1 e L.R. 9/1983), so the asseverazione's
  sismica quadro says "prevede opere strutturali soggette ad autorizzazione sismica" and attaches
  the documents for it, the strutturista goes in quadro h1, and the table adds the autorizzazione
  at the Genio Civile, filed apart (`sismica-sanatoria`); a deposito or a variant filing is refused
  at pre-flight. On the portal the art. 36-bis c. 3-bis box (seismic zone, structural relevance,
  art. 94-bis class, authorization attached or silenzio assenso) shows only under the c. 1 case,
  already refused for its defect; with double conformity and for works under way the sismica
  quadro is the form's only place, and the c. 3-bis attestation (the technical rules of the time)
  goes with the authorization's documents. `answers-strutture.json` (beams of a timber floor
  replaced in 2019, double conformity) and `answers-ristrutturazione-strutture.json` (a roof
  rebuilt, works under way).
- **In a protected landscape area** (art. 36-bis c. 4 and 5-bis): works that needed a landscape
  authorization (semplificata or ordinaria), new surfaces or volumes included. The asseverazione
  says the intervento goes through the accertamento of landscape compatibility of art. 36-bis and
  attaches the documents for the binding parere the Sportello asks for; the sanction of c. 5-bis
  follows the assessment, after filing. Only with double conformity: the SCIA of works still
  under way is refused there. `answers-paesaggio.json`, filled on the portal 2026-10-31.
- **Landscape works still to come** (works under way, art. 37 c. 5): the landscape authorization
  is asked with the sanatoria, the two operations in one pratica
  (`rehearsals/scia-sanatoria-paesaggistica-*`); it can't be given for works already done (art.
  146 c. 4 D.Lgs. 42/2004). `sanatoria_paesaggio` says which: done (the art. 36-bis route) or to
  come (the authorization).
- The sanatoria's own required slot, "Elaborati richiesti per la sanatoria (stato legittimo, stato
  di fatto e comparativi)", takes only signed files (.p7m): the technician's, in the person's steps.

Refused at pre-flight, with the reason:

- **Conformità urbanistica** (art. 36-bis c. 1, €1,032 to €10,328): on the portal the
  asseverazione's dating (by documents or by attestation), its oblazione and its works proposal
  (art. 36-bis c. 2) are one radio group though the form asks for all three: ticking one unticks
  the others (seen 2026-10-30). Checked again on a draft 2026-11-01: the four rows (dating by
  documents, dating attested, oblazione, "ai fini della sanatoria") are one field with the values
  1 to 4, so the portal can save only one of them, where the national form keeps the dating, the
  oblazione and the works choice apart. A defect of the portal, not a gap in the mapping
  (`docs/portal-defects.md`): the asseverazione can't state the case. Ask the SUE.
- **Variants to pre-1977 titles** (art. 34-ter c. 1-3): the law asks for the variant's date (by the
  art. 9-bis documents, else the technician's attestation, c. 2) and the oblazione of art. 36-bis c. 5
  (c. 3). On the portal the asseverazione's three rows (dating by documents, dating attested,
  oblazione) are one field with the values 1 to 3: ticking one unticked the others (read on a made-up
  draft 2026-11-02, cancelled). A defect of the portal (`scia-34ter`, `docs/portal-defects.md`): the
  case is refused. The quadro's own rows work (the varied title and the payment are two fields).
- Structures, bene culturale, changes of use, a permesso's works: the table's.

The payment goes by its references or its receipt (`sanatoria_prova`): read on both filled drafts
(2026-11-02), the receipt adds no slot of its own, so it goes signed in "copia attestazione versamento
oneri, diritti e spese" (.p7m only), the person's. With double conformity the receipt row asks the
amount again, a decimal box. `answers-ricevuta.json` and `answers-in-corso-ricevuta.json`. The Comune's SCIA form (23/06/2025) still says cases d.2 to d.4 go on
paper; DD 501/2026 makes the portal the only channel from 1/7/2026, and the portal offers them.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-10-30 | pane | `answers-p6.json` (doppia conformità) | First try stopped on Tipologia: "presentata in sanatoria" ticked before the intervention type, whose id then landed on it (now ticked last, by label). Rerun from a blank draft: every section filled and read back on a fresh load (150.6 s, fresh load 24.7 s); then the sanatoria drawings slot turned out to take only .p7m (moved to the person's steps) and the attachments resumed on the same draft (7.9 s): **filled**, 7 files kept |
| 2026-10-30 | pane | `answers-in-corso.json` (art. 37 c. 5) | **Filled** from a blank draft in 143.4 s, read back on a fresh load (24.2 s), 7 files kept |
| 2026-10-30 | pane | `answers-p6.json`, after the sanatoria choice became `sanatoria_titolo` (shared with the permesso) | **Filled** from a blank draft in 149.2 s, read back on a fresh load (25.0 s), nothing moved or loose |
| 2026-10-30 | pane | `answers-in-corso.json` | **filled** |
| 2026-10-30 | pane | `answers-p6.json` | **filled** |
| 2026-10-31 | pane | `answers-paesaggio`: works in a protected area, the art. 36-bis c. 4 route, `bench/rerun.py` bundle | **filled** in 140 s, nothing moved or loose |
| 2026-11-01 | pane | `answers-strutture`: timber floor beams replaced, double conformity, the sismica quadro's autorizzazione and the strutturista, `bench/rerun.py` bundle | **filled** from a blank draft in 162 s, read back on a fresh load, nothing moved or loose |
| 2026-11-01 | pane | `answers-ristrutturazione-strutture`: a roof rebuilt, works under way (art. 37 c. 5), same bundle | **filled** from a blank draft in 151 s, read back on a fresh load, nothing moved or loose |
| 2026-11-02 | pane | `answers-in-corso-ricevuta`: works under way, the €516 sanction's receipt attached, `bench/rerun.py` bundle | **filled** in 153 s, read back on a fresh load, nothing moved or loose |
| 2026-11-02 | pane | `answers-ricevuta`: double conformity, the oblazione's receipt | First try stopped: the receipt row's "di euro" is a decimal box, which read 516 back as 516,00 (now `kind: number`). Rerun: **filled** in 146 s, nothing moved or loose |
| 2026-11-02 | pane | two art. 34-ter cases (title by estremi, dating by documents, payment by estremi; title by the art. 9-bis documents, dating attested, receipt) | Both stopped in the asseverazione on the dating's date box ("è: 0 fields with this label"), each retried twice by the runner as a slow portal. The saved draft held the oblazione ticked and the dating unticked: the read-back after Salva couldn't find the date box the oblazione's tick had hidden. The dating and the oblazione are one field: the case is refused as a portal defect (`scia-34ter`), the answers files dropped, and the runner now says "not kept … hidden by a later choice" and doesn't retry it |
| 2026-11-02 | pane | `answers-cambio-uso`: one unit changed from a professional office to a tailor's workshop in 2021 without the SCIA (same category, art. 23-ter), with CILA-level works, double conformity, `bench/rerun.py` bundle | **filled** from a blank draft in 171 s, read back on a fresh load, nothing moved or loose |
| 2026-11-02 | pane | `answers-ricevuta.json` | **stopped** in 105 s |
| 2026-11-02 | pane | `answers-in-corso-ricevuta.json` | **filled** in 153 s |
| 2026-11-02 | pane | `answers-ricevuta.json` | **filled** in 146 s |
| 2026-11-02 | pane | `answers-p6.json` | **filled** in 150 s |
| 2026-11-02 | pane | `answers-cambio-uso.json` | **filled** in 171 s |
| 2026-11-03 | pane | `answers-variante-scia`: a variant to a 2022 SCIA built without depositing it, double conformity, the varied SCIA's number and date, `bench/rerun.py` bundle | **filled** from a blank draft in 161 s, read back on a fresh load, nothing moved or loose |
| 2026-11-04 | pane | `answers-catasto-dopo.json` | **filled** in 180 s |

<!-- /runs -->

Exploring by hand first (a blank draft with only the wizard, then ticking each case) showed the
four cases' rows and the case-3 radio group. Opening the sanatoria quadro right after saving an
asseverazione section twice sent the portal back to its home page; opening it from the Scheda
anagrafica, and in both runs, worked.

The plain SCIA's P6 (rehearsals/scia-fittizia) on the steps regenerated with these entries: filled
in 140 s, read back on a fresh load (23.4 s).
