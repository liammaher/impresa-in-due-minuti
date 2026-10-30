#!/usr/bin/env python3
"""branches.py offline, on the crawls in catalogue/F839/sections and the dictionary.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_branches.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import branches  # noqa: E402
import gen  # noqa: E402

results = []
ROWS = branches.rows()


def case(name):
    def run(fn):
        try:
            fn()
            results.append(True)
            print(f"ok    {name}")
        except Exception as e:  # noqa: BLE001
            results.append(False)
            print(f"FAIL  {name}: {e}")
    return run


def one(section, choice, option=None):
    hits = [r for r in ROWS if gen.norm(r["section"]).startswith(gen.norm(section))
            and gen.norm(r["choice"]).startswith(gen.norm(choice)) and (option is None or r.get("option") == option)]
    assert hits, f"no row for {section!r} / {choice!r}"
    return hits[0]


@case("every choice has a known state, and a section is counted once")
def _():
    assert ROWS, "no rows"
    assert all(r["state"] in branches.STATES for r in ROWS)
    seen = {}
    for r in ROWS:
        key = (r["fingerprint"], r["id"], r.get("option"), r.get("under"))
        seen[key] = seen.get(key, 0) + 1
    # A radio pair's two "si" under one parent share a label, not an id: ids are unique.
    dup = [k for k, n in seen.items() if n > 1]
    assert not dup, f"counted twice: {dup[:3]}"


@case("a choice the dictionary ticks under an answer is ticked (the SCIA's systems)")
def _():
    assert one("Asseverazione SCIA - Sicurezza impianti", "Non comporta l'installazione")["state"] == "ticked"
    assert one("Asseverazione SCIA - Sicurezza impianti", "idrici e sanitari")["state"] == "ticked"


@case("a choice no entry names is unmapped (the land register)")
def _():
    assert one("Dati catastali", "Nuovo Catasto Terreni")["state"] == "unmapped"
    assert one("Dati catastali", "Nuovo Catasto Edilizio Urbano")["state"] == "ticked"


@case("another option of a dropdown set to one value is fixed")
def _():
    assert one("Qualifica e dati del procuratore", "Qualifica del procuratore", "NOTAIO")["state"] == "fixed"


@case("a section with no dictionary entry is no entry")
def _():
    # Made up: every crawled SUE section has an entry since the esonero's (2026-10-30).
    n = {"id": "r1c1p1reg:radio:0", "kind": "radio", "choice": "una scelta"}
    f = {"id": n["id"], "kind": "radio", "label": "una scelta"}
    assert branches.state(n, f, "Una sezione nuova", []) == "no entry"


@case("only the dictionary says what's the person's: an asseverazione stays the case's")
def _():
    r = one("Asseverazione SCIA - Inquinamento acustico", "costituisce variante e il sottoscritto assevera")
    assert r["state"] != "theirs", r["state"]


@case("a box a choice opened but the crawl never tried counts, marked not_tried (art. 94-bis's class)")
def _():
    r = one("Relazione Tecnica di Asseverazione C.I.L.A.", "intervento rilevante nei riguardi della pubblica")
    assert r.get("not_tried") and r["state"] == "unmapped" and r["under"].startswith("ha rilevanza strutturale"), r


@case("the weakest title decides: ticked under one title, not the other, is unmapped")
def _():
    n = {"id": "r1c1p1reg:chk", "kind": "checkbox", "choice": "una scelta"}
    f = {"id": n["id"], "kind": "checkbox", "label": "una scelta"}
    yes = [({"section": "A", "fields": [{"kind": "checkbox", "label": "una scelta"}]}, "A")]
    no = [({"section": "B", "fields": []}, "B")]
    assert branches.state(n, f, "A", yes) == "ticked"
    assert branches.state(n, f, "B", no) == "unmapped"
    assert max(["ticked", "unmapped"], key=branches.STATES.index) == "unmapped"


@case("the page renders with its counts")
def _():
    text = branches.render(ROWS)
    assert f"**{len(ROWS)} choices**" in text
    assert "## Unmapped, by section" in text


print(f"\n{sum(results)} of {len(results)} passed")
sys.exit(0 if all(results) else 1)
