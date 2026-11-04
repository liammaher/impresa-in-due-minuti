#!/usr/bin/env python3
"""The rehearsals' one run record: rehearsals/<name>/runs.json, an entry per run on the portal.

    runs.py            list the READMEs whose run table isn't their runs.json's
    runs.py --write    draw every README's run table from its runs.json

An entry has its `date` and what was recorded of the run: `answers` (the case's file), `result`
(filled, stopped) and `seconds`, which `bench/rerun.py --record` writes, and `browser`, `case` and
`note`, the words a person wrote for it (the runs before 2026-10-31 have only these). Each README's
"## Runs" table is drawn from it between the two markers, by `rerun.py --record` and by
`--write`; test_gen holds every table to its runs.json. Prose around the table is the README's.
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REHEARSALS = HERE.parents[3] / "rehearsals"
START = "<!-- Runs: drawn from runs.json by claude/skills/pratica/portal/runs.py; edit runs.json, not this table. -->"
END = "<!-- /runs -->"
# A run that filled the draft: read back on a fresh load, or taken to the end of the form. A note
# counts as the README's row did for the scoreboard (a run that only stopped doesn't).
FILLED = re.compile(r"(filled|read back|to the end of the form)", re.I)


def load(d):
    f = Path(d) / "runs.json"
    return json.loads(f.read_text()) if f.is_file() else []


def filled(runs):
    """Whether one of these runs filled its draft."""
    return any(r.get("result") == "filled" or FILLED.search(r.get("note", "")) for r in runs)


def _result(r):
    if r.get("note"):
        return r["note"]
    s = f"**{r['result']}**" if r.get("result") else ""
    return s + (f" in {round(r['seconds'])} s" if r.get("seconds") else "")


def table(runs):
    """The README's block: the markers around one row per run, in runs.json's order."""
    rows = []
    for r in runs:
        case = r.get("case") or (f"`{r['answers']}`" if r.get("answers") else "")
        cells = [r["date"], r.get("browser", ""), case, _result(r)]
        for c in cells:
            if "|" in c or "\n" in c:
                raise ValueError(f"a run's cell can't hold a | or a line break: {c!r}")
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([START, "", "| Date | Browser | Case | Result |", "|---|---|---|---|", *rows, "", END])


def drawn(text, runs):
    """The README's text with its run table drawn from runs (a new "## Runs" at the end where it
    has none), or the text as it is when it has no table and no run."""
    if START in text:
        head, rest = text.split(START, 1)
        if END not in rest:
            raise ValueError(f"{START} without {END}")
        return head + table(runs) + rest.split(END, 1)[1]
    if not runs:
        return text
    m = re.search(r"^## Runs\n\n?", text, re.M)
    if m:
        return text[:m.end()] + table(runs) + "\n\n" + text[m.end():]
    return text.rstrip("\n") + "\n\n## Runs\n\n" + table(runs) + "\n"


def stale(root=REHEARSALS):
    """The rehearsals whose README's run table differs from their runs.json."""
    out = []
    for d in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        readme = d / "README.md"
        if readme.is_file():
            text = readme.read_text()
            if drawn(text, load(d)) != text:
                out.append(d.name)
    return out


def write(d):
    """Draw one rehearsal's README run table again (no README: nothing)."""
    readme = Path(d) / "README.md"
    if readme.is_file():
        text = readme.read_text()
        new = drawn(text, load(d))
        if new != text:
            readme.write_text(new)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    if a.write:
        for d in sorted(p for p in REHEARSALS.iterdir() if p.is_dir()):
            write(d)
    names = stale()
    print("\n".join(names) if names else "every README's run table is its runs.json's")
    raise SystemExit(1 if names else 0)


if __name__ == "__main__":
    main()
