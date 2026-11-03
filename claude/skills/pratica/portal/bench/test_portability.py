#!/usr/bin/env python3
"""portability.py offline, on the crawls in catalogue/F839/sections; with PRATICHE_NAPOLI_DIR, the
rules table's sources too.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_portability.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import branches  # noqa: E402
import gen  # noqa: E402
import portability  # noqa: E402

results = []
ROWS = branches.rows()
CHOICES = portability.choices(ROWS)
LIB = os.environ.get("PRATICHE_NAPOLI_DIR")


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


def level(section, choice):
    hits = [c for c in CHOICES if gen.norm(c["section"]).startswith(gen.norm(section))
            and gen.norm(c["choice"]).startswith(gen.norm(choice))]
    assert hits, f"no choice {section!r} / {choice!r}"
    return {c["level"] for c in hits}


@case("every SUE choice has a level, the SUAP's own left out")
def _():
    assert len(CHOICES) == sum(r["state"] != "suap" for r in ROWS)
    assert all(c["level"] in portability.CHOICE_LEVELS for c in CHOICES)


@case("an alternative of a national form's choice is national (the CILA's titolarità)")
def _():
    # Its section is named "a)" on the CILA, "b)" on others: one section, matched under any title.
    assert level("Titolarità dell'intervento", "avere titolarità esclusiva") == {"national"}


@case("a box naming a Campania law is campania-napoli (the piano casa, l.r. 19/2009)")
def _():
    assert level("a) Qualificazione pratica dell'intervento", "piano casa, ai sensi della l.r.") == {"campania-napoli"}
    assert level("Asseverazione PdC - Dati progettista", "Interventi di recupero abitativo dei sottotetti") == {"campania-napoli"}


@case("the national forms' \"corrispondente normativa regionale\" names no Campania law")
def _():
    assert "campania-napoli" not in level("Asseverazione SCIA - Sicurezza impianti", "altre tipologie di impianti")
    assert not portability.LOCAL.search("si allega la documentazione per il Comitato Tecnico Regionale")
    assert portability.LOCAL.search("ai sensi della L.R.19/09") and portability.LOCAL.search("regolamento n. 4/2010")


@case("a source is placed by its host, and an unknown host stops the count")
def _():
    assert portability.host_level("https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato") == "national"
    assert portability.host_level("https://portalesismica.regione.campania.it/x.pdf") == "campania"
    assert portability.host_level("https://static-www.comune.napoli.it/x.pdf") == "napoli"
    assert portability.host_level("https://www.impresainungiorno.gov.it/route/suap") == "portal"
    try:
        portability.host_level("https://example.org/x")
    except ValueError as e:
        assert "HOSTS" in str(e)
    else:
        raise AssertionError("an unknown host was placed")
    # A suffix, not a substring: notcomune.napoli.it is no Comune site.
    try:
        portability.host_level("https://notcomune.napoli.it/x")
    except ValueError:
        pass
    else:
        raise AssertionError("a lookalike host was placed")


@case("the rules table: every source placed, each rule by the levels it adds")
def _():
    if not LIB:
        print("      (PRATICHE_NAPOLI_DIR unset: the rules table's sources not read)")
        return
    rs, levels = portability.rules(LIB)
    by = {r["id"]: r for r in rs}
    assert all(r["level"] in portability.RULE_LEVELS for r in rs)
    assert by["altro"]["level"] == "+campania"  # the piano casa, l.r. 31/2021
    assert by["centro-storico-a1-a2"]["level"] == "+napoli"  # the Comune's variante, D.C.C. 129/2026
    assert by["sanatoria-titolo"]["level"] == "national"  # art. 6 DPR 380/2001 only
    assert by["permesso-sanatoria-zona-a-tutela"]["level"] == "national" and by["permesso-sanatoria-zona-a-tutela"]["portal"]
    # A rule citing nothing is not national by default (no works, no change of use: nothing to file).
    assert by["nessuna-opera-nessun-cambio"]["level"] == "uncited"
    text = portability.render(CHOICES, rs, levels)
    assert f"**{len(rs)} rules**" in text and "`lr13-2022`" in text and "`nessuna-opera-nessun-cambio` (uncited)" in text


@case("a source is its procedure's: one id under two procedures keeps each one's level")
def _():
    rs = [{"id": "x", "level": "+napoli", "portal": False, "refuses": False,
           "cites": [{"procedure": "a", "source": "pagina", "level": "national"},
                     {"procedure": "b", "source": "pagina", "level": "napoli"}]}]
    text = portability.render(CHOICES, rs, {("a", "pagina"): "national", ("b", "pagina"): "napoli"})
    assert "| national | `pagina` | 1 |" in text and "| napoli | `pagina` | 1 |" in text, text[-400:]
    assert "- `x` (+napoli): `pagina`" in text


@case("the page renders without the library, saying the rules weren't counted")
def _():
    text = portability.render(CHOICES, None, {})
    assert f"**{len(CHOICES)} choices**" in text and "PRATICHE_NAPOLI_DIR is unset" in text


print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
