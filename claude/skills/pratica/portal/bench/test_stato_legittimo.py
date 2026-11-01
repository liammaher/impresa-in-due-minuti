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
    r = run.preflight(steps, values(steps, a), made_up=True)
    assert r["ready"], {k: r[k] for k in ("unsupported", "questions", "proposals", "missing") if r[k]}
    return {p["id"]: p["value"] for p in run.plan(steps, values(steps, a)) if "precedenti edilizi" in p["section"].lower()}


def rows(a, recipe="scia-fittizia"):
    """The quadro's boxes this case fills, (label, value), after a pre-flight that must be ready.
    By label: once a choice in the quadro shifts the rows below it (the primo impianto's copy
    opens an upload box), gen.py gives the boxes after it no fixed id."""
    steps = STEPS[recipe]
    r = run.preflight(steps, values(steps, a), made_up=True)
    assert r["ready"], {k: r[k] for k in ("unsupported", "questions", "proposals", "missing") if r[k]}
    return [(p["label"] or "", p["value"]) for p in run.plan(steps, values(steps, a)) if "precedenti edilizi" in p["section"].lower()]


def has(rs, start):
    return [r for r in rs if gen.norm(r[0]).startswith(gen.norm(start))]


def refused(a, words, recipe="scia-fittizia"):
    steps = STEPS[recipe]
    r = run.preflight(steps, values(steps, a), made_up=True)
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


@case("built before titles, a title lost: the primo impianto's details or its copy, by its own boxes")
def _():
    # Each line's box, then one of its two boxes with no text (read as the line's label): the
    # epoca line's are nth 2 and 3, the prova line's nth 3 and 4 (the epoca line's are hidden).
    for name, radio, line in (("stato-epoca", "si tratta di immobile", 1), ("stato-prova", "non sono disponibili", 2)):
        rs = rows(answers(name))
        assert has(rs, radio) and has(rs, "altri documenti probanti"), rs
        boxes = [r for r in rs if gen.norm(r[0]).startswith(gen.norm("copia accatastamento"))]
        assert len(boxes) == 2, boxes
        assert {"5678", "01/03/1939"} <= {v for _, v in rs if v}, rs
        rs = rows(answers(name + "-copia"))
        assert len(has(rs, "copia accatastamento")) == 3 and not has(rs, "n."), rs  # line, copy, its upload
        assert any(v and v.endswith("accatastamento-primo-impianto.pdf") for _, v in rs), rs
    steps = STEPS["scia-fittizia"]
    nths = {(f.get("nth"), f["kind"]) for s in steps["sections"] if "precedenti edilizi" in s["section"].lower()
            for f in s["fields"] if (f.get("label") or "").startswith("copia accatastamento")}
    assert nths == {(None, "checkbox"), (2, "checkbox"), (3, "checkbox"), (4, "checkbox"), (None, "file")}, nths
    # Never an id: the crawl has the two boxes only as choices under the line's box.
    assert not [f for s in steps["sections"] for f in s["fields"]
                if (f.get("label") or "").startswith("copia accatastamento") and "id" in f]


@case("two titles of one kind: the second on an altro line, \"+\" for each line after the first")
def _():
    a = answers("stato-titoli-ripetuti")
    rs = rows(a)
    assert ("specificare", "denuncia di inizio attività") in rs and ("specificare", "condono edilizio") in rs, rs
    assert {"2004/88", "2009/412", "95/1207", "PG/2017/5531", "20/11/2017"} <= {v for _, v in rs if v}, rs
    steps = STEPS["scia-fittizia"]
    plan = [p for p in run.plan(steps, values(steps, a)) if "precedenti edilizi" in p["section"].lower()]
    adds = [p for p in plan if p["kind"] == "add"]
    assert len(adds) == 2, adds
    # The fourth line isn't added: its question said no.
    assert not [p for p in plan if p.get("value") == "{{ask.prec_altro_4_quale}}"]


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


@case("refused: more than ten altro lines, titles with none named, no document, no declaration")
def _():
    more = {}
    for i in range(4, 11):
        more |= {f"prec_altro_{i}": "true", f"prec_altro_{i}_quale": f"titolo {i}", f"prec_altro_{i}_numero": str(i),
                 f"prec_altro_{i}_data": f"20{i + 10}-01-01"}
    refused(answers("stato-titoli-ripetuti", **more, prec_altro_11="true"), "More than ten")
    refused(answers("stato-epoca", prova_documenti=[]), "catasto primo impianto or other documents")
    refused(answers("stato-titoli", precedenti=[]), "at least one title")
    refused(answers("stato-tolleranze", tolleranze_precedenti=[]), "where they were made")


@case("a question is asked only on its way: the sanctions case is never asked about titles")
def _():
    steps = STEPS["scia-fittizia"]
    a = answers("stato-sanzioni-estremi")
    del a["sanzione_importo"]
    r = run.preflight(steps, values(steps, a), made_up=True)
    asked = json.dumps(r["questions"])
    assert "sanzione_importo" in asked, asked
    assert "prec_permesso_numero" not in asked and "precedenti" not in asked, asked
    # The titles case is asked about a further altro line only once "altro" is ticked, and
    # about a third only once the second is.
    r = run.preflight(steps, values(steps, answers("stato-titoli", prec_altro_2=None)), made_up=True)
    keys = {q["key"]: q.get("only_if") for q in r["questions"]}
    assert "prec_altro_2" in keys and not keys["prec_altro_2"], keys
    assert keys.get("prec_altro_3") == ["prec_altro_2"], keys
    # A refusal's `if` stops at its first false word, as a `when` does: a building with no title
    # runs without the altro lines' answers, and a fourth line's "no" ends the questions there.
    for name in ("stato-epoca", "stato-titoli-ripetuti"):
        run.require_supported(steps, values(steps, answers(name)))


@case("the SCIA offers no free-land option; the permesso does")
def _():
    assert "area libera" not in STEPS["scia-fittizia"]["asks"]["stato_legittimo"]["options"]
    assert "area libera" in STEPS["pdc-fittizio"]["asks"]["stato_legittimo"]["options"]


print(f"\n{sum(results)} of {len(results)} passed")
sys.exit(0 if all(results) else 1)
