# subingresso-negozio: filed by a tecnico with a procura (SUAP Napoli)

`rehearsals/subingresso-negozio-fittizio` filed by a tecnico for a made-up client company with a procura speciale: see
`rehearsals/ristorante-procura-fittizio` (gen.py `as_client`, route.py `via`). Values: `fixture.json`
(the client has no REA: a registered company is checked against the real register). Never declared,
paid, signed or sent. The procura attached in the second run is not proven (it needs a real firma
digitale).

Its attachments slots weren't read on its own draft: they are the parent's crawl slots with the procura's
two in front, and the run attached the grantor's identity document in them (2026-11-11).

Run it in a batch of its own. Twice it stopped on an error from another pratica's section ("TypeError:
(s || \"\").normalize is not a function" at «dati dell'impresa a cui si subentra»), once in a batch after
the subingresso ristorante's variant and once in a batch with its parent, whose run then stopped on the
procuratore section only the variant has: two runs of one procedure in one batch mixed their steps. Alone
it filled.

## Runs

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-11 | pane | `answers.json` | **filled** in 88 s |

<!-- /runs -->
