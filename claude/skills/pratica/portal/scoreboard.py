#!/usr/bin/env python3
"""The portal map's scoreboard, counted from the catalogue and the rehearsals.

    scoreboard.py            print docs/coverage.md's tables
    scoreboard.py --write    rewrite docs/coverage.md

Three levels, each a stricter claim than the last (docs/coverage.md says them in words):

  mapped    a stored crawl of the pratica (catalogue/F839/sections/)
  fillable  mapped, and the dictionary fills every section of it (gen.py's own test)
  run       fillable, and a rehearsal recipe generated from it has a filled run in its runs.json

Run it with the pratica venv's Python (it imports gen.py, which needs PyYAML).
"""
import argparse
import datetime
import collections
import re
import sys
from pathlib import Path

import yaml

import catalogue as cat
import gen
import route
import runs

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
    """Each recipe: the crawl it was generated from, and whether its runs.json records a filled run."""
    out = {}
    for d in sorted(p for p in REHEARSALS.iterdir() if p.is_dir()):
        recipe = d / "recipe.yaml"
        if not recipe.exists():
            continue
        r = gen.resolved(gen.load_yaml(recipe))
        # A run that filled the draft, from its runs.json (a run that only stopped doesn't count).
        out[d.name] = {"crawl": r.get("crawl"), "sportello": r.get("sportello"), "run": runs.filled(runs.load(d)),
                       "readme": (d / "README.md").exists()}
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
    "a radio pair; art. 36 is filled). A SCIA in sanatoria in a protected area is mapped two ways: works done "
    "through the art. 36-bis c. 4 compatibility, works under way (art. 37 c. 5) with the authorization for the "
    "landscape works still to come; partly done landscape works under way are refused (art. 146 c. 4). "
    "The combinations of pratiche still to map are counted above, from the rules tables.",
    "SCIA in sanatoria, case 3 (art. 36-bis c. 1, Salva Casa): refused, because the portal saves its dating, "
    "oblazione and works proposal as one field with four values (checked 2026-11-01): a portal defect "
    "(docs/portal-defects.md), as is the permesso's under art. 36-bis. So is a variant to a pre-1977 title "
    "(art. 34-ter): its dating and oblazione are one field (checked 2026-11-02).",
    "PdC in sanatoria under art. 36 in a protected area: works that don't alter the place are filled "
    "(2026-11-02); works that do go with the accertamento of art. 167 in the same pratica, refused because the "
    "permesso's landscape quadro wants one of three procedures and none is that one (pdc-36-paesaggio, checked "
    "2026-11-02); new usable surface or volume is refused by law (art. 167 c. 4).",
    "The landscape vincolo alone: art. 136 (with the semplificata) and art. 142 (with the ordinaria) filled on the "
    "portal 2026-11-03, art. 134 (with the semplificata) on 2026-11-04; the ordinaria and the accertamento refuse art. 134 alone (their forms name only "
    "136 and 142). The parere di esonero's two mapping refusals (several previous titles, several Allegato A items) "
    "stay: the rules table refuses the parere in Napoli by law, so there is nothing to file them on.",
    "Attachments: where a slot depends on an answer, only the cases a rehearsal took are read, so other slots "
    "may be missing (the catalogue notes this for the pratiche read on an empty draft). The \"Elaborati richiesti "
    "per la sanatoria\" slot is mapped by the title a filled draft showed, never crawled. The diritti come from the Comune's 2026 "
    "table (G.C. 239/2026), by the case's facts; it can't say an onerous SCIA's, an onerous permesso's or SCIA "
    "alternativa's bracket (no ask holds the contributo's amount), a car park's (its floor area), works under "
    "way in sanatoria (art. 37 c. 5), the art. 10-septies proroghe or a landscape renewal: those are asked.",
    "Signed files: the portal checks every digital signature on upload and refuses a made-up one (2026-11-03), "
    "so the slots that take only signed files can't be filled with made-up data: on the portal only the "
    "refusal is proven; a real signed file, never yet. The second run after the declarations ran on the portal "
    "with made-up annexes (the Allegato A and the Modello DP under Allegati liberi, the DSC, 2026-11-03); the "
    "procura, signed only, never.",
    "Terre e rocce (DPR 120/2017): the wizard takes every two operations of different groups (sue-wizard.json "
    "`pairs`, all 190 probed 2026-11-03, none refused), and the rules table routes a title with the dichiarazione di "
    "utilizzo (art. 21: sites up to 6,000 m³, or larger ones with no VIA/AIA) to its combination, mapped for the CIL, "
    "CILA, SCIA, SCIA alternativa and permesso. The piano di utilizzo (art. 9, sites under VIA/AIA) goes apart to the "
    "VIA authority (the Regione's Staff Valutazioni Ambientali), never with a title; the DAU (art. 7) apart once the "
    "soil is used. Not in the table: edilizia libera that digs (its dichiarazione alone, the standalone rehearsal), "
    "works in sanatoria (the dichiarazione comes before the excavation), soil reused on the site (art. 24, no filing). "
    "A title, its landscape authorization and the dichiarazione are three operations in one pratica, mapped too: all 15 "
    "combinations filled on the portal with made-up data (2026-11-03); the dichiarazione itself is the portal's "
    "document, signed, so its slot is proven only empty and required, never with a real signed file.",
    "Drift: the check compares the 27 single operations' sections as they show before any choice (last "
    "2026-11-02); the combinations and what a choice opens are checked only by the runner's label checks.",
    "Portal defects (docs/portal-defects.md): none reported yet to InfoCamere or the Comune, the reports "
    "ready to send in docs/defect-reports/; two of them refuse common cases (a permesso with no energy "
    "incentive, a CILA or CIL before the firm is chosen).",
    "Firma e invio is the person's (unreachable on made-up data; FILING's yours says how). After filing, "
    "nothing in the repo maps the portal: integration requests, the codice pratica and receipt, the status "
    "in Pratiche inviate. InfoCamere's manual describes them (MyPage, \"Nuova Comunicazione\": portal/README.md), "
    "but only a sent pratica shows them, and made-up data sends none.",
    "No real case has been checked by an architect who files these pratiche (level 5).",
    # The audit of 2026-11-04 (what it found that no count above shows).
    "Which pratica a case needs: two rules tables route it (2026-11-04). sue-napoli takes new works (the title, "
    "the landscape authorization filed with it or extended or renewed with it, the terre e rocce); "
    "sue-napoli-adempimenti what is filed on a title held (inizio and fine lavori, agibilità, proroghe, "
    "voltura, a new direttore dei lavori or firm, the DAU). The person says which of the two: new works, or "
    "a title already held.",
    "Operations in one pratica: catalogue/F839/sue-pairs.yaml says, for each pair the wizard takes, whether a "
    "case files them together and why (counted above). Its `reading` reasons (two filings due at one moment: "
    "a title or its extension with what keeps the landscape authorization in force, the end of works with the "
    "DAU) are for an architect to confirm: the rules tables route these combinations on them, each such rule "
    "marked `Lettura` in the library's table.",
    "Several cadastral units are mapped, in both catasti (Dati catastali's two groups, 2026-11-04); "
    "a third group (back to the first catasto) is refused. The title's other holders take one row: more go in the "
    "assent's attachment, and the voltura's co-holders one person (portal defect coholders-one).",
    "Napoli's SUE wants every file PDF/A and signed (DD 501/2026), so on a real case every slot takes a signed "
    "file, and no real signed file has been uploaded yet: the attachments of a real pratica rest on that. "
    "InfoCamere's \"Copia pratica\" (a new pratica from one sent before) is read in its manual, never used.",
]


def pairs_line(reh):
    """The wizard's pairs and triples (catalogue/F839/sue-pairs.yaml) a case files together: how
    many have a steps file, how many of those ran on the portal; the rest, decided apart."""
    p = yaml.safe_load((HERE / "catalogue/F839/sue-pairs.yaml").read_text())
    entries = p["pairs"] + p["triples"]
    verdict = lambda e: p["reasons"][e["reason"]]["verdict"]
    together = [e for e in entries if verdict(e) == "together"]
    mapped = [e for e in together if e["rehearsals"]]
    ran = [e for e in mapped if any(reh.get(n, {}).get("run") for n in e["rehearsals"])]
    other = collections.Counter(verdict(e) for e in entries if verdict(e) != "together")
    return (f"- Operations in one pratica: of the {len(p['pairs'])} pairs the wizard takes and {len(p['triples'])} "
            f"triples a case needs, **{len(together)} are filed together**: {len(mapped)} with a steps file, "
            f"{len(ran)} of those run on the portal, **{len(together) - len(mapped)} still to map** "
            f"(`bench/test_pairs.py` lists them). The others are decided: "
            + ", ".join(f"{n} {k.replace('_', ' ')}" for k, n in sorted(other.items())) + ".")


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
        # As YAML reads them: an escaped quote left raw counted one refusal twice (2026-11-02).
        msgs = [yaml.safe_load('"' + m.group(1) + '"') for m in re.finditer(r'else:\s*"((?:[^"\\]|\\.)*)"', text)]
        try:
            steps = gen.generate(gen.load_yaml(REHEARSALS / name / "recipe.yaml"))
            msgs += [c["else"] for c in steps["supports"] if "else" in c and c["else"] not in msgs]
            for sec, label, _ in gen.unslotted(steps):
                slots.setdefault((sec, label), set()).add(name)
        except (gen.GenError, FileNotFoundError):  # a recipe whose crawl isn't imported yet (2026-11-04)
            pass  # not fillable yet: the recipe's own refusals only
        for msg in msgs:
            msg = msg.strip()
            if re.search(r"(isn't|aren't|not) (yet )?mapped|not mapped yet|mapped yet", msg):
                refusals.setdefault(msg, set()).add(name)
                per[name] = per.get(name, 0) + 1
    sue = {k: v for k, v in status.items() if v["sportello"] == "sue"}
    fill = [k for k, v in sue.items() if not v["missing"]]
    short = ", ".join("`" + k + "`" for k, v in sue.items() if v["missing"])
    # The rules table's cases, walked as bench/test_route.py walks them: a pratica counted alone
    # can be done while the same works with another pratica filed with it aren't (2026-10-31: the
    # permesso was, with its landscape authorization it wasn't, and this page didn't say).
    tables = [route.coverage(t, REHEARSALS) for t in ("sue-napoli", "sue-napoli-adempimenti")]
    c = {k: sum(x[k] for x in tables) for k in ("cases", "routed", "refused")}
    c["unmapped"] = sorted((kv for x in tables for kv in x["unmapped"]), key=lambda kv: (-kv[1], kv[0]))
    c["combinations"] = sorted({k for x in tables for k in x["combinations"]})
    combos = sum(1 for k in sue if k.startswith("sue-combo-"))
    bare = lambda p: p.removeprefix("napoli/comune/")
    combo = lambda k: " + ".join(bare(x) for x in [k[0], *k[1]])
    to_map = sum(n for _, n in c["unmapped"])
    out = ["## SUE completeness", ""] + DEFINITION + [
        "", "Measured today:", "",
        f"- Level 1: {len(fill)} of {len(sue)} pratiche fully in the dictionary" + (f" ({short} not)." if short else ".")
        + f" {combos} of them are two operations in one pratica (`sue-combo-*`).",
        f"- Which pratiche a case needs: of the {c['cases']} cases the rules tables decide, **{c['routed']} reach a "
        f"steps file**, {c['refused']} are refused with a reason or need no pratica, and **{to_map} have no steps "
        f"file yet**: {len(c['unmapped'])} combinations of pratiche, listed below (`bench/test_route.py`).",
        f"- Level 2: **{sum(per.values())} refusals across {len(per)} recipes**, {len(refusals)} distinct messages.",
        f"- Level 3, in part: **{len(slots)} ticked \"si allega\" boxes with no attachment slot** under their"
        " condition (listed below): each may add a required slot. A box read on a filled draft says what it adds"
        " (the dictionary's `slot`).",
        pairs_line(reh),
        "- Levels 4 and 5: not measured yet (see the open items).", "",
        "| Recipe | Refusals left |", "|---|---:|"]
    out += [f"| `{n}` | {k} |" for n, k in sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))]
    out += ["", "Pratiche filed together, mapped (a steps file each):", ""]
    out += [f"- {combo(k)}" for k in c["combinations"]] or ["- none"]
    out += ["", "Pratiche filed together, not mapped yet (the cases that need them, most first):", ""]
    out += [f"- {combo(k)}: {n} case{'s' * (n != 1)}" for k, n in c["unmapped"]] or ["- none"]
    out += ["", "Refusals, by how many recipes carry them (the most shared are the cheapest to close once):", ""]
    for msg, rs in sorted(refusals.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        out.append(f"- {len(rs)}×: {msg[:170]}")
    out += ["", "Ticked \"si allega\" boxes with no attachment slot under their condition (gen.py `unslotted`; "
            "some only in cases a recipe refuses, some with no slot on the portal: a filled draft's slots tell):", ""]
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
- **Run on the portal**: fillable, and a rehearsal generated from it has a run in its
  `runs.json` (the README's run table) that **filled** the draft: every value read back on a fresh load, with made-up
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
