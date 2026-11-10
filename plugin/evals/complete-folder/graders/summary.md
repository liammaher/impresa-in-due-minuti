---
type: llm
---
A complete real job (not a test): the client's documents in their real formats, every file a signed
PDF/A, and the tecnico's own note with what no document holds (contacts, the owner's legale
rappresentante, the two firms, no other filings, no other technicians). The documents are made-up
specimens (the identity card is a blank scan). A short list of points to check before the «sì»
(a document that can't be read, or one that disagrees with an answer, a line each) is allowed.
Two closing lines are expected and are not requests for files the folder holds: that the tecnico
picks the job's files once at the start of the compilation (the portal's page can't receive them
otherwise), and that after the declarations they give the signed files the portal makes only then
(the procura), for a second compilation.
The reply carries, between what it understood and the summary, the card «Cosa succede»: three lines, a heading
that names the pratica (and why it is this one), «Io compilo … quadri, allego … file e rileggo tutto dal portale»
and «Tu controlli l'anteprima, spunti le dichiarazioni, paghi, firmi e invii». It is generated, it is not a list of
every answer and it is not a request. A reply without it fails.
PASS if the final reply is in Italian, addresses the tecnico as tu (never Lei), opens with whether the pratica
is covered by the automation, says in a few sentences what it understood (naming the documents
and the tecnico's note it comes from) and that it proposes a CILA, then a short summary: under
«Da controllare» each answer Impresa in un minuto proposes itself, a line each; the rest counted by where it
comes from, with «dettagli» to see every answer; what is left to the tecnico at the end
(declarations, signature, payment, sending); and one «sì» before opening the portal.
FAIL if it asks a question with options to pick, asks for documents, details or files that the
folder or the note holds, lists every answer one per line instead of the short summary, shows
technical words (pre-flight, JSON, script, answers.json, riepilogo_id) or file names like
values.json, or says the pratica was filled or sent.
