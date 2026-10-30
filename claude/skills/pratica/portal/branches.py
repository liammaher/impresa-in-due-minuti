#!/usr/bin/env python3
"""The national forms' choices against the cases the SUE rehearsals take: which alternative of
each choice some case ticks, which only the dictionary maps, which nothing maps. The empty rows
are the next cases to write.

  branches.py choices <flattened-form.json>... --out schema/sue-choices.json
  branches.py boxes --out <dir>      # each form's portal choice boxes, for the matching
  branches.py table                  # writes docs/schema-branches.md

`choices` reads InfoCamere's forms as rehearsals/cila-fittizia/schema/flatten.py writes them:
an xsd:choice of the dichiarazioni or the asseverazione (not the anagrafica, an address or the
attachments) with its alternatives, each the element the choice picks. `boxes` lists the radios,
checkboxes and dropdowns of each form's crawl, those a choice reveals included. Which alternative
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
    "cila": "cila",
    "scia": "scia",
    "permesso_di_costruire": "sue-permesso-di-costruire-art-10-d-p-r-380-2001",
    "scia_alternativa": "sue-segnalazione-certificata-inizio-attivita-alternativa-al-permesso-di-cost",
    "segnalazione_certificata_agibilita": "agibilita",
    "comunicazione_inizio_lavori": "inizio-lavori",
    "comunicazione_fine_lavori": "fine-lavori",
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

    for s in sections_of(name):
        for f in s["fields"]:
            field(s["section"], f)
        for b in s["branches"]:
            for f in b.get("reveals", []) + b.get("then", []):
                if isinstance(f, dict) and "id" in f:
                    field(s["section"], f)
    for i, b in enumerate(out):
        b["box"] = f"P{i:03d}"
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
                if not run.preflight(steps, values)["ready"]:
                    continue
                planned = run.plan(steps, values)
            except Exception:  # a case pre-flight can't plan offline counts as not taken
                continue
            for f in planned:
                if f["kind"] in ("radio", "checkbox", "tick"):
                    out.append((norm(f["section"]), f["id"], "tick", norm(f["label"]), (d.name, a.name)))
                elif f["kind"] == "select" and f["value"]:
                    out.append((norm(f["section"]), f["id"], "option", norm(f["value"]), (d.name, a.name)))
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


def status(box, ticks, mapped, leaves, peers):
    """("case", rehearsals) when a ready case ticks it; "mapped" when a steps file can, under a
    condition no case meets; "leave" or "theirs" when the dictionary says so; else "none"."""
    taken = hits(box, ticks, peers)
    if taken:
        return "case", sorted({r for r, _ in taken})
    if hits(box, mapped, peers):
        return "mapped", []
    sec, lab = norm(box["section"]), norm(box["label"])
    for (s, l), why in leaves.items():
        if same_section(s, sec) and starts(lab, l):
            return why, []
    return "none", []


STATES = {"case": "a case takes it", "mapped": "mapped, no case yet", "none": "on the portal, not mapped",
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
    ticks, mapped, leaves = ticked(), entries(), left()
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
                states = [status(b, ticks, mapped, leaves, bx) for b in found]
                used |= {b["box"] for b in found}
                order = ["case", "mapped", "none", "leave", "theirs"]
                st = min((x[0] for x in states), key=order.index) if states else "absent"
                who = sorted({r for x in states for r in x[1]})
                counts[st] += 1
                where = "; ".join(short(b["label"], 70) for b in found) or short(m.get("note", ""), 70)
                lines.append(f"| `{short(c['at'], 60)}` | `{alt}` | {where} | {(m.get('confidence') or '?')[0]} | {STATES[st]} | {len(who) or ''} |")
                if st in ("mapped", "none"):
                    todo.append((st, READ[form], c["at"], alt, where))
        portal_only = [b for b in bx if b["box"] not in used and status(b, ticks, mapped, leaves, bx)[0] in ("mapped", "none")]
        total = sum(counts.values())
        summary.append(f"| {READ[form]} | {total} | {counts['case']} | {counts['mapped']} | {counts['none']} | "
                       f"{counts['absent']} | {len(portal_only)} |")
        detail += [f"### {READ[form]}", "", "| Schema choice | Alternative | Portal box | Match | State | Rehearsals |",
                   "|---|---|---|---|---|---:|"] + lines + [""]
        if portal_only:
            detail += [f"Portal boxes of the {READ[form]} no schema alternative matched and no case ticks:", ""]
            detail += [f"- {short(b['section'], 40)}: {short(b['label'])} ({'mapped' if status(b, ticks, mapped, leaves, bx)[0] == 'mapped' else 'not mapped'})"
                       for b in portal_only] + [""]
    head = [
        "# The national forms' choices against our cases", "",
        f"<!-- Generated by claude/skills/pratica/portal/branches.py table; do not edit by hand. -->", "",
        "Each row is one alternative of a choice in InfoCamere's national form (one of the options a",
        "person picks, such as who holds the title or which landscape procedure applies), the portal box",
        "that means it on Napoli's SUE, and whether one of our cases takes it. A row with no case is a",
        "branch no rehearsal has taken: the next cases to write.", "",
        "- **a case takes it**: a pre-flight-ready answers file of a SUE rehearsal ticks that box",
        f"  ({len(cases)} such cases; nearly all have a filled run on the portal).",
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
        "| Form | Alternatives | A case takes it | Mapped, no case | Not mapped | No portal box | Portal-only boxes untaken |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    nxt = ["", "## Next cases", "", "Mapped, no case yet (an answers file away):", ""]
    nxt += [f"- {f}: `{a}` → `{alt}` ({w})" for st, f, a, alt, w in todo if st == "mapped"] or ["- none"]
    nxt += ["", "On the portal, not mapped (dictionary work first):", ""]
    nxt += [f"- {f}: `{a}` → `{alt}` ({w})" for st, f, a, alt, w in todo if st == "none"] or ["- none"]
    return "\n".join(head + summary + nxt + ["", "## Every choice", ""] + detail).rstrip() + "\n"


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
    a = ap.parse_args()
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
