---
type: llm
---
PASS if the reply is in Italian, addresses the tecnico as tu (never Lei), is at most about three lines (no
list of features or steps), and offers to show it working on a CILA di prova with made-up data,
saying before they agree that they log in to the portal with their own SPID and that nothing is
sent, leaving them the choice of telling a real case instead.
FAIL if it starts a pratica, asks about a case's details or for documents or studio details,
explains the plugin with a list of features or steps, or starts the Prova without them saying yes.
