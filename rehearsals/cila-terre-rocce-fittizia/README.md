# CILA with the dichiarazione di utilizzo delle terre e rocce da scavo, one pratica

The CILA and the dichiarazione di utilizzo (art. 21 DPR 120/2017) selected together in the wizard on
Napoli's SUE. The case: rehearsals/cila-fittizia's, with non-structural works and a new sewer connection in the courtyard, 30 m³ dug; works not begun (the P6 CILA is a late one: here "da iniziare", start 11/01/2027); the soil leaves the site as a by-product
(a small site). Made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations,
payment, signing and sending.

- **Two operations** (`catalogue/F839/sections/sue-combo-cila-dichiarazione-utilizzo.json`, crawled 2026-11-03 with its
  attachments screen, 23 sections): the CILA's own sections, every one already in the dictionary. The
  dichiarazione adds two adempimenti (the SUE's, ARPA Campania's) and no section of its own; the
  location and land register sections are the dichiarazione's lower-case ones, not the title's
  (catalogue/F839/sue-wizard.json `pairs`).
- **The recipe** `extends` cila-fittizia's and `parts/dichiarazione-utilizzo-terre.yaml`, restating its
  `yours` (a recipe's `yours` replaces the one it extends).
- **The attachments screen** adds one slot, "Dichiarazione di utilizzo di cui all'art. 21 …": the
  portal's own document, required, signed only, attached in the second run. Read on the filled
  draft 2026-11-03 (`slotsOf`): besides it, the CILA's own slots under the case's answers: the third parties' assent, the co-holders' IDs, the notifica preliminare (the CILA case's answers).
- The rules table sends here a CILA case whose excavated soil leaves the site as a by-product from a
  site up to 6,000 m³ (or larger with no VIA/AIA), with no landscape authorization; the DAU (art. 7)
  is the person's, apart, once the soil is used.

## Runs

| Date | Browser | Result |
|---|---|---|
| 2026-11-03 | pane | P6, from scratch, `bench/rerun.py` bundle: **filled** in 114 s, every value read back on a fresh load; the portal's usual warnings on made-up data (the PEC, the address, the land register) |
