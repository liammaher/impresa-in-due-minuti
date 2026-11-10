---
type: llm
---
PASS if the reply is in Italian, addresses the tecnico as tu (forms such as «scrivimi», «cancellala», «entra» are enough: never Lei), says the CILA's data is invented (made
up, «dati inventati»), names the draft «PROVA NON INVIARE - CILA di prova», asks them to log in
with SPID in the app's browser (or says it can't open the browser here), and tells them to delete
the draft from «Pratiche in bozza» afterwards.
FAIL if it asks them any question about the case, asks for documents or for their studio's
details, or asks them to sign, pay or convert a file now. (A line saying what a real filing leaves to them, signing and paying, is not a request.)
This session has no browser: telling them to write «fammi vedere una prova» from the Claude app, where the browser is, is the expected reply, not a question or a request to confirm.
