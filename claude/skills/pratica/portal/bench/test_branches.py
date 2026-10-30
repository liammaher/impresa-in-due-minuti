#!/usr/bin/env python3
"""Offline tests of branches.py: the national forms' choices against the SUE rehearsals' cases.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_branches.py

No browser, vault or network: the crawls, the steps files and schema/sue-choice-match.json.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
import branches  # noqa: E402

TICKS, MAPPED, LEAVES = branches.ticked(), branches.entries(), branches.left()


def state(crawl, section, label):
    bx = branches.boxes(crawl)
    box = next(b for b in bx if b["section"].startswith(section) and branches.norm(b["label"]).startswith(branches.norm(label)))
    return branches.status(box, TICKS, MAPPED, LEAVES, bx)


def labels_alike():
    """The crawl writes ’ where the dictionary writes ', and a section's name is the start of the portal's."""
    assert branches.norm("all’interno") == branches.norm("all'interno") == "all interno"
    assert branches.starts(branches.norm("unità immobiliare all’interno"), branches.norm("unità immobiliare all"))
    assert not branches.starts("a 20 nell ambito", "a 2")
    assert branches.same_section(branches.norm("Asseverazione SCIA - Tipologia di intervento, descrizione opere"),
                                 branches.norm("Asseverazione SCIA - Tipologia di intervento"))


def states():
    """A box a run took, one only the dictionary maps, one nothing maps."""
    st, who = state("scia", "c) Qualificazione", "senza opere (o con opere riconducibili agli interventi di cui all'articolo 6) di singola unità immobiliare all")
    assert st == "case" and "scia-fittizia" in who, (st, who)
    # Works finished in part: the fine lavori's recipe refuses it (its planimetria isn't mapped).
    assert state("fine-lavori", "", "in forma parziale")[0] == "mapped"
    assert state("scia", "Dati catastali", "Nuovo Catasto Terreni")[0] == "none"


def every_alternative_matched():
    """The match file answers every alternative of sue-choices.json, by boxes the crawls have."""
    forms = json.loads(branches.CHOICES.read_text())
    match = json.loads(branches.MATCH.read_text())["forms"]
    for form, rows in forms.items():
        texts = {(branches.norm(b["section"]), branches.norm(b["label"])) for b in branches.boxes(branches.FORMS[form])}
        for c in rows:
            for alt in c["alternatives"]:
                m = match[form][f"{c['id']}/{alt}"]
                for b in m["boxes"]:
                    assert (branches.norm(b["section"]), branches.norm(b["label"])) in texts, (form, c["id"], alt, b)


def table_current():
    """docs/schema-branches.md is what `branches.py table` writes now."""
    assert branches.OUT.read_text() == branches.table(), "regenerate: branches.py table"


def main():
    tests = [labels_alike, states, every_alternative_matched, table_current]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
