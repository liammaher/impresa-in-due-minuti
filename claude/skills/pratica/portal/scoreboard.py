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


# The wedge: what a Napoli architect or pratiche agency files again and again. The SUE side is
# every pratica of the building chain (CILA, SCIA, permesso, inizio and fine lavori, agibilità,
# proroghe, voltura, the DL and contractor changes, the landscape authorizations): all of them,
# since the SUE is to be mapped 100% for the technician (SUE_RARE would leave some out). The SUAP side is a grid of the sectors small Napoli
# businesses are in (indices into suap-wizard.json's `sectors`, which crawl names use) and the
# operations a business repeats through its life. Change the lists to move the wedge.
SUE_RARE = ()
WEDGE_SECTORS = [4, 5, 11, 16, 17, 18, 56, 60, 61]
WEDGE_OPS = [("aprire-l-attivita", "open"), ("subentrare-nell-esercizio-dell-attivita", "take over"),
             ("cessare-l-attivita", "close"), ("sospendere-l-attivita", "suspend"),
             ("trasferire-la-sede-dell-attivita", "move"), ("variazioni-soggetti", "change people"),
             ("variazioni-strutturali", "change premises")]
WEDGE_COMMON = ["suap-common-occupazione-suolo-pubblico-domanda-di-occupazione-suolo-pubb"]  # the dehors
SYMBOL = {"done": "run", "run": "fill", "map": "map", "crawl": "crawl", "none": "-"}
NEEDS = {
    "crawl": "crawl it in the pane on the scratch draft (20-60 s each; needs Liam logged in)",
    "map": "add the missing sections to the dictionary (draft.py drafts them; a person checks)",
    "run": "run it in the pane with made-up people (40-150 s; needs Liam logged in)",
}


# Hairdressers' sector has one operation per trade ("... di acconciatore"), named otherwise than the rest.
TRADE = ["subentrare-nell-attivita-di-{}", "cessare-l-attivita-di-{}", "sospendere-l-attivita-di-{}",
         "trasferire-la-sede-dell-attivita-di-{}", "variazioni-soggetti-in-attivita-di-{}",
         "variazioni-strutturali-in-attivita-di-{}"]


SHORT = {4: "Bakery (panificio)", 5: "Food workshop (pizza al taglio, gelateria)", 16: "Shop, non-food",
         17: "Shop, food or mixed", 18: "Shop, food eaten on the spot (protected zones)",
         56: "B&B, affittacamere (extralberghiere)", 60: "Bar / restaurant, normal zones",
         61: "Bar / restaurant, protected zones (centro storico)"}


def wedge_rows(wiz):
    """(label, sector index, the operation slug of each WEDGE_OPS column)."""
    rows = []
    for i in WEDGE_SECTORS:
        name = SHORT.get(i) or wiz["sectors"][i]["sector"]
        if i == 11:
            for trade in ("acconciatore", "estetista"):
                ops = ["aprire-l-attivita-di-" + trade] + [t.format(trade) for t in TRADE]
                rows.append(("Hairdresser (acconciatore)" if trade == "acconciatore" else "Beautician (estetista)", i, ops))
        else:
            rows.append((name, i, [op for op, _ in WEDGE_OPS]))
    return rows


def wedge(status, ran):
    """Each wedge cell: not offered by the sector, or what it still needs."""
    wiz = cat.json.loads((cat.CAT / "suap-wizard.json").read_text())
    cells, blockers = {}, {}
    for label, i, ops in wedge_rows(wiz):
        offered = {cat.slug(o.split(": ", 1)[1].split(" › ")[-1], 50) for o in wiz["sectors"][i]["operations"]}
        for col, op in enumerate(ops):
            name = f"suap-{i:03d}-{op}"
            if op not in offered:
                cells[label, col] = "none"
            elif name not in status:
                cells[label, col] = "crawl"
            elif status[name]["missing"]:
                cells[label, col] = "map"
                for m in status[name]["missing"]:
                    blockers.setdefault(m, set()).add(name)
            else:
                cells[label, col] = "done" if name in ran else "run"
    return wiz, cells, blockers


def wedge_text(status, ran):
    wiz, cells, blockers = wedge(status, ran)
    count = lambda v: sum(1 for x in cells.values() if x == v)
    n = len(cells) - count("none")
    d = WEDGE_COMMON[0]
    dehors = ("not crawled" if d not in status else "not fillable" if status[d]["missing"]
              else "run" if d in ran else "fillable, never run")
    out = ["## The wedge", "",
           "What a Napoli architect or pratiche agency files again and again, so what has to be perfect first.", "",
           "**SUE: every pratica of the building chain** (CILA, SCIA, permesso, start and end of works, agibilità, "
           "extensions, voltura, DL and contractor changes, the landscape authorizations), all of them.", ""]
    sue = {k: v for k, v in status.items() if v["sportello"] == "sue" and not k.startswith(SUE_RARE)}
    ok = [k for k, v in sue.items() if not v["missing"]]
    out += [f"- {len(ok)} of {len(sue)} fillable, {sum(1 for k in ok if k in ran)} run on the portal.", "",
            "**SUAP: nine sectors × seven operations.** Each cell is one pratica on the portal:", "",
            "| Sector | " + " | ".join(label for _, label in WEDGE_OPS) + " |",
            "|---|" + "---|" * len(WEDGE_OPS)]
    for label_full, _, ops in wedge_rows(wiz):
        label = label_full if len(label_full) < 60 else label_full[:57] + "..."
        out.append(f"| {label} | " + " | ".join(SYMBOL[cells[label_full, col]] for col in range(len(ops))) + " |")
    out += ["", "`run` = run on the portal; `fill` = fillable, never run; `map` = crawled, sections missing from the "
            "dictionary; `crawl` = not crawled; `-` = the sector doesn't offer it.", "",
            f"Of {n} cells: **{count('done')} run, {count('run')} fillable but not run, {count('map')} need "
            f"dictionary work, {count('crawl')} not crawled yet.**", "",
            f"Also in the wedge: the dehors ({dehors}), the outside sign and the alcohol notice as ticks "
            "inside an opening (their rehearsals have no recorded run), and the sectors' own notices "
            "(food safety, sanitary).", "",
            "### What each gap needs", ""]
    for key in ("run", "map", "crawl"):
        out.append(f"- **{count(key)} cells to {key}**: "
                   + NEEDS[key] + ".")
    out += ["- **Every cell**: the legal choice of which pratica a case needs (the library's rules table covers shops, "
            "bars and restaurants, hairdressers and beauticians and B&Bs; the bakery, the food workshop and "
            "moving premises have no entry in it), and a real case run past someone who knows the pratica.", ""]
    if blockers:
        out += ["Sections that block the most wedge cells (the cheapest way to turn `map` into `fill`):", ""]
        for m, cs in sorted(blockers.items(), key=lambda kv: -len(kv[1]))[:8]:
            out.append(f"- {len(cs)} cells: {m}")
        out.append("")
    return out


DEFINITION = [
    "**100% for the SUE means all of these**, for the 27 operations Napoli's SUE offers (and the combinations "
    "of two it allows):",
    "",
    "1. Every operation is crawled, and every section of it is in the dictionary.",
    "2. Every box of every screen is filled at every answer a real case can give: no refusal left in a recipe "
    "except one the law itself makes (a case that needs a human, said as such).",
    "3. The attachments screen is read for every answer that changes it, and every slot is mapped or named "
    "as the person's (a signed `.p7m`, a drawing).",
    "4. A drift check of the live portal against the crawls finds nothing new, and is repeated.",
    "5. Each pratica has been filled on the portal from a blank draft, and a real case has been checked by "
    "someone who files that pratica.",
]
# Open items the recipes can't show (a recipe has no line for what was never tried), from the working
# notes of 2026-10-28 to 10-30. Edit when one closes.
OPEN_BEYOND = [
    "Not mapped: PdC in sanatoria under art. 36-bis (refused: the portal makes two acknowledgment checkboxes "
    "a radio pair; art. 36 is filled); sanatoria in protected areas (building works plus landscape works); "
    "PdC and SCIA alternativa with a landscape authorization; any combination of two pratiche other than "
    "CILA+semplificata and SCIA+semplificata/ordinaria.",
    "SCIA in sanatoria, case 3 (art. 36-bis c. 1, Salva Casa): refused, because the portal's dating, oblazione "
    "and works-proposal radios behave as one group.",
    "The SCIA vincolo cases that stand alone (art. 136, art. 134) were never run on the portal.",
    "Attachments: where a slot depends on an answer, only the cases a rehearsal took are read, so other slots "
    "may be missing (the catalogue notes this for the pratiche read on an empty draft); the diritti amount per "
    "pratica is unknown.",
    "The screens after the attachments (the declarations' signing, the sending) and everything after filing "
    "(integration requests, the receipt, the status): nothing in the repo maps them.",
]


def sue_completeness(reh, status):
    """The refusals the SUE recipes still carry, counted from their `else:` messages: the
    recipe's own and those its sections bring from the dictionary (gen.py adds them)."""
    refusals = {}  # message -> recipes
    per = {}
    slots = {}  # (section, label) -> recipes: a ticked "si allega" with no slot under its condition
    for name, v in reh.items():
        if v["sportello"] != "sue":
            continue
        text = (REHEARSALS / name / "recipe.yaml").read_text()
        msgs = [m.group(1) for m in re.finditer(r'else:\s*"((?:[^"\\]|\\.)*)"', text)]
        try:
            steps = gen.generate(gen.load_yaml(REHEARSALS / name / "recipe.yaml"))
            msgs += [c["else"] for c in steps["supports"] if "else" in c and c["else"] not in msgs]
            for sec, label, _ in gen.unslotted(steps):
                slots.setdefault((sec, label), set()).add(name)
        except gen.GenError:
            pass  # not fillable yet: the recipe's own refusals only
        for msg in msgs:
            msg = msg.strip()
            if re.search(r"(isn't|aren't|not) (yet )?mapped|not mapped yet|mapped yet", msg):
                refusals.setdefault(msg, set()).add(name)
                per[name] = per.get(name, 0) + 1
    sue = {k: v for k, v in status.items() if v["sportello"] == "sue"}
    fill = [k for k, v in sue.items() if not v["missing"]]
    short = ", ".join("`" + k + "`" for k, v in sue.items() if v["missing"])
    out = ["## SUE completeness", ""] + DEFINITION + [
        "", "Measured today:", "",
        f"- Level 1: {len(fill)} of {len(sue)} pratiche fully in the dictionary" + (f" ({short} not)." if short else "."),
        f"- Level 2: **{sum(per.values())} refusals across {len(per)} recipes**, {len(refusals)} distinct messages.",
        f"- Level 3, in part: **{len(slots)} ticked \"si allega\" boxes with no attachment slot** under their"
        " condition (listed below): each may add a required slot a run would stop on.",
        "- Levels 4 and 5: not measured yet (see the open items).", "",
        "| Recipe | Refusals left |", "|---|---:|"]
    out += [f"| `{n}` | {c} |" for n, c in sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))]
    out += ["", "Refusals, by how many recipes carry them (the most shared are the cheapest to close once):", ""]
    for msg, rs in sorted(refusals.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        out.append(f"- {len(rs)}×: {msg[:170]}")
    out += ["", "Ticked \"si allega\" boxes with no attachment slot under their condition (gen.py `unslotted`; "
            "some only in cases a recipe refuses, some with no slot on the portal: a run tells):", ""]
    out += [f"- {len(rs)}×: {sec[:50]}: {label[:100]}" for (sec, label), rs in sorted(slots.items(), key=lambda kv: (-len(kv[1]), kv[0]))] or ["- none"]
    out += ["", "Open items no recipe shows:", ""] + [f"- {x}" for x in OPEN_BEYOND] + [""]
    return out


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
    ran = {v["crawl"] for v in reh.values() if v["run"] and v["crawl"]}
    out += [""] + sue_completeness(reh, status) + wedge_text(status, ran)
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
