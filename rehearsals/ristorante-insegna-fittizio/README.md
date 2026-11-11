# A restaurant's opening with an outside sign, generated from the batch crawl

"Aprire l'attività" for a bar or restaurant outside the protected zones on Napoli's SUAP, with
the wizard's "in caso di attività che preveda insegna esterna" tick: the SCIA, the Reg. 852/2004
notifica and the sign's SCIA (mezzi pubblicitari) in one pratica, for the pizzeria rehearsal's
made-up ditta individuale (`rehearsals/pizzeria-fittizia/fixture.json`), with a 3 × 0.6 m unlit
sign over the door. The draft is "PROVA NON INVIARE - ristorante insegna generato" and stops
before the declarations, payment, signing and sending.

- **Crawl**: `catalogue/F839/sections/suap-060-aprire-l-attivita.json`, the sign's sections from
  `suap-060-aprire-l-attivita-interventi.json` (the same in every sector, already mapped for the
  shop: `rehearsals/negozio-insegna-fittizio`).
- **The rules table**: an outside sign at an opening adds `napoli/comune/insegna-esercizio`
  (`insegna`), which this recipe handles; the opening without a sign stays
  `rehearsals/ristorante-fittizio`, whose steps file is unchanged.
- **Questions**: the shop's sign refusals (the owner's consent, a protected building, over 5 m²),
  and the opening's (alcohol, music). The fees are proposed, for the person to confirm: €120 (S72)
  plus €100 (S204), summed as the Comune's guide says for a joined pratica.
- **Not read yet**: the attachments screen with the sign's slots.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-10 |  | `answers.json` | **filled** in 97 s |

<!-- /runs -->

