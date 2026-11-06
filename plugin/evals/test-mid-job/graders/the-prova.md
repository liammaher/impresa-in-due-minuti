---
type: llm
---
The tecnico's third message on 2026-11-06, after being asked for a folder and then shown the
questions that pick the pratica.
PASS if the reply is in Italian, addresses the tecnico as Lei (formal forms such as «mi scriva», «la cancelli» are enough), drops those questions and runs the made-up CILA (the draft
«PROVA NON INVIARE - CILA di prova», with invented client, studio and documents), asks them to log
in with SPID in the app's browser (or says it can't open the browser here) and tells them to
delete the draft from «Pratiche in bozza» afterwards.
FAIL if it asks any of those questions again, or any other about the case, asks for a folder,
documents, test data or the studio's details, asks them to confirm before starting, or says it
doesn't invent data.
This session has no browser: telling them to write «fammi vedere una prova» from the Claude app, where the browser is, is the expected reply, not a question or a request to confirm.
