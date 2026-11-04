# Fine lavori e DAU, one pratica

`fine-lavori` + `dau` selected together in the wizard on Napoli's SUE. Why a case files them together (`catalogue/F839/sue-pairs.yaml`, `dau-at-the-end`, reading): The DAU is due when the soil's use is over (art. 7 DPR 120/2017), and the end of works (art. 23 c. 7 DPR 380/2001) or the agibilità (art. 24) is the filing at that moment: one pratica carries both. The law doesn't require them together.

- **The crawl**: `catalogue/F839/sections/sue-combo-fine-lavori-dau.json`.
- **The recipe** `extends` `fine-lavori-fittizia`, `dau-fittizia`: the first is the main pratica, the others' answers fill what its don't say.
- No rules table routes this combination yet: the person names it.

Made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations, payment, signing and sending.

## Runs

| Date | Browser | Result |
|---|---|---|
| 2026-11-04 | pane | P6, from scratch, `bench/rerun.py` bundle: **filled** in 170 s, every value read back on a fresh load; the portal's usual warnings on made-up data |
