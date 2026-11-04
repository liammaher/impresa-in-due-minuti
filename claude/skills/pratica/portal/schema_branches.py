#!/usr/bin/env python3
"""The national forms' choices against the cases the SUE rehearsals take: which alternative of
each choice some case ticks, which only the dictionary maps, which nothing maps. The empty rows
are the next cases to write.

  schema_branches.py choices <flattened-form.json>... --out schema/sue-choices.json
  schema_branches.py boxes --out <dir>      # each form's portal choice boxes, for the matching
  schema_branches.py table                  # writes docs/schema-branches.md

`choices` reads InfoCamere's forms as rehearsals/cila-fittizia/schema/flatten.py writes them:
an xsd:choice of the dichiarazioni or the asseverazione (not the anagrafica, an address or the
attachments) with its alternatives, each the element the choice picks. `boxes` lists the radios,
checkboxes and dropdowns of each form's crawl, those a choice reveals included, at every depth
the crawl tried. Which alternative
is which box is a reading of meaning, kept in schema/sue-choice-match.json (who matched, when).
`table` joins the three with the boxes each pre-flight-ready answers file of a SUE rehearsal
ticks (run.plan), and with the dictionary's `leave:` lists.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import run  # noqa: E402

ROOT = HERE.parents[3]
REHEARSALS = ROOT / "rehearsals"
SECTIONS = HERE / "catalogue" / "F839" / "sections"
CHOICES = HERE / "schema" / "sue-choices.json"
MATCH = HERE / "schema" / "sue-choice-match.json"
OUT = ROOT / "docs" / "schema-branches.md"
FIXTURE = REHEARSALS / "cila-fittizia" / "fixture-p6.json"

# Each national SUE form and the crawl of the pratica built from it.
FORMS = {
    "cila": "sue-comunicazione-inizio-lavoro-asseverata",
    "scia": "sue-segnalazione-certificata-di-inizio-attivita-edilizia",
    "permesso_di_costruire": "sue-permesso-di-costruire-art-10-d-p-r-380-2001",
    "scia_alternativa": "sue-segnalazione-certificata-inizio-attivita-alternativa-al-permesso-di-cost",
    "segnalazione_certificata_agibilita": "sue-segnalazione-certificata-per-l-agibilita",
    "comunicazione_inizio_lavori": "sue-comunicazione-inizio-lavori",
    "comunicazione_fine_lavori": "sue-comunicazione-di-fine-lavori",
}
# The wizard's operation each form is (sue-wizard.json): a form's choices apply only to cases that
# file it. Two forms share section names ("h) Impresa esecutrice dei lavori" is the CILA's and the
# permesso's), so by section alone the permesso's choices were held against CILA cases.
FORM_OPS = {
    "cila": "Comunicazione Inizio Lavoro Asseverata (C.I.L.A.)",
    "scia": "Segnalazione Certificata di Inizio Attività Edilizia (S.C.I.A.)",
    "permesso_di_costruire": "Permesso di Costruire (P.d.C) - Art.10 D.P.R. 380/2001",
    "scia_alternativa": "Segnalazione Certificata Inizio Attività alternativa al Permesso di Costruire (S.C.I.A. alternativa P.d.C.)",
    "segnalazione_certificata_agibilita": "Segnalazione Certificata per l'Agibilità",
    "comunicazione_inizio_lavori": "Comunicazione inizio lavori",
    "comunicazione_fine_lavori": "Comunicazione di fine lavori",
}
# Choices that are a person's or a place's details, not a branch of the case.
NOT_BRANCHES = re.compile(r"scheda_anagrafica|allegat|residente|/sede\b|/nato|indirizzo|recapito|coordinate|"
                          r"localitaEstera|domicilio|cittadinanza|documento", re.I)

# Sections of people's and places' details: their dropdowns are data, not choices of the case.
PEOPLE = re.compile(r"scheda anagrafica|procuratore|domicilio|localizzazione|tecnici incaricati|impresa esecutrice|"
                    r"dati catastali|professionisti|direttore dei lavori", re.I)


def form_name(path):
    m = re.search(r"mod_(.+?)_v\d", Path(path).name)
    return m[1] if m else Path(path).stem


def choices(paths):
    """{form: [{id, at, alternatives}]}: each xsd:choice outside the person's details, its
    alternatives the elements right under it (a subtype choice: the subtypes)."""
    out = {}
    for p in paths:
        leaves = json.loads(Path(p).read_text())
        groups = defaultdict(list)
        for f in leaves:
            if f.get("choice"):
                groups[f["choice"]].append(f["path"])
        rows = []
        for cid, paths_ in groups.items():
            base = cid.split("#")[0]
            if NOT_BRANCHES.search(base):
                continue
            alts = []
            for q in paths_:
                rest = q[len(base):].lstrip("/") if q.startswith(base) else q.rsplit("/", 1)[-1]
                alt = rest.split("/")[0] or q.rsplit("/", 1)[-1]
                if alt not in alts:
                    alts.append(alt)
            if cid.endswith("#subtype"):
                alts = [a for a in alts if "[" in a]
            if len(alts) < 2 and not cid.endswith("#subtype"):
                # A choice of one: the element or nothing (an optional declaration).
                alts = alts + ["(nothing)"]
            if len(alts) < 2:
                continue
            at = re.sub(r"^modulo_[^/]+/", "", base)
            rows.append({"id": f"{len(rows):03d}", "at": at, "alternatives": alts})
        out[form_name(p)] = rows
    return out


def crawl(name, seen=None):
    return json.loads((SECTIONS / f"{name}.json").read_text())


def sections_of(name):
    """A crawl's sections with their fields, a `same_as` resolved to the section it names."""
    out = []
    for s in crawl(name)["sections"]:
        if "skipped" in s:
            continue
        src = s
        if "same_as" in s:
            other, _, sec = s["same_as"].partition("#")
            src = next((t for t in crawl(other)["sections"] if t["section"] == sec), s)
        out.append({"section": s["section"], "fields": src.get("fields", []), "branches": src.get("branches", [])})
    return out


def boxes(name):
    """The radios, checkboxes and dropdown options of a crawl, those a choice reveals included,
    one per section and label (a box several choices reveal is one row, its ids all kept):
    [{box, section, kind, label, ids}]."""
    out, rows = [], {}

    def add(sec, kind, label, fid, **more):
        key = (sec, kind, norm(label))
        if not key[2]:  # a revealed copy the crawl saw with no text of its own can't be named
            return
        if key in rows:
            rows[key]["ids"] = sorted(set(rows[key]["ids"]) | {fid})
            return
        rows[key] = {"section": sec, "kind": kind, "label": label, "ids": [fid], **more}
        out.append(rows[key])

    def field(sec, f):
        if f.get("kind") == "select":
            # A list of places, codes or a person's details (sex, province, street type) is no branch.
            opts = f["options"] if isinstance(f.get("options"), list) else []
            for o in opts if len(opts) <= 12 and not PEOPLE.search(sec) else []:
                add(sec, "option", o, f["id"], of=f.get("label"))
        elif f.get("kind") in ("radio", "checkbox"):
            add(sec, f["kind"], f.get("label"), f["id"], **({"context": f["context"]} if f.get("context") else {}))

    def walk(sec, node, seen):
        # A choice tried under another (crawl.js `then`, as deep as the crawl went) names its box
        # by its `choice` text, cut short: it counts only where no fuller row has its id.
        for f in node.get("reveals", []):
            if isinstance(f, dict) and "id" in f:
                field(sec, f)
                seen.add(f["id"])
        for t in node.get("then", []):
            if isinstance(t, dict) and "id" in t:
                if t["id"] not in seen and (t.get("label") or t.get("choice")):
                    field(sec, {**t, "label": t.get("label") or t["choice"]})
                    seen.add(t["id"])
                walk(sec, t, seen)

    for s in sections_of(name):
        seen = {f["id"] for f in s["fields"] if "id" in f}
        for f in s["fields"]:
            field(s["section"], f)
        for b in s["branches"]:
            walk(s["section"], b, seen)
    for i, b in enumerate(out):
        b["box"] = f"P{i:03d}"
    return out


def revealers(name):
    """{box id: the label of the choice that shows it} for the boxes of a crawl a choice opens
    (crawl.js `reveals` and `then`); a box always on screen isn't in it."""
    out = {}

    def walk(node, parent):
        for f in node.get("reveals", []):
            if isinstance(f, dict) and "id" in f:
                out.setdefault(f["id"], parent)
        for t in node.get("then", []):
            if isinstance(t, dict) and "id" in t:
                out.setdefault(t["id"], parent)
                walk(t, t.get("label") or t.get("choice"))

    for s in sections_of(name):
        base = {f["id"] for f in s["fields"] if "id" in f}
        for b in s["branches"]:
            walk(b, b.get("label") or b.get("choice"))
        for i in base:
            out.pop(i, None)
    return out


def norm(s):
    """A label as the crawl and the dictionary both write it: no accents, quotes or punctuation."""
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()  # "all’interno" and "all'interno" alike


def starts(label, prefix):
    return bool(prefix) and (label == prefix or label.startswith(prefix + " "))


def same_section(a, b):
    """The dictionary names a section by the start of the portal's name for it."""
    return starts(a, b) or starts(b, a)


def steps_fields(steps):
    """(section, id, kind, label) of each tickable field and each dropdown value of a steps
    file; a templated dropdown value is "*" (any of its options)."""
    for sec in steps["sections"]:
        for x in sec["fields"]:
            if x["kind"] in ("radio", "checkbox", "tick"):
                yield norm(sec["section"]), x.get("id"), "tick", norm(x.get("label"))
            elif x["kind"] == "select":
                v = str(x.get("value", ""))
                yield norm(sec["section"]), x.get("id"), "option", "*" if "{{" in v else norm(v)


def sue_steps():
    for d in sorted(REHEARSALS.iterdir()):
        f, recipe = d / "portal-steps.generated.yaml", d / "recipe.yaml"
        if f.is_file() and recipe.is_file() and yaml.safe_load(recipe.read_text()).get("sportello") == "sue":
            yield d, yaml.safe_load(f.read_text())


def ticked():
    """[(section, id, kind, label, (rehearsal, answers))] for each box a pre-flight-ready
    answers file of a SUE rehearsal ticks, and each dropdown value it chooses."""
    fields = dict(json.loads(FIXTURE.read_text())["fields"])
    out = []
    os.chdir(ROOT)  # the answers name their files from the repo's root
    for d, steps in sue_steps():
        for a in sorted(d.glob("answers*.json")):
            values = run.Values(json.loads(a.read_text()), fields=fields, asks=steps.get("asks"))
            try:
                if not run.preflight(steps, values, made_up=True)["ready"]:
                    continue
                planned = run.plan(run.rehearsal(steps, values), values)
            except Exception:  # a case pre-flight can't plan offline counts as not taken
                continue
            for f in planned:
                if f["kind"] in ("radio", "checkbox", "tick"):
                    out.append((norm(f["section"]), f["id"], "tick", norm(f["label"]), (d.name, a.name)))
                elif f["kind"] == "select" and f["value"]:
                    out.append((norm(f["section"]), f["id"], "option", norm(f["value"]), (d.name, a.name)))
    return out


def filled():
    """{(rehearsal, answers file)} with a filled run on the portal recorded in its runs.json
    (bench/rerun.py --record writes them; earlier runs only where a README row names the case)."""
    out = set()
    for d, _ in sue_steps():
        f = d / "runs.json"
        for r in json.loads(f.read_text()) if f.is_file() else []:
            if r.get("result") == "filled":
                out.add((d.name, r["answers"]))
    return out


def entries():
    """[(section, id, kind, label, rehearsal)] for every field any SUE steps file can tick or
    choose, whatever its condition."""
    return [(*f, d.name) for d, steps in sue_steps() for f in steps_fields(steps)]


def hits(box, records, peers):
    """The records that name this box: its label's start (a dropdown value: the option's), and
    one of its ids, or no id (found by label on the page), or a start only this box has."""
    sec, lab = norm(box["section"]), norm(box["label"])
    mine = [b for b in peers if b["section"] == box["section"] and b["kind"] == box["kind"]]
    out = []
    for s, i, kind, l, who in records:
        if not same_section(s, sec) or (kind == "option") != (box["kind"] == "option"):
            continue
        if kind == "option":
            if (l == "*" and i in box["ids"]) or starts(lab, l):
                out.append(who)
        elif starts(lab, l) and (i is None or i in box["ids"] or sum(starts(norm(b["label"]), l) for b in mine) == 1):
            out.append(who)
    return out


def left():
    """{(section, label): why} for what the dictionary leaves empty (`leave:`) or to the
    person (`theirs:`, their acknowledgements)."""
    dic = yaml.safe_load((HERE / "dictionary" / "fnsuap.yaml").read_text())
    out = {}
    for s in dic["sections"]:
        for name in [s["section"]] + s.get("aliases", []):
            for why in ("leave", "theirs"):
                for lab in s.get(why, []):
                    out[(norm(name), norm(lab))] = why
    return out


def status(box, ticks, mapped, leaves, peers, runs=frozenset()):
    """("filled", rehearsals) when a case with a filled run on the portal ticks it, ("case",
    rehearsals) when only pre-flight-ready cases do; "mapped" when a steps file can, under a
    condition no case meets; "leave" or "theirs" when the dictionary says so; else "none"."""
    taken = hits(box, ticks, peers)
    if taken:
        return "filled" if any(t in runs for t in taken) else "case", sorted({r for r, _ in taken})
    if hits(box, mapped, peers):
        return "mapped", []
    sec, lab = norm(box["section"]), norm(box["label"])
    for (s, l), why in leaves.items():
        if same_section(s, sec) and starts(lab, l):
            return why, []
    return "none", []


STATES = {"filled": "filled on the portal", "case": "a case, no recorded run", "mapped": "mapped, no case yet", "none": "on the portal, not mapped",
          "leave": "left empty", "theirs": "the person's", "absent": "no portal box"}
READ = {"cila": "CILA", "scia": "SCIA", "permesso_di_costruire": "Permesso di costruire",
        "scia_alternativa": "SCIA alternativa", "segnalazione_certificata_agibilita": "Agibilità (SCA)",
        "comunicazione_inizio_lavori": "Inizio lavori", "comunicazione_fine_lavori": "Fine lavori"}


def short(text, n=90):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def table():
    forms = json.loads(CHOICES.read_text())
    match = json.loads(MATCH.read_text())
    ticks, mapped, leaves, runs = ticked(), entries(), left(), filled()
    cases = sorted({who for *_, who in ticks})
    summary, detail, todo = [], [], []
    for form, rows in forms.items():
        bx = boxes(FORMS[form])
        by_text = {(norm(b["section"]), norm(b["label"])): b for b in bx}
        counts, used = defaultdict(int), set()
        lines = []
        for c in rows:
            for alt in c["alternatives"]:
                m = match["forms"][form].get(f"{c['id']}/{alt}", {})
                found = [by_text[k] for k in ((norm(x["section"]), norm(x["label"])) for x in m.get("boxes", [])) if k in by_text]
                states = [status(b, ticks, mapped, leaves, bx, runs) for b in found]
                used |= {b["box"] for b in found}
                order = ["filled", "case", "mapped", "none", "leave", "theirs"]
                st = min((x[0] for x in states), key=order.index) if states else "absent"
                who = sorted({r for x in states for r in x[1]})
                counts[st] += 1
                where = "; ".join(short(b["label"], 70) for b in found) or short(m.get("note", ""), 70)
                lines.append(f"| `{short(c['at'], 60)}` | `{alt}` | {where} | {(m.get('confidence') or '?')[0]} | {STATES[st]} | {len(who) or ''} |")
                if st in ("mapped", "none"):
                    todo.append((st, READ[form], c["at"], alt, where))
        portal_only = [b for b in bx if b["box"] not in used and status(b, ticks, mapped, leaves, bx, runs)[0] in ("mapped", "none")]
        total = sum(counts.values())
        summary.append(f"| {READ[form]} | {total} | {counts['filled']} | {counts['case']} | {counts['mapped']} | {counts['none']} | "
                       f"{counts['absent']} | {len(portal_only)} |")
        detail += [f"### {READ[form]}", "", "| Schema choice | Alternative | Portal box | Match | State | Rehearsals |",
                   "|---|---|---|---|---|---:|"] + lines + [""]
        if portal_only:
            detail += [f"Portal boxes of the {READ[form]} no schema alternative matched and no case ticks:", ""]
            detail += [f"- {short(b['section'], 40)}: {short(b['label'])} ({'mapped' if status(b, ticks, mapped, leaves, bx)[0] == 'mapped' else 'not mapped'})"
                       for b in portal_only] + [""]
    head = [
        "# The national forms' choices against our cases", "",
        f"<!-- Generated by claude/skills/pratica/portal/schema_branches.py table; do not edit by hand. -->", "",
        "Each row is one alternative of a choice in InfoCamere's national form (one of the options a",
        "person picks, such as who holds the title or which landscape procedure applies), the portal box",
        "that means it on Napoli's SUE, and whether one of our cases takes it. A row with no case is a",
        "branch no rehearsal has taken: the next cases to write.", "",
        "- **filled on the portal**: a pre-flight-ready answers file of a SUE rehearsal ticks that box,",
        "  and the rehearsal's `runs.json` records a filled run of it (`bench/rerun.py --record`).",
        "- **a case, no recorded run**: such a case ticks it, but no filled run is recorded: never run,",
        "  stopped, or run before 2026-10-31 and described in its README in words that don't name the",
        f"  case ({len(cases)} cases in all, {len(runs & set(cases))} with a recorded filled run).",
        "- **mapped, no case yet**: the dictionary can tick it, under answers no case gives. Next: an",
        "  answers file, then a run.",
        "- **on the portal, not mapped**: no steps file ever ticks it. Next: a dictionary entry.",
        "- **no portal box**: Napoli's form has no box for it (or it is a value, not a tick).", "",
        "Some rows can't be a Napoli case: Napoli is in seismic zone 2, so the low-seismicity",
        "alternatives (`*zona_sismica_bassa`) never apply there.", "",
        f"Schema: InfoCamere `Sistema-Informatico-degli-Sportelli-Unici-Moduli-PA`, commit `fc13e08`, the 7",
        "SUE forms flattened (`schema/sue-choices.json`). Which alternative is which box was read by",
        f"{match.get('by', '?')} on {match.get('made', '?')} (`schema/sue-choice-match.json`): leads, not",
        "checked one by one (Match: h, m, l for the matcher's high, medium, low confidence). A box",
        "several choices reveal is one row here: a combination of choices (this option under that",
        "parent) isn't told apart. Rehearsals counts the rehearsals whose cases tick the box.", "",
        "| Form | Alternatives | Filled on the portal | A case, no recorded run | Mapped, no case | Not mapped | No portal box | Portal-only boxes untaken |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    nxt = ["", "## Next cases", "", "Mapped, no case yet (an answers file away):", ""]
    nxt += [f"- {f}: `{a}` → `{alt}` ({w})" for st, f, a, alt, w in todo if st == "mapped"] or ["- none"]
    nxt += ["", "On the portal, not mapped (dictionary work first):", ""]
    nxt += [f"- {f}: `{a}` → `{alt}` ({w})" for st, f, a, alt, w in todo if st == "none"] or ["- none"]
    return "\n".join(head + summary + nxt + ["", "## Every choice", ""] + detail).rstrip() + "\n"


# Rows the flattening split out of one choice of the national form, at one path: ticking the
# other row's box states this one. The permesso's stato legittimo is shown by its titles, its era,
# a lost title or tolerances (009), or the works are a new building on free land (008), which has
# none: the plot case ticks 008 (filled on the portal 2026-11-02). Its conformity (011), at the
# same path, is required either way: the portal stopped on it.
SPLIT = {("permesso_di_costruire", "009"): ["008"]}


def required():
    """[(form, choice id, at, rehearsal, answers file)]: a choice of the national form with no
    "(nothing)" alternative (one of them must be stated), its boxes in a section the case files,
    and the case ticks none. The free land's conformity (choice 011 of the permesso) was one: the
    portal stopped on it (2026-11-02). Not judged, rather than guessed: a choice under a parent
    alternative the case doesn't take (or one this can't name), one with an alternative no portal
    box matches (it may be stated another way), and one with the person's boxes. A choice whose
    boxes only another choice shows is required only where the case ticks that one: the
    flattening sometimes puts such a choice at its parent's path (the agibilità's "completamente"
    under "vale come fine lavori"). An option the flattening gave its own row (`at` + "/name")
    counts as one of the choice's."""
    forms = json.loads(CHOICES.read_text())
    match = json.loads(MATCH.read_text())
    leaves = left()
    fields = dict(json.loads(FIXTURE.read_text())["fields"])
    cases = []
    os.chdir(ROOT)  # the answers name their files from the repo's root
    import gen  # noqa: E402 (portal/, on the path)
    for d, steps in sue_steps():
        recipe = gen.resolved(gen.load_yaml(d / "recipe.yaml"))
        ops = set(recipe["operation"] if isinstance(recipe["operation"], list) else [recipe["operation"]])
        for a in sorted(d.glob("answers*.json")):
            values = run.Values(json.loads(a.read_text()), fields=fields, asks=steps.get("asks"))
            try:
                if not run.preflight(steps, values, made_up=True)["ready"]:
                    continue
                planned = run.plan(run.rehearsal(steps, values), values)
                sections = [norm(x["section"]) for x in run.expand(steps, values)["sections"]]
            except Exception:
                continue
            ticks = [(norm(f["section"]), f["id"], "tick", norm(f["label"]), (d.name, a.name))
                     for f in planned if f["kind"] in ("radio", "checkbox", "tick")]
            ticks += [(norm(f["section"]), f["id"], "option", norm(f["value"]), (d.name, a.name))
                      for f in planned if f["kind"] == "select" and f["value"]]
            cases.append(((d.name, a.name), sections, ticks, ops))
    out = []
    for form, rows in forms.items():
        bx = boxes(FORMS[form])
        by_text = {(norm(b["section"]), norm(b["label"])): b for b in bx}
        # The form's boxes some alternative names: a box only Napoli's form has (Campania's attics,
        # car parks) that a case ticks in a choice's section may be that case's answer to it.
        named = {(norm(x["section"]), norm(x["label"])) for e in match["forms"][form].values() for x in e.get("boxes", [])}
        napoli = [b for b in bx if (norm(b["section"]), norm(b["label"])) not in named]
        found = lambda c, alt: [by_text[k] for k in ((norm(x["section"]), norm(x["label"]))
                                for x in match["forms"][form].get(f"{c['id']}/{alt}", {}).get("boxes", [])) if k in by_text]
        shows = revealers(FORMS[form])
        for c in rows:
            if "(nothing)" in c["alternatives"]:
                continue
            # A choice nested under a name no row lists as an option (after its last [..._ctype]):
            # its parent can't be told, so neither can whether it applies.
            tail = c["at"].rsplit("]", 1)[1] if "]" in c["at"] else ""
            if tail.strip("/") and not any(c["at"].startswith(p["at"] + "/") and tail.strip("/").split("/")[0] in p["alternatives"] for p in rows):
                continue
            alts = {alt: found(c, alt) for alt in c["alternatives"]}
            if not all(alts.values()):
                continue
            mine = [b for bs in alts.values() for b in bs]
            # An option with a row of its own (its sub-choice): any of that row's boxes takes it.
            for sub in rows:
                if sub["at"].startswith(c["at"] + "/") and "/" not in sub["at"][len(c["at"]) + 1:]:
                    mine += [b for alt in sub["alternatives"] for b in found(sub, alt)]
            if any(same_section(s, norm(b["section"])) and starts(norm(b["label"]), l) for b in mine for (s, l) in leaves):
                continue
            parent = max((p for p in rows if c["at"].startswith(p["at"] + "/")), key=lambda p: len(p["at"]), default=None)
            under = None
            if parent:
                seg = re.sub(r"^\[|\]$", "", c["at"][len(parent["at"]) + 1:].split("/")[0])
                if seg not in parent["alternatives"]:
                    continue
                under = found(parent, seg)
                if not under:
                    continue
            for other in SPLIT.get((form, c["id"]), []):
                row = next(r for r in rows if r["id"] == other)
                mine += [b for alt in row["alternatives"] for b in found(row, alt)]
            own = [b for b in napoli if any(same_section(norm(b["section"]), norm(m["section"])) for m in mine)]
            # Shown only under other choices (every box of it): the labels that show it.
            shown = {shows[i] for b in mine for i in b["ids"] if i in shows} if all(any(i in shows for i in b["ids"]) for b in mine) else None
            for who, sections, ticks, ops in cases:
                if FORM_OPS[form] not in ops or not any(same_section(s, norm(b["section"])) for b in mine for s in sections):
                    continue
                if any(hits(b, ticks, bx) for b in own):
                    continue
                if shown is not None and not any(starts(l, norm(x)[:50]) or starts(norm(x), l[:50]) for *_, l, _ in ticks for x in shown if x):
                    continue
                if under is not None and not any(hits(b, ticks, bx) for b in under):
                    continue
                if not any(hits(b, ticks, bx) for b in mine):
                    out.append((READ[form], c["id"], c["at"], *who))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("choices")
    c.add_argument("forms", nargs="+")
    c.add_argument("--out", type=Path, default=CHOICES)
    b = sub.add_parser("boxes")
    b.add_argument("--out", type=Path, required=True)
    m = sub.add_parser("match", help="keep matchers' answers (by box id) as section and label")
    m.add_argument("dir", type=Path)
    m.add_argument("--by", required=True)
    m.add_argument("--made", required=True)
    sub.add_parser("table")
    sub.add_parser("required", help="cases that state none of a required choice's alternatives")
    a = ap.parse_args()
    if a.cmd == "required":
        rows = required()
        print("\n".join(f"{f} {i} `{at}`: {r}/{ans}" for f, i, at, r, ans in rows) or "none")
        return
    if a.cmd == "match":
        forms = json.loads(CHOICES.read_text())
        out = {"made": a.made, "by": a.by, "forms": {}}
        for form, rows in forms.items():
            got = json.loads((a.dir / f"{form}.json").read_text())["alternatives"]
            bx = {b["box"]: b for b in boxes(FORMS[form])}
            keys = [f"{c['id']}/{alt}" for c in rows for alt in c["alternatives"]]
            if set(keys) - set(got):
                sys.exit(f"{form}: no answer for {sorted(set(keys) - set(got))[:5]}")
            out["forms"][form] = {k: {"boxes": [{"section": bx[i]["section"], "label": bx[i]["label"]} for i in got[k]["boxes"]],
                                      "confidence": got[k].get("confidence"), "note": got[k].get("note", "")} for k in keys}
        MATCH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        return
    if a.cmd == "choices":
        a.out.write_text(json.dumps(choices(a.forms), ensure_ascii=False, indent=1) + "\n")
    elif a.cmd == "boxes":
        a.out.mkdir(parents=True, exist_ok=True)
        for form, name in FORMS.items():
            (a.out / f"{form}.json").write_text(json.dumps(boxes(name), ensure_ascii=False, indent=1) + "\n")
    else:
        OUT.write_text(table())


if __name__ == "__main__":
    main()
