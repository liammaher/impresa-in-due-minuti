#!/usr/bin/env python3
"""Every choice on Napoli's SUE, and whether the dictionary takes it: the count of branches.

    branches.py            print docs/sue-branches.md
    branches.py --write    rewrite docs/sue-branches.md
    branches.py --json     every choice, one row each

A choice is one radio, one tick box or one dropdown option of a crawled section (crawl.js's
`branches`, and the choices those open, `then`; a radio or tick box a choice opened that the
crawl never tried itself counts too, as `not_tried`: what it opens isn't known). Sections are counted once by fingerprint,
whatever pratiche share them. gen.py lets a radio or a tick box the dictionary doesn't name
pass (a section is "filled" without it: the run leaves it unticked), so the scoreboard can't
see these; here each one is:

  ticked     a dictionary field names it, under some answer: Claude takes it when the case does
  answer     a dropdown whose value comes from an answer: which options it reaches isn't known here
  fixed      another option of a dropdown the dictionary sets to one value (the procuratore is
             always PROFESSIONISTA INCARICATO): a different kind of case, if it is one at all
  theirs     the person's (the dictionary's `theirs`, `omit`, or a declaration's section), never ticked
  left       a dictionary entry leaves it empty on purpose
  law        the law closes it to new cases (the dictionary's `law`: the piano casa, closed to new
             requests since 2022, or a repealed rule): not a gap, and a case that takes it is
             refused as the law's
  suap       a choice only the SUAP's procedures take (the dictionary's `suap_only`: the bollo's
             reasons for a fire-brigade or emissions filing): no SUE case does, so not a gap
  defect     a known portal defect blocks the case (the dictionary's `defect`, by defects.yaml id:
             the portal saves rows the law asks for together as one field): refused with the defect,
             not a gap in the mapping. What a law-, SUAP- or defect-closed box opens is closed with it,
             though its label is ticked elsewhere
  unmapped   the section has an entry, the choice is in none of it: a case that takes it is
             unmapped (a recipe refuses it, or pre-flight never asks it)
  no entry   the section isn't in the dictionary at all

Under every title the section shows: a choice is ticked only if each title's entries name it.
What the crawl couldn't see is flagged, not counted: a section whose top level holds exactly as
many choices as crawl.js tries by default (`limit`, 30) may have more, and what a `not_tried`
choice opens, or a dropdown the crawl saw open but never chose from.

Run it with the pratica venv's Python (it imports gen.py, which needs PyYAML).
"""
import argparse
import collections
import datetime
import json
import sys
from pathlib import Path

import catalogue as cat
import gen

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[3] / "docs" / "sue-branches.md"
LIMIT = 30  # crawl.js's default `limit` before 2026-10-31 (80 since; a cut section says `truncated`)
TICKS = ("radio", "checkbox", "tick")
STATES = ["ticked", "answer", "theirs", "left", "law", "suap", "defect", "fixed", "unmapped", "no entry"]


def distinct_sections():
    """Each SUE section once, by fingerprint: the crawled section, its titles, the pratiche
    showing it."""
    stored, cache = cat.crawls(), {}
    out = {}
    for name, c in stored.items():
        if cat.sportello(name) != "sue":
            continue
        cache.setdefault(name, c)
        for s in c["sections"]:
            if s.get("skipped") or s.get("error"):
                continue
            sec = cat.resolve(s["same_as"], cache) if s.get("same_as") else s
            fp = s.get("fingerprint") or cat.fingerprint(sec.get("fields", []))
            row = out.setdefault(fp, {"fingerprint": fp, "crawl": sec, "names": set(), "pratiche": set()})
            if not s.get("same_as") and not row["crawl"].get("branches") and sec.get("branches"):
                row["crawl"] = sec
            row["names"].add(s["section"])
            row["pratiche"].add(name)
    return out


def walk(nodes, fields, depth=1, parent=None):
    """(node, its crawled field, depth, parent node), the choices a choice opens after it, then
    the radios and tick boxes it opened that the crawl didn't try (at its depth limit, the art.
    94-bis class under a structural tolerance), as nodes marked `not_tried`."""
    by_id = {f["id"]: f for f in fields}
    for n in nodes or []:
        f = by_id.get(n["id"]) or {"id": n["id"], "kind": n["kind"], "label": n.get("choice", "")}
        yield n, f, depth, parent
        opened = [x for x in n.get("reveals", []) if x["kind"] != "message"]
        yield from walk(n.get("then"), fields + opened, depth + 1, n)
        tried = {x["id"] for x in n.get("then") or []}
        for x in opened:
            if x["kind"] in ("radio", "checkbox") and x["id"] not in tried:
                yield {"id": x["id"], "kind": x["kind"], "choice": x.get("label", ""), "not_tried": True}, x, depth + 1, n


def fitting(entries, crawl, name):
    """The entry gen.py fills a section with: the first that fits it ("Tecnici incaricati" is the
    SCIA's h1 and the permesso's g1, each with its own entry). None fits: all of them, as a
    recipe's own entries may complete one."""
    for e, as_name in entries:
        try:
            if not gen.fill(e, as_name, crawl, {}, name)[1]:
                return [(e, as_name)]
        except Exception:  # a recipe-only key (firms, subject) the empty recipe lacks
            pass
    return entries


def ticks(f, d, fields):
    """Whether a dictionary field ticks this choice, as gen.py's find picks the box: a label that
    starts its text, else, where no box of the section starts with it, one inside it (the CILA's
    "che i lavori sono/saranno eseguiti dall'impresa" is "lavori sono/saranno eseguiti dall")."""
    label = d.get("label", "")
    return gen.matches(f, d["kind"], label) or not any(gen.matches(x, d["kind"], label) for x in fields) \
        and gen.matches(f, d["kind"], label, inside=True)


def state(n, f, name, entries, fields=()):
    """What one title's dictionary entries do with one choice (`fields`: the section's boxes).
    Only the dictionary says what is the person's: crawl.js's own word list also catches the
    technician's asseverazioni ("il sottoscritto assevera"), which are the case's facts."""
    if cat.DECLARATIONS.search(name):
        return "theirs"
    if not entries:
        return "no entry"
    for entry, _ in entries:
        if entry.get("omit"):
            return "theirs"
        if any(gen.norm(f.get("label")).startswith(gen.norm(t)) for t in entry.get("theirs", [])):
            return "theirs"
    fixed = False
    for entry, _ in entries:
        for d in [*entry.get("fields", []), *entry.get("block", []),
                  *(b for e in entry.get("fields", []) if e.get("kind") == "each" for b in e["block"])]:
            if n["kind"] == "select":
                if d.get("kind") == "select" and gen.matches(f, "select", d.get("label", "")):
                    v = str(d.get("value", ""))
                    if "{{" in v:
                        return "answer"
                    if gen.norm(v) == gen.norm(n.get("option")):
                        return "ticked"
                    fixed = True
            elif d.get("kind") in TICKS and ticks(f, d, fields):
                return "ticked"
    for entry, _ in entries:
        if any(gen.norm(f.get("label")).startswith(gen.norm(x)) or gen.norm(f.get("context")).startswith(gen.norm(x))
               for x in entry.get("leave", [])):
            return "left"
    for entry, _ in entries:
        if any(gen.norm(f.get("label")).startswith(gen.norm(x)) for x in entry.get("law", [])):
            return "law"
    for entry, _ in entries:
        if any(gen.norm(f.get("label")).startswith(gen.norm(x)) for x in entry.get("suap_only", [])):
            return "suap"
    for entry, _ in entries:
        if any(gen.norm(f.get("label")).startswith(gen.norm(x)) for xs in (entry.get("defect") or {}).values() for x in xs):
            return "defect"
    return "fixed" if fixed else "unmapped"


def rows():
    dictionary = gen.load_yaml(HERE / "dictionary" / "fnsuap.yaml")
    out, seen, closed = [], set(), {}
    for fp, s in sorted(distinct_sections().items()):
        crawl = s["crawl"]
        base = [f for f in crawl.get("fields", []) if f["kind"] != "message"]
        top = len(crawl.get("branches") or [])
        names = sorted(s["names"])
        entries = {nm: fitting(gen.dictionary_entries(dictionary["sections"], nm), crawl, nm) for nm in names}
        walked = list(walk(crawl.get("branches"), base))
        boxes = [f for _, f, _, _ in walked]
        for n, f, depth, parent in walked:
            # One box reached by two paths (two same-label parents, the primo impianto line's
            # under epoca and under prova, both reveal it) is one choice.
            key = (fp, n["id"], n.get("option"), (parent or {}).get("choice"))
            if key in seen:
                continue
            seen.add(key)
            per = {nm: state(n, f, nm, entries[nm], boxes) for nm in names}
            # The weakest title decides: a choice ticked under one title and not another is
            # unmapped where it isn't.
            st = max(per.values(), key=STATES.index)
            # What a box the law or a defect closes opens is closed with it, though its label is
            # ticked elsewhere (art. 36-bis c. 1's receipt shares the double conformity's).
            up = closed.get((fp, (parent or {}).get("id"), (parent or {}).get("choice")))
            if up:
                st = up
            if st in ("law", "suap", "defect"):
                closed[(fp, n["id"], n.get("choice"))] = st
            out.append({
                "section": names[0], "titles": names, "fingerprint": fp, "pratiche": sorted(s["pratiche"]),
                "choice": (n.get("choice") or f.get("label") or "")[:160], "kind": n["kind"],
                **({"option": n["option"]} if n.get("option") else {}), "id": n["id"], "depth": depth,
                **({"under": (parent.get("choice") or "")[:80]} if parent else {}),
                "state": st, "opens": len([x for x in n.get("reveals", []) if x["kind"] != "message"]),
                **({"not_tried": True} if n.get("not_tried") else {}),
                **({"section_at_limit": True} if crawl.get("truncated") or top == LIMIT else {}),
            })
    return out


def render(rs):
    today = datetime.date.today().isoformat()
    count = collections.Counter(r["state"] for r in rs)
    secs = {r["fingerprint"]: r for r in rs}
    by_sec = collections.defaultdict(list)
    for r in rs:
        by_sec[r["fingerprint"]].append(r)
    capped = sorted({r["section"] for r in rs if r.get("section_at_limit")})
    untried = [r for r in rs if r.get("not_tried")]
    lines = [
        "# Napoli SUE: every choice", "",
        f"<!-- Generated by claude/skills/pratica/portal/branches.py on {today}; do not edit by hand. -->", "",
        "Every choice the crawls of Napoli's SUE have seen (a radio, a tick box, a dropdown option), each "
        "counted once however many pratiche share its section, and what the dictionary does with it. A "
        "case that takes an **unmapped** choice can't be filled yet. The scoreboard (`coverage.md`) counts "
        "a section as filled even with these left unticked, so they don't show there.", "",
        f"**{len(rs)} choices** in {len(secs)} sections that have any.", "",
        "| State | Choices | Meaning |", "|---|---:|---|",
        f"| ticked | {count['ticked']} | Claude takes it when the case does |",
        f"| answer | {count['answer']} | a dropdown filled from an answer (options reached not counted) |",
        f"| theirs | {count['theirs']} | the person's own (an acknowledgement, a declaration), never ticked |",
        f"| left | {count['left']} | left empty on purpose |",
        f"| law | {count['law']} | closed by law to new cases (the piano casa, a repealed rule): refused as the law's, not a gap |",
        f"| suap | {count['suap']} | an option only the SUAP's procedures take (the bollo's reasons for a fire-brigade or emissions filing): no SUE case, not a gap |",
        f"| defect | {count['defect']} | a known portal defect blocks the case (`defects.yaml`): refused with it, not a gap |",
        f"| fixed | {count['fixed']} | another option of a dropdown the dictionary sets to one value |",
        f"| unmapped | {count['unmapped']} | in a mapped section, not taken: a case that needs it is refused or not asked |",
        f"| no entry | {count['no entry']} | its section isn't in the dictionary yet |",
        "", "What the crawl didn't see (more choices may exist there):", "",
        f"- {len(capped)} sections cut at crawl.js's limit of choices (`truncated`, or exactly {LIMIT} from older crawls): "
        + (", ".join(capped) if capped else "none") + ".",
        f"- {len(untried)} of these choices the crawl saw but never tried: what they open isn't known"
        + (f" ({sum(r['state'] == 'law' for r in untried)} of them closed by law: no case takes them)."
           if any(r["state"] == "law" for r in untried) else "."),
        "- Choices only a saved answer shows (attachment slots, sections a scelta adds) aren't here: the "
        "crawl never saves.", "",
        "## Unmapped, by section", "",
        "Most shared first: closing a choice in a section many pratiche show helps all of them.", "",
    ]
    order = sorted(by_sec.items(), key=lambda kv: (-len(kv[1][0]["pratiche"]),
                                                   -sum(r["state"] in ("unmapped", "no entry") for r in kv[1]),
                                                   kv[1][0]["section"]))
    for fp, items in order:
        todo = [r for r in items if r["state"] in ("unmapped", "no entry")]
        if not todo:
            continue
        r0 = items[0]
        titles = " / ".join(r0["titles"])
        lines.append(f"### {titles}")
        lines.append("")
        lines.append(f"{len(r0['pratiche'])} pratiche; {len(todo)} of {len(items)} choices to map"
                     + (" (its section isn't in the dictionary)" if todo[0]["state"] == "no entry" else "") + ".")
        lines.append("")
        for r in todo:
            opt = r.get("option")
            what = r["choice"] + (f" → {opt}" if opt and gen.norm(opt) not in gen.norm(r["choice"]) else "")
            under = f" (under: {r['under']})" if r.get("under") else ""
            lines.append(f"- {r['kind']}: {what}{under}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help=f"rewrite {OUT.name}")
    ap.add_argument("--json", action="store_true", help="every choice as JSON")
    a = ap.parse_args()
    rs = rows()
    if a.json:
        json.dump(rs, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return
    text = render(rs)
    if a.write:
        OUT.write_text(text)
        print(f"wrote {OUT}")
    else:
        print(text)


if __name__ == "__main__":
    main()
