# subingresso-negozio: filed by a tecnico with a procura (SUAP Napoli)

`rehearsals/subingresso-negozio-fittizio` filed by a tecnico for a made-up client company with a procura speciale: see
`rehearsals/ristorante-procura-fittizio` (gen.py `as_client`, route.py `via`). Values: `fixture.json`
(the client has no REA: a registered company is checked against the real register). Never declared,
paid, signed or sent. The procura attached in the second run is not proven (it needs a real firma
digitale).

Its attachments slots weren't read on its own draft: they are the parent's crawl slots with the procura's
two in front, and the run attached the grantor's identity document in them (2026-11-11).

Twice it stopped on another rehearsal's sections (`TypeError: (s || "").normalize is not a function`) in a batch
with another run of its procedure: the pane then kept one steps file per procedure (now keyed by a hash of
what it fills). The run below is its own, alone.

<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->

| Date | Browser | Case | Result |
|---|---|---|---|
| 2026-11-11 | pane | `answers.json` | **filled** in 88 s |

<!-- /runs -->
