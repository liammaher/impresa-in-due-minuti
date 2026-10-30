#!/usr/bin/env python3
"""The portal map's scoreboard, counted from the catalogue and the rehearsals.

    scoreboard.py            print docs/coverage.md's tables
    scoreboard.py --write    rewrite docs/coverage.md

Three levels, each a stricter claim than the last (docs/coverage.md says them in words):

  mapped    a stored crawl of the pratica (catalogue/F839/sections/)
  fillable  mapped, and the dictionary fills every section of it (gen.py's own test)
  run       fillable, and a rehearsal recipe generated from it has a README with a dated run

Run it with the pratica venv's Python (it imports gen.py, which needs PyYAML).
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

import catalogue as cat
import gen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REHEARSALS = ROOT / "rehearsals"
OUT = ROOT / "docs" / "coverage.md"


def pratica_status(stored, alias, dictionary):
    """Per stored crawl: its sportello and whether every section is filled."""
    cache = dict(stored)
    rows = {}
    for name, c in list(stored.items()) + [(n, stored[l]) for n, l in alias.items() if l in stored]:
        missing = []
        for s in c["sections"]:
            if s.get("skipped") or s.get("error") or s.get("scelta"):
                continue
            sec = cat.resolve(s["same_as"], cache) if s.get("same_as") else s
            if not cat.covered({**sec, "section": s["section"]}, dictionary):
                missing.append(s["section"])
        rows[name] = {"sportello": cat.sportello(name), "missing": missing, "alias": name not in stored}
    return rows


def rehearsal_status():
    """Each recipe: the crawl it was generated from, and whether its README records a run."""
    out = {}
    for d in sorted(p for p in REHEARSALS.iterdir() if p.is_dir()):
        recipe = d / "recipe.yaml"
        if not recipe.exists():
            continue
        r = gen.load_yaml(recipe)
        readme = d / "README.md"
        text = readme.read_text() if readme.exists() else ""
        # A run is a dated row of the README's table that says the draft was filled: read back
        # on a fresh load, or taken to the end of the form (a row that only stopped doesn't count).
        run = bool(re.search(r"^\|\s*20\d\d-\d\d-\d\d\s*\|.*(filled|read back|to the end of the form)",
                             text, re.M | re.I))
        out[d.name] = {"crawl": r.get("crawl"), "sportello": r.get("sportello"), "run": run, "readme": readme.exists()}
    return out


def build():
    stored = cat.crawls()
    alias = cat.json.loads(cat.SAME.read_text())["same"] if cat.SAME.exists() else {}
    dictionary = gen.load_yaml(HERE / "dictionary" / "fnsuap.yaml")
    status = pratica_status(stored, alias, dictionary)
    reh = rehearsal_status()
    ran = {v["crawl"] for v in reh.values() if v["run"] and v["crawl"]}
    drift = cat.json.loads((cat.CAT / "drift.json").read_text())["pratiche"] if (cat.CAT / "drift.json").exists() else {}
    drifted = {n for n, d in drift.items() if d.get("differences")}
    checked = set(drift)
    sections = cat.cmd_count(argparse.Namespace(summary=True))
    lines = []
    for sp in ("sue", "suap"):
        rows = {n: s for n, s in status.items() if s["sportello"] == sp}
        fill = {n for n, s in rows.items() if not s["missing"]}
        short = {n: s for n, s in rows.items() if s["missing"]}
        run_n = {n for n in fill if n in ran or any(n == a for a in ran)}
        lines.append((sp, len(rows), len(fill), len(run_n), sorted(short.items(), key=lambda kv: len(kv[1]["missing"])),
                      f"{len(checked & set(rows))} checked, {len(drifted & set(rows))} changed"))
    return lines, sections, reh, status


HEAD = """# Napoli portal coverage

Where the map of impresainungiorno stands, counted from the catalogue and the rehearsals by
`claude/skills/pratica/portal/scoreboard.py --write` (run it with the pratica venv's Python).
Three claims, each stricter than the last:

- **Mapped**: the pratica is crawled (`catalogue/F839/sections/`): we know its sections and boxes.
- **Fillable**: mapped, and the dictionary fills every section of it, so `gen.py` can write its
  steps file. Nothing has touched the portal yet.
- **Run on the portal**: fillable, and a rehearsal generated from it has a dated run in its
  README that says the draft was **filled**: every value read back on a fresh load, with made-up
  people. Never declared, paid, signed or sent: that is the person's, by design.

"Drift-checked" counts the pratiche whose sections a drift check has compared with the live
portal (a changed one is refused by the runner); an unchecked pratica may have changed since its crawl.
A count here is a floor on what works, not a promise about a real case: a real case can take a
branch no rehearsal took.

"""


def render():
    lines, sections, reh, status = build()
    today = datetime.date.today().isoformat()
    names = {"sue": "SUE (building works)", "suap": "SUAP (businesses)"}
    out = [f"<!-- Generated by claude/skills/pratica/portal/scoreboard.py on {today}; do not edit by hand. -->", ""]
    out.append("| Sportello | Mapped | Fillable | Run on the portal | Drift-checked |")
    out.append("|---|---:|---:|---:|---:|")
    for sp, mapped, fill, run, short, drift in lines:
        out.append(f"| {names[sp]} | {mapped} | {fill} | {run} | {drift} |")
    out += ["", "By section use (how much of what pratiche show the dictionary fills):", ""]
    out += [f"- {s}" for s in sections]
    out += ["", "Rehearsals with no recorded run (written, never confirmed on the portal):", ""]
    none = [n for n, v in reh.items() if not v["run"]]
    out += [f"- `{n}`" for n in none] or ["- none"]
    out += ["", "SUAP pratiche one or two sections short of fillable (the cheapest gaps):", ""]
    suap_short = next(x for x in lines if x[0] == "suap")[4]
    near = [(n, s) for n, s in suap_short if len(s["missing"]) <= 2]
    out.append(f"- {len(near)} pratiche; {len(suap_short)} in all are short at least one section.")
    out += ["", "SUE pratiche not yet fillable:", ""]
    sue_short = next(x for x in lines if x[0] == "sue")[4]
    out += [f"- `{n}`: {', '.join(s['missing'])}" for n, s in sue_short] or ["- none"]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    text = render()
    if a.write:
        OUT.write_text(HEAD + text)
        print("wrote", OUT)
    else:
        print(text)
