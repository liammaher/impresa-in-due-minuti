# Evals of the pratiche skill

How Claude follows the skill, on made-up data, with no browser and no portal: whether it sends
pre-flight's message as written, refuses a case it can't prepare before opening anything, says a
property outside the Comune di Napoli isn't covered, never
uses a credential, answers from the library, and puts documents attached to the conversation in
the job's folder and reads them, naming the document each fact comes from. And, when Impresa in un minuto itself fails, whether it
writes the problem report with none of the job's data in it and leaves sending it to the tecnico. `claude plugin eval` runs them against a built plugin; a release ships
none of this.

```sh
PRATICHE_NAPOLI_DIR=../pratiche-napoli ~/.cache/pratica-portal/venv/bin/python plugin/build.py --evals
claude plugin eval plugin/dist/impresa-in-un-minuto --scaffold --allow-tools Bash Write
```

`--evals` copies this folder into the build as `evals/`, with the made-up CILA job
(`_job/`: the CILA rehearsal's P6 fixture, split as a tecnico's folder holds it) that
`pre-flight-message`, `no-credentials`, `bug-report` and `test-own-case` start from (`complete-folder` instead starts from the same case complete as a tecnico hands it over: the
made-up dossier in its real formats, `_dossier/`, its files signed PDF/A, and the tecnico's
`note.txt`; it must take one message with every answer, for a single «sì»; the «sì» itself,
`confirm`, is bench/test_one_yes.py's: a one-turn case can't hold the summary the tecnico read); `prova`,
`first-contact` and the three tests asked as a tecnico asked them on 2026-11-06 (`test-in-a-job`: a CILA
called a test in its first line; `test-mid-job`: a test after the folder and the questions were asked;
`test-other-pratica`: a SCIA as a test) start from an empty folder, as a tecnico who has just installed the plugin.
A test asks nothing: every `prova`-tagged case fails on a question. Each case runs 3 times; graders that only say
whether the skill fired (`tool_used: Skill`) don't count toward the score.
