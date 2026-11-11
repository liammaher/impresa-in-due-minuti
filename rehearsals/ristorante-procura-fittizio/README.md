# Bar o ristorante: la SCIA presentata da un tecnico con procura (SUAP Napoli)

The opening of a bar or restaurant (`rehearsals/ristorante-fittizio`) filed by a tecnico for a client
company, with a procura speciale. Made up: Trattoria Fittizia S.r.l. (`trattoria:`, its legale
rappresentante Luca Fittizio `luca:` is `cr:`), the studio's titolare Chiara (`t:`, the portal's
procuratore); `fixture.json`, `answers.json`. Never declared, paid, signed or sent.

How it differs from the titolare's file (gen.py `as_client`, route.py `via`):

- The wizard's "Scelte eventuali" ticks «il presentatore della domanda è un professionista / altro
  soggetto munito di procura speciale»: the portal adds "Qualifica e dati del procuratore" (the tecnico).
- The Scheda anagrafica, the premises and the other sections read the client (`c:business.*`,
  `c:locale.*`) and its declarant (`cr:`); the carica comes from `ask.cliente_carica`.
- The case says it apart from the rules table's facts: `"via": "procura"` in route.py's answers.

On the portal (2026-11-11, pane):

- The attachments screen of this draft has the procura's own slots (`slots:` in the recipe): "Procura
  speciale" (portal-made after the declarations, signed only: `jpg.p7m;pdf.p7m`) and "Fotocopia di un
  documento di identita' del soggetto che conferisce la procura speciale" (a plain PDF, required, so the
  first run attaches it). No "Quadro riepilogativo" slot (the SUE's DSC) on the SUAP.
- A client company in the Registro delle imprese (a REA number) stops on the first section: the portal
  looks its codice fiscale up in the real register, which a made-up company can't pass. The rehearsal's
  client has no REA ("non ancora iscritta").
- Not proven: the procura attached in the second run (`--after-declarations`) needs a real firma
  digitale: the portal checks the .p7m at upload.

Warnings the run read: the made-up PEC, street and catasto only.

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-11 | pane | `answers.json` | **filled** in 82 s |

<!-- /runs -->
