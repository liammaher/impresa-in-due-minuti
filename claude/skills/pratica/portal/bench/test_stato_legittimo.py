#!/usr/bin/env python3
"""The stato legittimo quadro (the SCIA's and SCIA alternativa's f), the permesso's e)) offline:
gen.py on the crawls, then run.py's pre-flight and plan with the SCIA rehearsal's answers-stato-*
cases. No browser, vault or network.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_stato_legittimo.py
"""

import json
import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402
import run  # noqa: E402

os.chdir(ROOT)  # the answers name their files from the repo's root
SCIA = ROOT / "rehearsals" / "scia-fittizia"
FIELDS = dict(json.loads((ROOT / "rehearsals" / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
STEPS = {r: gen.generate(yaml.safe_load((ROOT / "rehearsals" / r / "recipe.yaml").read_text()))
         for r in ("scia-fittizia", "pdc-fittizio", "scia-sanatoria-fittizia")}
results = []


def case(name):
    def run_(fn):
        try:
            fn()
            results.append(True)
            print(f"ok    {name}")
        except Exception as e:  # noqa: BLE001
            results.append(False)
            print(f"FAIL  {name}: {e}")
    return run_


def answers(name, **change):
    a = json.loads((SCIA / f"answers-{name}.json").read_text())
    a.update(change)
    return {k: v for k, v in a.items() if v is not None}


def values(steps, a):
    return run.Values(dict(a), fields=dict(FIELDS), asks=steps.get("asks"))


def boxes(a, recipe="scia-fittizia"):
    """The quadro's boxes this case fills: {id: value}, after a pre-flight that must be ready."""
    steps = STEPS[recipe]
    r = run.preflight(steps, values(steps, a))
    assert r["ready"], {k: r[k] for k in ("unsupported", "questions", "proposals", "missing") if r[k]}
    return {p["id"]: p["value"] for p in run.plan(steps, values(steps, a)) if "precedenti edilizi" in p["section"].lower()}


def rows(a, recipe="scia-fittizia"):
    """The quadro's boxes this case fills, (label, value), after a pre-flight that must be ready.
    By label: once a choice in the quadro shifts the rows below it (the primo impianto's copy
    opens an upload box), gen.py gives the boxes after it no fixed id."""
    steps = STEPS[recipe]
    r = run.preflight(steps, values(steps, a))
    assert r["ready"], {k: r[k] for k in ("unsupported", "questions", "proposals", "missing") if r[k]}
    return [(p["label"] or "", p["value"]) for p in run.plan(steps, values(steps, a)) if "precedenti edilizi" in p["section"].lower()]


def has(rs, start):
    return [r for r in rs if gen.norm(r[0]).startswith(gen.norm(start))]


def refused(a, words, recipe="scia-fittizia"):
    steps = STEPS[recipe]
    r = run.preflight(steps, values(steps, a))
    assert any(words in u for u in r["unsupported"]), r["unsupported"]


@case("every title kind: its box, its number and its own date, the sanatoria heading once")
def _():
    rs = rows(answers("stato-titoli"))
    vals = {v for _, v in rs if v}
    assert has(rs, "che l’immobile/U.I. è stato oggetto del/i"), rs
    assert {"1234", "12/05/1965", "100", "10/01/1970", "112", "12/04/1982"} <= vals, vals
    assert len(has(rs, "del")) == 13, has(rs, "del")
    assert len(has(rs, "titolo edilizio in sanatoria")) == 1
    assert has(rs, "specificare") and has(rs, "pienamente conforme")
    assert not has(rs, "conforme alla documentazione dello stato legittimo o di fatto")
    for other in ("si tratta di immobile", "che per l’immobile", "che l’immobile/U.I. è stato oggetto della/e"):
        assert not has(rs, other), other


@case("built before titles, a title lost: refused until the primo impianto sub-choice is mapped")
def _():
    # The portal (2026-10-30): its details or its copy, by two boxes with no text the crawl didn't see.
    refused(answers("stato-epoca"), "isn't mapped yet")
    refused(answers("stato-prova"), "isn't mapped yet")


@case("sanctions: the receipt alone, or the payment's four details")
def _():
    rs = rows(answers("stato-sanzioni-ricevuta"))
    assert has(rs, "che per l’immobile") and has(rs, "si allega la relativa ricevuta")
    assert not has(rs, "si forniscono gli estremi") and not has(rs, "di Euro")
    steps = STEPS["scia-fittizia"]
    slot = [p for p in run.plan(steps, values(steps, answers("stato-sanzioni-ricevuta"))) if p["kind"] == "file"
            and (p["label"] or "").startswith("Ricevuta/e di versamento")]
    assert slot and slot[0]["value"].endswith("ricevuta-sanzione.pdf"), slot
    rs = rows(answers("stato-sanzioni-estremi"))
    assert has(rs, "si forniscono gli estremi") and not has(rs, "si allega la relativa ricevuta")
    assert {"1032", "04/06/2019", "PG/2019/123456", "01/07/2019"} <= {v for _, v in rs if v}


@case("tolerances: both declarations, each with its own number and date")
def _():
    rs = rows(answers("stato-tolleranze"))
    assert has(rs, "che l’immobile/U.I. è stato oggetto della/e")
    assert has(rs, "dichiarazione delle tolleranze di cui all’art. 34-bis o 34-ter, comma 4, presentata")
    assert has(rs, "dichiarazione delle tolleranze di cui all’art. 34-bis o 34-ter, comma 4, allegata")
    assert {"PG/2021/654321", "15/02/2021", "4321/1T", "30/09/2022"} <= {v for _, v in rs if v}


@case("in sanatoria the state is conforming with the sanatoria, not fully conforming")
def _():
    a = json.loads((ROOT / "rehearsals" / "scia-sanatoria-fittizia" / "answers-p6.json").read_text())
    rs = rows(a, "scia-sanatoria-fittizia")
    assert has(rs, "conforme alla documentazione dello stato legittimo o di fatto") and not has(rs, "pienamente conforme")


@case("the permesso's new construction on free land: its own radio, no conformity")
def _():
    a = json.loads((ROOT / "rehearsals" / "pdc-fittizio" / "answers-p6.json").read_text())
    a.update({"stato_legittimo": "area libera"})
    b = boxes(a, "pdc-fittizio")
    assert list(b) == ["r1c1p1reg:radio:0_clone"], b


@case("refused: two titles of one kind, titles with none named, no document, no declaration")
def _():
    refused(answers("stato-titoli", precedenti_ripetuti="true"), "same kind")
    refused(answers("stato-titoli", precedenti=[]), "at least one title")
    refused(answers("stato-tolleranze", tolleranze_precedenti=[]), "where they were made")


@case("a question is asked only on its way: the sanctions case is never asked about titles")
def _():
    steps = STEPS["scia-fittizia"]
    a = answers("stato-sanzioni-estremi")
    del a["sanzione_importo"]
    r = run.preflight(steps, values(steps, a))
    asked = json.dumps(r["questions"])
    assert "sanzione_importo" in asked, asked
    assert "prec_permesso_numero" not in asked and "precedenti" not in asked, asked


@case("the SCIA offers no free-land option; the permesso does")
def _():
    assert "area libera" not in STEPS["scia-fittizia"]["asks"]["stato_legittimo"]["options"]
    assert "area libera" in STEPS["pdc-fittizio"]["asks"]["stato_legittimo"]["options"]


print(f"\n{sum(results)} of {len(results)} passed")
sys.exit(0 if all(results) else 1)
