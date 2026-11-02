# Permesso di costruire in sanatoria: generated and walked

A room added on the roof terrace of the CILA rehearsal's building, with a high-performance
envelope, found built in 2019 without a permesso (`answers-p6.json`), or built in 2020 larger than
its permesso allowed (`answers-parziale.json`). Same people and made-up data; the draft is "PROVA NON INVIARE" and stops
before the declarations, signing and sending.

`portal-steps.generated.yaml` is `gen.py`'s, from `recipe.yaml`: the permesso's crawl
(`catalogue/F839/sections/sue-permesso-di-costruire-art-10-d-p-r-380-2001.json`), the wizard's
"Le opere ricadono nell'ambito della Sanatoria ?" answered Sì, which adds the quadro "SANATORIA",
and `dictionary/fnsuap.yaml`.

## What it covers (2026-10-30)

The SUE rules table (`rules/sue-napoli.yaml`) gives this pratica (`napoli/comune/permesso-in-
sanatoria`) for works already done that needed the permesso (a new construction or an extension
like a veranda, a heavy ristrutturazione, a variant to a permesso), without structures, change of
use, landscape protection, bene culturale or a Zona A demolition. Arts. 36 and 36-bis DPR 380/2001
checked on Normattiva. Works on structures since 2026-11-01: the asseverazione's sismica quadro
says the works need the autorizzazione sismica, which in Campania works begun without the seismic
filing always do (art. 4 c. 1 e L.R. 9/1983), its documents attached, and the table adds the
autorizzazione at the Genio Civile, filed apart; a deposito is refused at pre-flight. Art. 36 has
no seismic box of its own (art. 36-bis c. 3-bis is for art. 36-bis, refused for its defect).
`answers-strutture.json`: the roof-terrace room on a timber frame.

- **Assenza** (art. 36): without the permesso or in total difformity, conforming to the rules
  then and now; the date, and the acknowledgment that the release is subordinate to an oblazione
  twice the contributo di costruzione.
- **Parziale** (art. 36-bis): refused at pre-flight, a portal defect (below). The quadro's rows
  (the date, which conformity) are mapped, the asseverazione's aren't.
- Quadro a): art. 36's own radio ("intervento realizzato, ai sensi dell'articolo 36, comma 1"),
  not art. 10's (ticked until 2026-10-31).
- The asseverazione: the request "presentata in sanatoria", the stato legittimo also from this
  sanatoria, the case, the date, its documents, the catasto.
- The contributo: worked out by the SUE or by the prospetto, paid when the permesso is collected
  (the release is subordinate to the oblazione: instalments or "during the works" are refused).

The permesso's own asseverazione rows don't show in the crawl (it matched the section to the
SCIA's, whose sanatoria rows are hidden by default): they go by label on the page (`on_page`).

The portal's permesso form requires one energy incentive claimed (art. 14 c. 6 or 7 D.Lgs.
102/2014, or the 5% bonus of D.Lgs. 28/2011) even with no energy works (seen 2026-10-30): a case
with none, like a plain veranda, is refused at pre-flight, the plain permesso's too. With the
energy filing the report goes with the request (the works are done), in its own slot.

A portal defect, in the library's discrepancies: under art. 36-bis the asseverazione's documents
attached, its dating (by documents or by attestation) and its works proposal are one radio group
(ticking one unticks the others, seen 2026-10-30), as in the SCIA's case 4.4, and so are the
quadro's two acknowledgments (the oblazione, and the works the SUE may require, c. 2). The case
can't be stated in full, so pre-flight refuses it; `answers-parziale.json` is kept as that check.

Left to the person: the Elaborati richiesti per la sanatoria (signed .p7m only), the portal's
documents, the declarations, signing and sending, then the oblazione the SUE determines.

## Cases from the schema table (2026-10-30)

Written from `docs/schema-branches.md`, one answers file per group of options of the national
form no case took. Each passes pre-flight offline; **none has been run on the portal yet**.

- `answers-catasto-invariato.json`: the works to legalize need no change to the catasto.
- `answers-catasto-presentata.json`: the DOCFA already filed (its protocol and date).

## Runs

| Date | Browser | Answers | Result |
|---|---|---|---|
| 2026-10-30 | pane | `answers-p6.json` (art. 36) | **Filled** from a blank draft in 211.8 s, read back on a fresh load (23.8 s), 7 files kept (the energy report included), nothing moved or loose |
| 2026-10-30 | pane | `answers-parziale.json` (art. 36-bis) | Stopped on "Asseverazione PdC - stato legittimo": 7 required rows unmapped. Ticking them by hand showed the four (documents, the two datings, the works proposal) are one radio group: now refused at pre-flight |
| 2026-10-30 | pane | `answers-p6.json` after gen.py's offset fix (the new-construction lines get ids, `r14c2p21reg:chk` for this case's), `bench/rerun.py` bundle | **Filled** in 156.2 s, read back on a fresh load (27.4 s), nothing moved or loose: the id is the box's |
| 2026-10-30 | pane | systems needing a project (`answers-impianti`: six systems, each project in its own slot), `bench/rerun.py` bundle | **filled** in 170 s, read back on a fresh load (25 s), nothing moved or loose |
| 2026-10-31 | pane | `answers-p6.json` with quadro a)'s art. 36 radio, `bench/rerun.py` bundle | **filled** in 149 s, read back on a fresh load (24 s), nothing moved or loose |
| 2026-11-01 | pane | `answers-strutture`: the room on a timber frame, the sismica quadro's autorizzazione, `bench/rerun.py` bundle | **filled** from a blank draft in 144 s, read back on a fresh load, nothing moved or loose |
| 2026-11-02 | pane | `answers-tutela`: the underground room, in a protected area but with nothing above ground (DPR 31/2017 Allegato A.15), the landscape quadro's "non comportano alterazione", `bench/rerun.py` bundle | **filled** from a blank draft in 145 s, read back on a fresh load, nothing moved or loose |
| 2026-11-02 | pane | `answers-cambio-intero`: a whole building changed from offices to homes in 2021 without the SCIA alternativa (L.R. 13/2022), with maintenance works, as an art. 36 sanatoria ("altro" in the asseverazione), `bench/rerun.py` bundle | Stopped on "a) Qualificazione pratica dell'intervento": the art. 36 line was ticked only for art. 10 works. Now ticked for every permesso in sanatoria |
| 2026-11-02 | pane | `answers-cambio-intero`, the same, rerun with the fix, `bench/rerun.py` bundle | **filled** from a blank draft in 172 s, read back on a fresh load, nothing moved or loose |
| 2026-11-02 | pane | `answers-zona-a`: a storage building in a zona A courtyard demolished and rebuilt in 2018 with the same shape and volume, no title (DGC 454/2014: no SCIA in zona A), "altro" in the asseverazione, the autorizzazione sismica apart, `bench/rerun.py` bundle | Stopped on the sanatoria quadro's "allega la documentazione necessaria indicata nel quadro riepilogativo": covered by the calendar the date above it left open (`div#ui-datepicker-div`). The runner now closes it before each box and Salva (inpage.js `closeLists`) |
| 2026-11-02 | pane | `answers-zona-a`, the same, with the runner fixed, `bench/rerun.py` bundle | **filled** from a blank draft in 154 s, read back on a fresh load, nothing moved or loose |
