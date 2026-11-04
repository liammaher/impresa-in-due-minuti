# SCIA in sanatoria with its autorizzazione paesaggistica semplificata, one pratica

A SCIA filed of one's own accord for works still under way (art. 37 c. 5 DPR 380/2001, the €516
sanction) on a building under art. 136 and 142, with the landscape authorization for the works not
yet done: the SCIA and the semplificata selected together in the wizard, the sanatoria question
answered Sì. The case: interior works begun without the SCIA (partitions, a new bathroom, the
systems), the shutters and railings of a new design still to fit (Allegato B, B.3). Made-up data (rehearsals/scia-sanatoria-fittizia's
people and property); the draft is "PROVA NON INVIARE" and stops before the declarations,
payment, signing and sending.

- **Why only works under way**: the landscape authorization can't be given for works already
  done, even in part (art. 146 c. 4 D.Lgs. 42/2004). Works already done that needed it go through
  the art. 36-bis sanatoria alone, whose asseverazione asks for the binding parere (c. 4:
  rehearsals/scia-sanatoria-fittizia, answers-paesaggio.json); this recipe refuses a
  `doppia conformita` case with that reason. The asseverazione's tutela quadro offers the three as
  one choice (semplificato, ordinario, accertamento art. 36-bis): `sanatoria_paesaggio` false picks
  the semplificata.
- **Two operations**, their sections in the order of the combination's crawl with the sanatoria
  answered Sì (`catalogue/F839/sections/sue-combo-scia-sanatoria-paesaggistica-semplificata.json`, crawled
  2026-10-31): the earlier SCIA crawls with the landscape authorization tried only the procura.
- **The recipe** `extends` the SCIA in sanatoria's and `parts/paesaggistica-semplificata.yaml`.

## Runs

| Date | Browser | Result |
|---|---|---|
| 2026-10-31 | pane | P6, from scratch, `bench/rerun.py` bundle: **filled** in 155 s |
| 2026-11-01 | pane | P6, `bench/rerun.py` bundle, after the semplificata's "Si allega" box got its slot ("Relazione paesaggistica semplificata e documentazione necessaria": required, plain PDF; read on the earlier filled draft, whose run had left it empty: the runner took the portal's "required" under it for the person's signed-only "Relazione Paesaggistica Semplificata", whose title starts it; fixed in inpage.js): **filled** in 158.8 s, the slot holding its file. |
