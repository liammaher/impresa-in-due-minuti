#!/usr/bin/env python3
"""How much of the SUE mapping is national, and how much Campania's or Napoli's: a rough split.

    portability.py            print docs/portability.md
    portability.py --write    rewrite docs/portability.md
    portability.py --json     the counts, every choice and rule with its level

Two layers, each counted from what the repository already holds:

  the portal's choices   every choice branches.py counts (the SUAP's own bollo options left out):
                         one InfoCamere's national forms have as an alternative of a choice
                         (schema/sue-choice-match.json) is `national`; one whose text names a
                         Campania law or Napoli (l.r. n. 19/2009, regolamento n. 4/2010) is
                         `campania-napoli`, matched or not; the rest are `form`: the national
                         forms' yes/no leaves (their xsd:choice list doesn't hold them) and the
                         portal's own boxes. "o della corrispondente normativa regionale" is the
                         national forms' own wording, not a Campania box.
  the rules tables       each rule of the SUE tables (rules/sue-napoli*.yaml) by the sources it cites, each source
                         placed by the host of its URL in the library (PRATICHE_NAPOLI_DIR):
                         Normattiva is national, the Regione Campania's sites Campania's, the
                         Comune's and the Soprintendenza for Napoli Napoli's, impresainungiorno
                         the portal (which operation to pick, not a law). A rule is `national`
                         if it cites only national law (and the portal), `uncited` if it cites
                         nothing, else it names the levels it adds. A host not in HOSTS stops
                         the count.

A rule that also cites a Comune page may only confirm the national rule there; a national rule
still holds only where the same portal (impresainungiorno's SUE front office) serves the comune.
The split is rough on purpose: a reading of meaning would be the hand comparison the CILA had
(rehearsals/cila-fittizia/schema/schema-vs-portal.md).

Run it with the pratica venv's Python (it imports branches.py and gen.py, which need PyYAML).
"""

import argparse
import collections
import datetime
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import branches  # noqa: E402
import gen  # noqa: E402

OUT = HERE.parents[3] / "docs" / "portability.md"
MATCH = HERE / "schema" / "sue-choice-match.json"
# New works, and the filings on a title held (2026-11-04).
RULES = [HERE / "rules" / "sue-napoli.yaml", HERE / "rules" / "sue-napoli-adempimenti.yaml"]


def table_rules():
    return [r for path in RULES for r in yaml.safe_load(path.read_text())["rules"]]

# A Campania law by its number (l.r. n. 15/2000, L.R.19/09, legge regionale n. 13), the regional
# seismic regulation, or the region or city by name.
LOCAL = re.compile(r"\bl\.\s?r\b|legge regionale\s+(n\.\s*)?\d|regolamento\s+(regionale\s+)?n\.\s*4/2010|campania|napoli",
                   re.I)
# Where a cited source is published, by host suffix.
HOSTS = {
    "normattiva.it": "national",
    "gazzettaufficiale.it": "national",
    "protezionecivile.gov.it": "national",
    "impresainungiorno.gov.it": "portal",
    "regione.campania.it": "campania",
    "comune.napoli.it": "napoli",
    "sabap.na.it": "napoli",
}
CHOICE_LEVELS = ["national", "form", "campania-napoli"]
RULE_LEVELS = ["national", "+napoli", "+campania", "+campania +napoli", "uncited"]


def matched():
    """{(section, label)} of the portal boxes a national form's alternative was matched to."""
    m = json.loads(MATCH.read_text())
    return {(gen.norm(b["section"]), gen.norm(b["label"])[:60])
            for alts in m["forms"].values() for a in alts.values() for b in a.get("boxes") or []}


def choices(rows=None):
    known = matched()
    out = []
    for r in rows if rows is not None else branches.rows():
        if r["state"] == "suap":
            continue
        text = " ".join(x for x in (r["choice"], r.get("option")) if x)
        if LOCAL.search(text):
            level = "campania-napoli"
        elif any((gen.norm(t), gen.norm(r["choice"])[:60]) in known for t in r["titles"]):
            level = "national"
        else:
            level = "form"
        out.append({"section": r["section"], "choice": r["choice"], **({"option": r["option"]} if r.get("option") else {}),
                    "pratiche": len(r["pratiche"]), "level": level})
    return out


def host_level(url):
    host = urlparse(url).hostname or ""
    for suffix, level in HOSTS.items():
        if host == suffix or host.endswith("." + suffix):
            return level
    raise ValueError(f"no level for host {host!r} ({url}): add it to HOSTS")


def sources(lib):
    """{(procedure, source id): level} for every source the table cites, from the library."""
    out = {}
    for r in table_rules():
        for c in r.get("cites") or []:
            key = (c["procedure"], c["source"])
            if key in out:
                continue
            proc = yaml.safe_load((Path(lib) / "procedures" / f"{c['procedure']}.yaml").read_text())
            found = [s for s in proc.get("sources") or [] if s["id"] == c["source"]]
            if not found:
                raise ValueError(f"{c['procedure']} has no source {c['source']}")
            out[key] = host_level(found[0]["url"])
    return out


def rules(lib):
    levels = sources(lib)
    out = []
    for r in table_rules():
        # A source is its procedure's: one id under two procedures may be two documents.
        cites = sorted({(c["procedure"], c["source"]) for c in r.get("cites") or []})
        cited = {levels[k] for k in cites}
        adds = [x for x in ("campania", "napoli") if x in cited]
        level = " ".join("+" + x for x in adds) or ("national" if cites else "uncited")
        out.append({"id": r["id"], "level": level, "portal": "portal" in cited,
                    "cites": [{"procedure": p, "source": s, "level": levels[(p, s)]} for p, s in cites],
                    "refuses": "refuse" in r["then"]})
    return out, levels


def pct(n, total):
    return f"{round(100 * n / total)}%" if total else "–"


def render(cs, rs, levels):
    today = datetime.date.today().isoformat()
    cc = collections.Counter(c["level"] for c in cs)
    lines = [
        "# The SUE mapping: national, Campania or Napoli", "",
        f"<!-- Generated by claude/skills/pratica/portal/portability.py on {today}; do not edit by hand. -->", "",
        "A rough split of what the SUE mapping rests on, for a comune or region other than Napoli: what "
        "carries over as it is, and what is Campania's or Napoli's. Counted, not read: see "
        "`portability.py` for how each line is placed.", "",
        "## The portal's choices", "",
        f"**{len(cs)} choices** on Napoli's SUE (`branches.py`, the SUAP's own bollo options left out); "
        f"{len(cs) - cc['campania-napoli']} ({pct(len(cs) - cc['campania-napoli'], len(cs))}) name no Campania "
        "or Napoli rule.", "",
        "| Level | Choices | Share | What it is |", "|---|---:|---:|---|",
        f"| national | {cc['national']} | {pct(cc['national'], len(cs))} | an alternative of a choice in InfoCamere's national forms |",
        f"| form | {cc['form']} | {pct(cc['form'], len(cs))} | the national forms' yes/no leaves and the portal's own boxes, no Campania or Napoli rule named |",
        f"| campania-napoli | {cc['campania-napoli']} | {pct(cc['campania-napoli'], len(cs))} | its text names a Campania law or Napoli |",
        "",
        "The CILA's fields, read one by one against the national form on 2026-10-28, were 133 of 152 "
        "in the form and 4 more asked elsewhere in it "
        "([schema-vs-portal.md](../rehearsals/cila-fittizia/schema/schema-vs-portal.md)): most `form` "
        "choices are the national forms' own.", "",
        "Choices naming Campania or Napoli:", "",
    ]
    seen = set()
    for c in cs:
        if c["level"] != "campania-napoli":
            continue
        key = (c["section"], c["choice"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {c['section'].strip()}: {c['choice'].strip()}")
    lines.append("")
    lines += ["## The rules tables", ""]
    if rs is None:
        lines += ["Not counted: PRATICHE_NAPOLI_DIR is unset (the sources' URLs are in the library).", ""]
        return "\n".join(lines)
    rc = collections.Counter(r["level"] for r in rs)
    portal = sum(r["portal"] for r in rs if r["level"] == "national")
    lines += [
        f"**{len(rs)} rules** in `rules/sue-napoli.yaml` and `rules/sue-napoli-adempimenti.yaml`, each by the sources it cites, placed by where "
        "the library has them published.", "",
        "| Level | Rules | Share | What it rests on |", "|---|---:|---:|---|",
        f"| national | {rc['national']} | {pct(rc['national'], len(rs))} | national law only ({portal} also cite the portal, for which operation to pick) |",
        f"| +napoli | {rc['+napoli']} | {pct(rc['+napoli'], len(rs))} | also a Comune or Soprintendenza source: a city rule, or a page confirming a national one |",
        f"| +campania | {rc['+campania']} | {pct(rc['+campania'], len(rs))} | also a Campania law or circular |",
        f"| +campania +napoli | {rc['+campania +napoli']} | {pct(rc['+campania +napoli'], len(rs))} | both |",
        f"| uncited | {rc['uncited']} | {pct(rc['uncited'], len(rs))} | cites no source (nothing to file, say) |",
        "", "Sources by level (rules citing each; one id under two procedures shows once per level):", "",
        "| Level | Source | Rules |", "|---|---|---:|",
    ]
    uses = collections.Counter()
    for r in rs:
        uses.update({(c["level"], c["source"]) for c in r["cites"]})
    order = ["national", "portal", "campania", "napoli"]
    for (lv, sid), n in sorted(uses.items(), key=lambda kv: (order.index(kv[0][0]), -kv[1], kv[0][1])):
        lines.append(f"| {lv} | `{sid}` | {n} |")
    lines += ["", "Rules that aren't national:", ""]
    for r in rs:
        if r["level"] == "uncited":
            lines.append(f"- `{r['id']}` (uncited)")
        elif r["level"] != "national":
            local = sorted({c["source"] for c in r["cites"] if c["level"] in ("campania", "napoli")})
            lines.append(f"- `{r['id']}` ({r['level']}): " + ", ".join(f"`{s}`" for s in local))
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help=f"rewrite {OUT.name} (needs PRATICHE_NAPOLI_DIR)")
    ap.add_argument("--json", action="store_true", help="the choices and rules, each with its level")
    a = ap.parse_args()
    lib = os.environ.get("PRATICHE_NAPOLI_DIR")
    if a.write and not lib:
        sys.exit("portability.py --write: set PRATICHE_NAPOLI_DIR (the rules' sources are in the library)")
    cs = choices()
    try:
        rs, levels = rules(lib) if lib else (None, {})
    except (ValueError, OSError) as e:
        sys.exit(f"portability.py: {e}")
    if a.json:
        json.dump({"choices": cs, "rules": rs}, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return
    text = render(cs, rs, levels)
    if a.write:
        OUT.write_text(text)
        print(f"wrote {OUT}")
    else:
        print(text)


if __name__ == "__main__":
    main()
