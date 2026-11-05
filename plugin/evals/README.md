# Evals of the portali-pratica skill

How Claude follows the skill, on made-up data, with no browser and no portal: whether it sends
pre-flight's message as written, refuses a case it can't prepare before opening anything, never
uses a credential, answers from the library, and puts documents attached to the conversation in
the job's folder unopened. `claude plugin eval` runs them against a built plugin; a release ships
none of this.

```sh
PRATICHE_NAPOLI_DIR=../pratiche-napoli ~/.cache/pratica-portal/venv/bin/python plugin/build.py --evals
claude plugin eval plugin/dist/portali --scaffold --allow-tools Bash Write
```

`--evals` copies this folder into the build as `evals/`, with the made-up CILA job
(`_job/`: the CILA rehearsal's P6 fixture, split as a tecnico's folder holds it) that
`pre-flight-message` and `no-credentials` start from. Each case runs 3 times; graders that only say
whether the skill fired (`tool_used: Skill`) don't count toward the score.
