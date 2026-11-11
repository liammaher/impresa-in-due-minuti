# The Impresa in un minuto plugin

What a tecnico in Naples installs in the Claude desktop app, or in Cowork (`impresa-in-un-minuto/README.md` is
what they read): the portal runner, the rehearsals' steps files and the library (`library/`),
with no server (`docs/design/packaging.md`; the archive only as `build.yaml` says). `impresa-in-un-minuto/` is
what's written by hand; `build.py` adds the rest.

```sh
~/.cache/pratica-portal/venv/bin/python plugin/build.py
```

writes `plugin/dist/impresa-in-un-minuto/` and `plugin/dist/impresa-in-un-minuto.plugin` (install it in Cowork
from a file). The build:

- copies `run.py`, `rules.py` (with `drift.json`, for its drift refusal), `inpage.js`,
  `fill.py`, `review.py` and `schema.json` into the skill unchanged (no authoring code:
  `catalogue.py` stays in the repo);
- writes each rehearsal's steps file (the generated one first, as `bench/rerun.py` picks it)
  and the rules tables as JSON, which `rules.load` reads without PyYAML: Cowork runs
  the plugin with no packages;
- lists them in `catalog.json`, one pratica a line (Claude searches it), with their library
  procedure and notes (the cases each refuses stay in its steps file, where pre-flight reads them);
- copies the library's procedures, rules, offices, situations and `signing.json`;
- makes the test skill's case from the CILA rehearsal's P6 fixture (studio and job split as
  an architect's folder holds them) and a 3 MB test PDF;
- stops unless the test case passes `check.py` and pre-flight under the system `python3`,
  and every pratica's pre-flight prints the same from the plugin as from the repo's runner;
- stops if any file holds a term from the maintainer's private list (`IMPRESA_IN_UN_MINUTO_PRIVATE_TERMS`,
  default `~/.config/impresa-in-un-minuto/private-terms.txt`, else the old `~/.config/impresa-in-due-minuti/`, `~/.config/portali/` or `~/.config/portale-sue/` one, one per line; outside the repo, since it is the
  data): their codice fiscale, address, CIE and the like. It names the file and the list's
  line, never the term.

**The sportelli.** `build.yaml`'s `sportelli` (`[sue]`) says whose pratiche the plugin carries: the
rehearsals of that sportello (a combination's from its main pratica), its rules tables
(`rules/<sportello>-*.yaml`) and the library procedures those pratiche and tables name, so its guides
are the SUE's too. The SUAP's rehearsals and table stay in the repo, out of the plugin.

**The archive switch.** `build.yaml`'s `vault` says whether the plugin ships Impresa in un minuto's archive
(pvault). Off (as now), the plugin has no `setup` skill and no installer, the skill and
README keep only their `<!-- no-vault -->` parts (a job's details live in files in the tecnico's
folder of jobs, still sealed under the on-screen code on their way to the portal), and a release
builds no pvault at all (`release.yml`). On, everything comes back as it was: flip it and
rebuild. `--vault on|off` overrides it for one build; `test_build.py` checks both.

One skill, `pratiche` (the job). `--cowork-test` keeps a second, `cowork-test` (the
tests that decide the design: script calls in Cowork's browser, a 3 MB attachment, a run's cost;
it writes `impresa-in-un-minuto-test-results.md` to bring back), for whoever runs them: a release leaves it out.
`--evals` adds `evals/`, how Claude follows the skill on made-up data, for `claude plugin eval`
(`evals/README.md`): a release leaves them out too.

**Trying it as a tecnico does.** `plugin/live.py` builds the plugin when `plugin/dist` is stale (`dist/build.json`
holds a digest of its sources) and says what to load; a test of how the plugin behaves (the Prova, a demo, a wording
change) runs through that build, in the app's browser pane, never through the repo's scripts. The build refuses a copy
of a runner file that differs from the repo's, and a Prova card (`run.py card`, "Cosa succede": two lines, the pratica and why, what
Claude does) that differs from the repo runner's. The Prova itself sends the tecnico three lines before the login, one
while it fills and three at the end (review.py: one line when everything matched, what a real filing leaves to them,
the draft to look at); the card goes with a real job's summary, and a hand-over with a second compilation says who acts
when (they, Claude, they).

Rebuild after a change to the runner, a steps file, the dictionary or the library, and bump
`version` in `impresa-in-un-minuto/.claude-plugin/plugin.json`. The generated steps files are built here from
their recipes (they are never committed), and the build stops unless each is the one
`rehearsals/steps.lock` names.
