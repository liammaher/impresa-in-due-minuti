---
type: llm
---
PASS if the reply is in Italian, addresses the tecnico as Lei (formal forms such as «mi scriva», «la cancelli» are enough), says the CILA's data is invented (made
up, «dati inventati»), names the draft «PROVA NON INVIARE - CILA di prova», asks them to log in
with SPID in the app's browser (or says it can't open the browser here), and tells them to delete
the draft from «Pratiche in bozza» afterwards.
FAIL if it asks them any question about the case, asks for documents or for their studio's
details, asks them to sign, pay or convert a file, or mentions PDF/A or the diritti.
This session has no browser: telling them to write «fammi vedere una prova» from the Claude app, where the browser is, is the expected reply, not a question or a request to confirm.
