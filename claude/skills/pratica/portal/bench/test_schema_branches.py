#!/usr/bin/env python3
"""Offline tests of schema_branches.py: the national forms' choices against the SUE rehearsals' cases.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_schema_branches.py

No browser, vault or network: the crawls, the steps files and schema/sue-choice-match.json.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
import schema_branches as sb  # noqa: E402

TICKS, MAPPED, LEAVES = sb.ticked(), sb.entries(), sb.left()


def state(crawl, section, label):
    bx = sb.boxes(crawl)
    box = next(b for b in bx if b["section"].startswith(section) and sb.norm(b["label"]).startswith(sb.norm(label)))
    return sb.status(box, TICKS, MAPPED, LEAVES, bx)


def labels_alike():
    """The crawl writes ’ where the dictionary writes ', and a section's name is the start of the portal's."""
    assert sb.norm("all’interno") == sb.norm("all'interno") == "all interno"
    assert sb.starts(sb.norm("unità immobiliare all’interno"), sb.norm("unità immobiliare all"))
    assert not sb.starts("a 20 nell ambito", "a 2")
    assert sb.same_section(sb.norm("Asseverazione SCIA - Tipologia di intervento, descrizione opere"),
                                 sb.norm("Asseverazione SCIA - Tipologia di intervento"))


def states():
    """A box a run took, one only the dictionary maps, one nothing maps."""
    st, who = state("sue-segnalazione-certificata-di-inizio-attivita-edilizia", "c) Qualificazione", "senza opere (o con opere riconducibili agli interventi di cui all'articolo 6) di singola unità immobiliare all")
    assert st == "case" and "scia-fittizia" in who, (st, who)
    # The same box once a run of a case that ticks it is recorded as filled (runs.json).
    bx = sb.boxes("sue-segnalazione-certificata-di-inizio-attivita-edilizia")
    box = next(b for b in bx if b["section"].startswith("c) Qualificazione") and sb.norm(b["label"]).startswith(sb.norm("senza opere (o con opere")))
    runs = {who for *_, who in TICKS}
    assert sb.status(box, TICKS, MAPPED, LEAVES, bx, runs)[0] == "filled"
    # Works finished in part: a case ticks it since 2026-11-03 (the planimetria in its own slot);
    # before, the recipe refused it and the box was only mapped.
    st, who = state("sue-comunicazione-di-fine-lavori", "", "in forma parziale")
    assert st == "case" and "fine-lavori-fittizia" in who, (st, who)
    # The land register: a case ticks it since 2026-11-02 (the permesso's plot), not yet run.
    assert state("sue-segnalazione-certificata-di-inizio-attivita-edilizia", "Dati catastali", "Nuovo Catasto Terreni")[0] == "case"
    # The procuratore born abroad: a CILA case ticks it since 2026-11-02 (the shared section).
    st, who = state("sue-segnalazione-certificata-di-inizio-attivita-edilizia", "Qualifica e dati del procuratore", "all'Estero")
    assert st == "case" and "cila-fittizia" in who, (st, who)


def required_choices():
    """No ready case states none of a required choice; and the report catches the free land's
    conformity (choice 011 of the permesso) when its tick is taken away, as it was until a portal
    run stopped on it (2026-11-02)."""
    assert sb.required() == []
    real = sb.sue_steps

    def without_conformity():
        for d, steps in real():
            if d.name == "pdc-fittizio":
                steps = {**steps, "sections": [{**sec, "fields": [f for f in sec["fields"]
                         if not sb.norm(f.get("label")).startswith(sb.norm("pienamente conforme alla documentazione"))]}
                         for sec in steps["sections"]]}
            yield d, steps
    sb.sue_steps = without_conformity
    try:
        flagged = {(i, r, a) for _, i, _, r, a in sb.required()}
    finally:
        sb.sue_steps = real
    assert ("011", "pdc-fittizio", "answers-terreno.json") in flagged, sorted(flagged)[:5]


def deeper_boxes():
    """A box only a choice under another choice reveals, two levels down, is listed; a deeper
    choice's own box counts once, by its fuller label."""
    import tempfile
    crawl = {"sections": [{"section": "a) Prova", "fields": [
        {"id": "r1:radio:0_clone", "kind": "radio", "label": "primo caso"}],
        "branches": [{"choice": "primo caso", "id": "r1:radio:0_clone", "kind": "radio",
                      "reveals": [{"id": "r2:chk", "kind": "checkbox", "label": "copia accatastamento di primo impianto"}],
                      "then": [{"choice": "copia accatastamento", "id": "r2:chk", "kind": "checkbox",
                                "then": [{"choice": "estremi", "id": "r3:radio:1_clone", "kind": "radio",
                                          "reveals": [{"id": "r4:radio:2_clone", "kind": "radio", "label": "2%, per le U.I. > 500 mq"}]}]}]}]}]}
    before = sb.SECTIONS
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "prova.json").write_text(json.dumps(crawl))
        sb.SECTIONS = Path(tmp)
        try:
            labels = [b["label"] for b in sb.boxes("prova")]
        finally:
            sb.SECTIONS = before
    assert labels == ["primo caso", "copia accatastamento di primo impianto", "estremi", "2%, per le U.I. > 500 mq"], labels


def every_alternative_matched():
    """The match file answers every alternative of sue-choices.json, by boxes the crawls have."""
    forms = json.loads(sb.CHOICES.read_text())
    match = json.loads(sb.MATCH.read_text())["forms"]
    for form, rows in forms.items():
        texts = {(sb.norm(b["section"]), sb.norm(b["label"])) for b in sb.boxes(sb.FORMS[form])}
        for c in rows:
            for alt in c["alternatives"]:
                m = match[form][f"{c['id']}/{alt}"]
                for b in m["boxes"]:
                    assert (sb.norm(b["section"]), sb.norm(b["label"])) in texts, (form, c["id"], alt, b)


def table_current():
    """docs/schema-branches.md is what `schema_branches.py table` writes now."""
    assert sb.OUT.read_text() == sb.table(), "regenerate: schema_branches.py table"


def main():
    tests = [labels_alike, states, deeper_boxes, every_alternative_matched, required_choices, table_current]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
