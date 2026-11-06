# SCIA in sanatoria e proroga paesaggistica, one pratica

`scia` (the sanatoria question answered Sì) + `proroga-paesaggistica` selected together in the wizard on Napoli's SUE. A SCIA filed of one's own accord for works still under way (art. 37 c. 5 DPR 380/2001, the €516 sanction) on a protected property whose landscape authorization, held for the facade works not yet done, is about to expire: the SCIA carries its art. 10-septies extension, as a new title would (`catalogue/F839/sue-pairs.yaml`, `authorization-keeps-pace`; the rules table's `paesaggistica-proroga` and its reading for an architect).

- **Why only works under way**: works all done that needed the landscape authorization take their compatibility inside the art. 36-bis sanatoria (c. 4); this recipe inherits the refusal of `doppia conformita` from `scia-sanatoria-paesaggistica-semplificata-fittizia`.
- **The crawl**: `catalogue/F839/sections/sue-combo-scia-sanatoria-proroga-paesaggistica.json`, crawled 2026-11-05 with the sanatoria answered Sì (`catalogue.py ops sue --combo ... --combo-scelta`): 41 sections, none new. The pratica has no bollo section (as the SCIA with the proroga).
- **The recipe** `extends` `scia-sanatoria-paesaggistica-semplificata-fittizia`, `proroga-paesaggistica-fittizia`: the first is the main pratica, the other's answers fill what its don't say (the authorization's protocol and expiry, the extension's period). It restates the main pratica's `diritti_euro` and rules facts, which the proroga's would replace.
- The rules table sue-napoli routes this combination: 28 cases (2026-11-05).

Made-up data; the draft is "PROVA NON INVIARE" and stops before the declarations, payment, signing and sending.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-05 | pane | `answers-p6.json` | P6, from scratch, `bench/rerun.py` bundle: **filled** in 234 s, every value read back on a fresh load; the portal's usual warnings on made-up data (PEC, address, catasto) |

<!-- /runs -->

