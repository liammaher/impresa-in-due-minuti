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
checked on Normattiva.

- **Assenza** (art. 36): without the permesso or in total difformity, conforming to the rules
  then and now; the date, and the acknowledgment that the release is subordinate to an oblazione
  twice the contributo di costruzione.
- **Parziale** (art. 36-bis): refused at pre-flight, a portal defect (below). The quadro's rows
  (the date, which conformity) are mapped, the asseverazione's aren't.
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

## Runs

| Date | Browser | Answers | Result |
|---|---|---|---|
| 2026-10-30 | pane | `answers-p6.json` (art. 36) | **Filled** from a blank draft in 211.8 s, read back on a fresh load (23.8 s), 7 files kept (the energy report included), nothing moved or loose |
| 2026-10-30 | pane | `answers-parziale.json` (art. 36-bis) | Stopped on "Asseverazione PdC - stato legittimo": 7 required rows unmapped. Ticking them by hand showed the four (documents, the two datings, the works proposal) are one radio group: now refused at pre-flight |
