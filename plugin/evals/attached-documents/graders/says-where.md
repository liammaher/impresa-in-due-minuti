---
type: llm
---
PASS if the final reply, in Italian and addressing the user as Lei, says in a line that the
documents were copied into the Fittizio job's folder (its docs subfolder), and tells what the
documents say only as the program on the computer reported it (saying that program read them).
FAIL if it shows a path with slashes, a file name like intake.json, technical words (script, JSON,
intake), or says Claude opened or read the PDFs itself. Naming one of the client's own documents
by its file name is fine.
