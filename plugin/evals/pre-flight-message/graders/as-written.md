---
type: llm
---
PASS if the final reply is in Italian, addresses the tecnico as Lei, opens with whether the pratica is
covered by the automation (with that it was tried on the portal with made-up data), and gives pre-flight's
questions numbered (with any lettered follow-ups under them) and its proposals as "Risposte che propongo" lines,
asking the tecnico to answer by number and to confirm the proposals with «ok».
FAIL if it answers the questions itself, drops the numbering, shows file names like values.json or
technical words (pre-flight, JSON, script, steps file), or says the pratica was filled or sent.
