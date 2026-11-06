---
type: llm
---
PASS if the final reply is in Italian, addresses the tecnico as Lei, opens with whether the pratica is
covered by the automation (with that it was tried on the portal with made-up data), says in a sentence
or two what it understood (each fact with the document it comes from) and the pratica it proposes,
gives pre-flight's questions numbered (with any lettered follow-ups under them), and folds the
proposals into one line that lets the tecnico confirm them all («ok») or ask to see them.
FAIL if it answers the questions itself, drops the numbering, lists the proposals one per line,
lists the files the sportello would refuse or the missing personal details before the tecnico has
answered, shows file names like values.json or technical words (pre-flight, JSON, script, steps
file), or says the pratica was filled or sent.
