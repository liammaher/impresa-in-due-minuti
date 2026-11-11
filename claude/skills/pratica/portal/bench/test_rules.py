#!/usr/bin/env python3
"""Offline tests of the rules tables (rules.py) and how gen.py and run.py preflight use them.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_rules.py

No browser, vault or network: the non-food shop's and the restaurant's rehearsals, and the
SUE's building ones (library/rules/sue-napoli.yaml), changed one fact at a time.
"""

import copy
import itertools
import json
import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
import gen  # noqa: E402
import route  # noqa: E402
import rules  # noqa: E402
import run  # noqa: E402

gen.ensure()  # the rehearsals' steps files are built, never committed (steps.lock)
REHEARSALS = HERE.parents[4] / "rehearsals"
TABLE = rules.table("suap-napoli")


def case(name, fixture, **answers):
    """A rehearsal's pre-flight report, its answers changed (None drops one)."""
    d = REHEARSALS / name
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((REHEARSALS / fixture / "fixture.json").read_text())["fields"])
    a = json.loads((d / "answers.json").read_text())
    for k, v in answers.items():
        if v is None:
            a.pop(k, None)
        else:
            a[k] = v
    return run.preflight(steps, run.Values(a, fields=fields, asks=steps.get("asks")), made_up=True)


def shop(**answers):
    return case("negozio-fittizio", "negozio-fittizio", **answers)


def restaurant(**answers):
    return case("ristorante-fittizio", "pizzeria-fittizia", **answers)


def every_case_decided_once():
    """As the library's validator: every combination of the facts (numbers at each bound
    and past it) is decided by a main rule or refused, never by two that disagree."""
    domains = []
    for name, f in TABLE["facts"].items():
        if f["type"] == "choice":
            domains.append(list(f["values"]))
        elif f["type"] == "yes_no":
            domains.append([True, False])
        else:
            bounds = {b for r in TABLE["rules"] if isinstance(r["when"].get(name), dict) for b in r["when"][name].values()}
            domains.append(sorted({0.0} | bounds | {b + 1 for b in bounds}))
    n = 0
    for combo in itertools.product(*domains):
        d = rules.decide(TABLE, dict(zip(TABLE["facts"], combo)))
        assert not d["conflict"] and (d["main"] or d["refused"]), (combo, d)
        n += 1
    assert n > 10000, n


def decide_answers():
    d = rules.decide(TABLE, {"attivita": "somministrazione", "evento": "apertura"})
    assert d["ask"] == ["zona", "somministrazione_particolare", "prevenzione_incendi", "alcolici", "insegna", "musica",
                        "dehors"], d["ask"]
    assert d["main"] is None
    facts = {"attivita": "somministrazione", "evento": "apertura", "zona": "a", "somministrazione_particolare": False,
             "prevenzione_incendi": False, "alcolici": False, "insegna": False, "musica": True, "dehors": False}
    d = rules.decide(TABLE, facts)
    assert d["main"]["regime"] == "autorizzazione", d
    assert [a["procedure"] for a in d["also"]] == ["napoli/comune/nulla-osta-impatto-acustico",
                                                   "napoli/asl-napoli-1/registrazione-attivita-alimentare"], d["also"]
    d = rules.decide(TABLE, {**facts, "evento": "subingresso"})
    assert d["refused"] and not d["main"], d


def ready_as_proven():
    for name, fx in [("negozio-fittizio", "negozio-fittizio"), ("negozio-insegna-fittizio", "negozio-fittizio"),
                     ("ristorante-fittizio", "pizzeria-fittizia"), ("subingresso-negozio-fittizio", "negozio-fittizio"),
                     ("subingresso-ristorante-fittizio", "pizzeria-fittizia"), ("ampliamento-negozio-fittizio", "negozio-fittizio"),
                     ("cessazione-fittizia", "pizzeria-fittizia"),
                     ("ristorante-centro-storico-fittizio", "ristorante-centro-storico-fittizio")]:
        r = case(name, fx)
        assert r["ready"], (name, r)


def facts_asked():
    r = restaurant(zona=None, fatti=None)
    assert [q["key"] for q in r["questions"]][:2] == ["zona", "fatti"], r["questions"]
    zona = r["questions"][0]
    assert zona["type"] == "choice" and zona["options"] == ["a", "b", "c"] and zona["labels"]["c"] and zona["how"], zona
    items = [i["key"] for i in r["questions"][1]["items"]]
    assert items == ["somministrazione_particolare", "prevenzione_incendi", "alcolici", "musica", "dehors"], items
    # The shop's facts: never its zone, which no rule for a non-food shop reads.
    r = shop(fatti=None)
    assert [q["key"] for q in r["questions"]] == ["fatti"], r["questions"]
    d = REHEARSALS / "negozio-fittizio"
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    answers = {k: v for k, v in json.loads((d / "answers.json").read_text()).items() if k != "fatti"}
    fields = dict(json.loads((d / "fixture.json").read_text())["fields"])
    raises(lambda: run.require_supported(steps, run.Values(answers, fields=fields, asks=steps["asks"])),
           "unanswered: ask.alcolici, ask.dehors, ask.insegna, ask.prevenzione_incendi")


def refused_by_the_table():
    assert shop(superficie_vendita_mq="300")["unsupported"] == [
        next(r["then"]["refuse"] for r in TABLE["rules"] if r["id"] == "vicinato-oltre-250-mq")]
    assert "Agenzia delle Dogane" in shop(fatti=["alcolici"])["unsupported"][0]
    assert restaurant(zona="a")["unsupported"][0].startswith(
        "Questo caso è un'altra pratica: " + N("napoli/comune/scia-somministrazione-alimenti-bevande")
        + " (sul portale: Esercizio di somministrazione di alimenti e bevande in zone tutelate")


def other_pratiche():
    assert shop(fatti=["insegna"])["unsupported"] == [
        f"Questo caso chiede anche {N('napoli/comune/insegna-esercizio')}, che questa pratica non presenta."]
    assert case("negozio-insegna-fittizio", "negozio-fittizio", fatti=[])["unsupported"] == [
        f"Questa pratica presenta anche {N('napoli/comune/insegna-esercizio')}, che a questo caso non serve."]
    assert N("napoli/comune/concessione-suolo-pubblico-dehors") in restaurant(fatti=["dehors"])["unsupported"][0]


SUE = rules.table("sue-napoli")
N = run.procedure_name  # a procedure as the tecnico reads it: its library title


def sue(name, answers="answers-p6.json", **changes):
    """A SUE rehearsal's pre-flight report with the P6 fixture's fields, its answers changed
    (None drops one)."""
    d = REHEARSALS / name
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads((REHEARSALS / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    a = json.loads((d / answers).read_text())
    for k, v in changes.items():
        if v is None:
            a.pop(k, None)
        else:
            a[k] = v
    return run.preflight(steps, run.Values(a, fields=fields, asks=steps.get("asks")), made_up=True)


def sue_every_case_decided_once():
    """Every case of the SUE table is decided by one main rule, by "none needed", or refused.

    The walk is route.cases(): each fact as decide() asks it (seconds). The product of every
    fact's values (34.5 million, 45 minutes here) is the library's validator's
    (tools/lib/rules.ts, validateRules). Both hold the same cases: once decide() asks nothing,
    every rule has a false condition or has fired, so no fact left unset can change the
    decision. That is what this checks at each leaf, which the product did by setting them all:
    a fact decide() fails to ask would leave a rule open here."""
    n = 0
    for facts, d in route.cases("sue-napoli"):
        assert not d["conflict"] and (d["main"] or d["none"] or d["refused"]), (facts, d)
        for r in SUE["rules"]:
            held = [rules._holds(c, facts.get(name)) for name, c in r["when"].items()]
            assert False in held or None not in held, (facts, r["id"])
        n += 1
    assert n > 1000, n


def sue_rehearsals_ready():
    names = ["cil-fittizia", "cila-fittizia", "cila-paesaggistica-fittizia", "scia-fittizia", "scia-paesaggistica-semplificata-fittizia",
             "scia-paesaggistica-ordinaria-fittizia", "pdc-fittizio", "scia-alternativa-fittizia",
             "paesaggistica-semplificata-fittizia", "paesaggistica-ordinaria-fittizia", "scia-sanatoria-fittizia", "accertamento-paesaggistico-fittizio", "pdc-sanatoria-fittizio",
             "parere-esonero-fittizio"]
    # A whole building's change of use with CILA works: the national SCIA form has a box for it,
    # but in Campania it is a SCIA alternativa (art. 2 c. 6 L.R. 13/2022).
    refused = {("scia-fittizia", "answers-cambio-immobile-6bis.json"): "Questo caso è un'altra pratica: " + N("napoli/comune/scia-alternativa-pdc"),
               # The portal's art. 36-bis asseverazione is one radio group (the library's discrepancies).
               ("pdc-sanatoria-fittizio", "answers-parziale.json"): "Permesso in sanatoria dell'art. 36-bis",
               # The Comune gives no attestation of the exclusion (its landscape directive, § 3.2).
               ("parere-esonero-fittizio", "answers-p6.json"): "A Napoli il Comune non rilascia",
               # The portal requires the CILA's firm, "si riserva" or not (a run stopped on it, 2026-11-01).
               ("cila-fittizia", "answers-impresa-dopo.json"): "La CILA indica la sua impresa esecutrice",
               # No change-of-use line states a whole building to another category (cambio-uso-regionale).
               ("pdc-sanatoria-fittizio", "answers-cambio-intero.json"): "Il modulo non ha una voce per questo cambio d'uso"}
    for name in names:
        for f in sorted((REHEARSALS / name).glob("answers*.json")):
            r = sue(name, f.name)
            if (name, f.name) in refused:
                assert r["unsupported"][0].startswith(refused[name, f.name]), r
            else:
                assert r["ready"], (name, f.name, r)


def sue_another_pratica():
    """Each building recipe refuses a case the table gives to another pratica, or one that
    needs (or doesn't need) the landscape authorization it files with it."""
    other = "Questo caso è un'altra pratica: "
    cila, scia = N("napoli/comune/cila-lavori-edilizi"), N("napoli/comune/scia-edilizia")
    later = "answers-proprietario.json"  # works not started yet: no sanatoria
    semplificata = N("napoli/comune/autorizzazione-paesaggistica-semplificata")
    ordinaria = N("napoli/comune/autorizzazione-paesaggistica-ordinaria")
    assert sue("cila-fittizia", later, fatti=["strutture"], sismica="deposito")["unsupported"][0].startswith(other + scia)
    assert sue("cila-fittizia", later, cambio_uso="stessa_categoria", fatti=["uso_ammesso_prg"])["unsupported"][0].startswith(
        other + scia)
    assert sue("cila-fittizia", later, paesaggio="semplificata")["unsupported"] == [
        f"Questo caso chiede anche {semplificata}, che questa pratica non presenta."]
    assert sue("cila-paesaggistica-fittizia", paesaggio="no")["unsupported"] == [
        f"Questa pratica presenta anche {semplificata}, che a questo caso non serve."]
    # The SCIA's P6 job before it touched the facades: internal works, a CILA's.
    assert sue("scia-fittizia", fatti=[])["unsupported"][0].startswith(other + cila)
    assert sue("scia-fittizia", paesaggio="semplificata")["unsupported"] == [
        f"Questo caso chiede anche {semplificata}, che questa pratica non presenta."]
    assert set(sue("scia-paesaggistica-semplificata-fittizia", paesaggio="ordinaria")["unsupported"]) == {
        f"Questo caso chiede anche {ordinaria}, che questa pratica non presenta.",
        f"Questa pratica presenta anche {semplificata}, che a questo caso non serve."}
    assert sue("scia-paesaggistica-ordinaria-fittizia", intervento="ristrutturazione_pesante")["unsupported"][0].startswith(
        other + N("napoli/comune/scia-alternativa-pdc"))
    assert sue("pdc-fittizio", intervento="manutenzione_straordinaria", fatti=[], strutture="false",
               cambio_uso="no")["unsupported"][0].startswith(other + cila)
    assert sue("scia-alternativa-fittizia", intervento="nuova_costruzione", fatti=[])["unsupported"][0].startswith(
        other + N("napoli/comune/permesso-di-costruire"))
    assert sue("paesaggistica-semplificata-fittizia", intervento="manutenzione_straordinaria", fatti=[])["unsupported"][0].startswith(
        other + cila)
    assert sue("paesaggistica-ordinaria-fittizia", paesaggio="semplificata")["unsupported"][0].startswith(other + semplificata)
    # Works that need no title, work already done, and a Naples rule (DGC 454/2014).
    assert sue("paesaggistica-semplificata-fittizia", paesaggio="no")["unsupported"][0].startswith("Per questo caso non serve alcuna pratica: ")
    # Works already done: the SCIA in sanatoria (facades, structures, ristrutturazione), its own
    # pratica; a permesso's goes to the permesso in sanatoria.
    assert sue("scia-fittizia", fatti=["prospetti", "sanatoria"])["unsupported"][0].startswith(
        other + N("napoli/comune/scia-in-sanatoria"))
    assert sue("scia-sanatoria-fittizia", fatti=[])["unsupported"][0].startswith(other + cila)  # the late CILA
    assert sue("scia-fittizia", "answers-strutture.json", fatti=["sanatoria", "uso_ammesso_prg"], sismica="autorizzazione")["unsupported"][0].startswith(
        other + N("napoli/comune/scia-in-sanatoria"))
    # In a protected area the art. 36-bis sanatoria carries the landscape compatibility (c. 4),
    # new volumes too; the SCIA of works still under way doesn't.
    assert sue("scia-sanatoria-fittizia", paesaggio="semplificata", fatti=["prospetti", "paesaggio_eseguiti", "paesaggio_volumi"])["ready"]
    assert any("36-bis c. 4" in u for u in sue("scia-sanatoria-fittizia", paesaggio="ordinaria", fatti=["prospetti", "paesaggio_eseguiti"],
                                                sanatoria_caso="in corso")["unsupported"])
    assert sue("scia-sanatoria-fittizia", intervento="ristrutturazione", fatti=[])["ready"]
    assert "accertamento di compatibilità" in sue("cila-paesaggistica-fittizia", fatti=["paesaggio_eseguiti"])["unsupported"][0].lower()
    # Works with no building title, already done in a protected area: the accertamento (art. 167
    # c. 4-5 D.Lgs. 42/2004); not with new surfaces or volumes.
    accertamento = N("napoli/comune/accertamento-compatibilita-paesaggistica")
    assert sue("paesaggistica-ordinaria-fittizia", fatti=["paesaggio_eseguiti"])["unsupported"][0].startswith(other + accertamento)
    assert sue("accertamento-paesaggistico-fittizio", fatti=[])["unsupported"][0].startswith(other + ordinaria)
    assert "167 c. 4" in sue("accertamento-paesaggistico-fittizio", fatti=["paesaggio_eseguiti", "paesaggio_volumi"])["unsupported"][0]
    # Works that needed the permesso, already done: the permesso in sanatoria.
    pdcs = N("napoli/comune/permesso-in-sanatoria")
    assert sue("pdc-fittizio", intervento="nuova_costruzione", strutture="false", fatti=["sanatoria"])["unsupported"][0].startswith(other + pdcs)
    assert sue("pdc-sanatoria-fittizio", intervento="variante_essenziale_pdc")["ready"]
    # On structures, begun without the seismic filing: the autorizzazione at the Genio Civile,
    # filed apart, never the deposito (art. 4 c. 1 e L.R. 9/1983); the SCIA's the same.
    genio = "Da presentare a parte, al suo ufficio: " + N("napoli/genio-civile/deposito-autorizzazione-sismica")
    for name in ("pdc-sanatoria-fittizio", "scia-sanatoria-fittizia"):
        assert "L.R. 9/1983" in sue(name, "answers-strutture.json", sismica="deposito")["unsupported"][0]
        assert genio in sue(name, "answers-strutture.json")["yours"]
    assert genio in sue("scia-sanatoria-fittizia", "answers-ristrutturazione-strutture.json")["yours"]
    # Under art. 36-bis c. 1 the case's defect still refuses it, structures or not.
    assert sue("scia-sanatoria-fittizia", "answers-strutture.json", sanatoria_caso="conformita urbanistica")["defects"]
    # The portal's permesso wants an energy incentive claimed even with no energy works.
    assert "incentivo energetico" in sue("pdc-sanatoria-fittizio", incentivo_energetico="nessuno")["unsupported"][0]
    assert "incentivo energetico" in sue("pdc-fittizio", incentivo_energetico="nessuno")["unsupported"][0]
    # The parere di esonero: refused in Napoli; works needing an authorization are that pratica,
    # and a property under no protection needs nothing.
    esonero = sue("parere-esonero-fittizio")["unsupported"]
    assert "D.D. 1072I/2024/154" in esonero[0], esonero
    assert sue("parere-esonero-fittizio", paesaggio="semplificata")["unsupported"][0].startswith(other + semplificata)
    assert sue("parere-esonero-fittizio", paesaggio="no")["unsupported"][0].startswith("Per questo caso non serve alcuna pratica: ")
    # The other recipes never ask for it: a CILA in a protected area with works of Allegato A.
    assert sue("cila-fittizia", later, paesaggio="senza_autorizzazione")["ready"]
    assert sue("scia-fittizia", "answers-variante-pdc.json", fatti=["demolizione_zona_a"])["unsupported"][0].startswith(
        other + N("napoli/comune/permesso-di-costruire"))
    assert "DGC 454/2014" in sue("scia-alternativa-fittizia", fatti=["demolizione_zona_a"])["unsupported"][0]
    # Changes of use under Campania's laws (circolare regionale CI/2025/3).
    unit = {"fatti": ["uso_ammesso_prg"]}
    assert sue("scia-fittizia", "answers-cambio-unita-senza-tra.json", intervento="nessuna_opera")["unsupported"][0].startswith(
        "Per questo caso non serve alcuna pratica: ")  # art. 2 c. 5 L.R. 19/2001
    assert sue("scia-fittizia", cambio_uso="non_rilevante", fatti=["prospetti", "uso_ammesso_prg"])["ready"]  # the facades: a SCIA
    assert sue("scia-fittizia", cambio_uso="intero_immobile", **unit)["unsupported"][0].startswith(
        other + N("napoli/comune/scia-alternativa-pdc"))
    assert sue("scia-alternativa-fittizia", cambio_uso="intero_tra_categorie", fatti=["uso_ammesso_prg", "cambio_uso_sagoma"])[
        "unsupported"][0].startswith(other + N("napoli/comune/permesso-di-costruire"))  # art. 2 c. 6-7 L.R. 19/2001
    assert sue("scia-fittizia", cambio_uso="zona_agricola", **unit)["unsupported"][0].startswith(
        other + N("napoli/comune/permesso-di-costruire"))
    assert "art. 27 c. 2" in sue("scia-fittizia", cambio_uso="stessa_categoria", fatti=["prospetti"])["unsupported"][0]
    # Temporary works: the CIL, alone (art. 6 c. 1 e-bis); not on a bene culturale, not afterwards.
    cil = N("napoli/comune/cil-opere-temporanee")
    assert sue("cila-fittizia", later, intervento="opere_temporanee", fatti=[])["unsupported"][0].startswith(other + cil)
    assert sue("cil-fittizia", intervento="manutenzione_straordinaria", fatti=[], cambio_uso="no")["unsupported"][0].startswith(
        other + cila)
    assert sue("cil-fittizia", paesaggio="semplificata")["unsupported"] == [
        f"Questo caso chiede anche {semplificata}, che questa pratica non presenta."]
    # On a bene culturale the CIL and the CILA go once the Soprintendenza has authorized the works,
    # apart and first: Napoli's SUE has no procedure to ask for it with them (art. 21 c. 4).
    sop = "Da presentare a parte, al suo ufficio: " + N("napoli/soprintendenza/autorizzazione-beni-culturali")
    assert "sabap-na@pec.cultura.gov.it" in sue("cil-fittizia", fatti=["bene_culturale"], soprintendenza_autorizzata="false")["unsupported"][0]
    for name in ("cil-fittizia", "cila-fittizia"):
        r = sue(name, "answers-bene-culturale.json")
        assert r["ready"] and sop in r["yours"], r
    # Works already under way on a bene culturale: no authorization after the fact (art. 169).
    assert "art. 169" in sue("cila-fittizia", "answers-bene-culturale.json", cila_stato="in corso")["unsupported"][0]
    assert "sanatoria" in sue("cil-fittizia", fatti=["sanatoria"])["unsupported"][0]
    # Naples: an ordinary home turned B&B or short let in the centro storico's tavola 7a area
    # (D.C.C. 129/2026), whose 70% threshold has no verified checking mechanism yet.
    a2 = sue("scia-fittizia", "answers-cambio-unita-senza-stessa.json", fatti=["uso_ammesso_prg", "verso_a2_tavola_7a"])
    assert len(a2["unsupported"]) == 1 and "tavola 7a" in a2["unsupported"][0] and "70%" in a2["unsupported"][0], a2
    # A ground-floor unit (art. 23-ter c. 1-quater) or one outside zones A, B and C: Campania's
    # SCIA alternativa (art. 2 c. 6 L.R. 13/2022), as a whole building's change (2026-11-03).
    for c in ("piano_terra", "altro"):
        assert sue("scia-fittizia", cambio_uso=c, **unit)["unsupported"][0].startswith(
            other + N("napoli/comune/scia-alternativa-pdc")), c


def sue_asks_and_apart():
    # What the works are is asked alone first: the other facts depend on it.
    r = sue("cila-fittizia", intervento=None, fatti=None, paesaggio=None, cambio_uso=None)
    assert [q["key"] for q in r["questions"]] == ["intervento"], r["questions"]
    # Then, in one message, the facts the rules for those works still wait on. The CILA's works
    # are under way, a sanatoria: the seismic filing is never asked, it can only be the
    # autorizzazione (art. 4 c. 1 e L.R. 9/1983).
    # A listed building's Soprintendenza authorization (#182) is asked with them, each marked as
    # hanging on the checklist's bene_culturale.
    r = sue("cila-fittizia", fatti=None, paesaggio=None, cambio_uso=None)
    qs = {q["key"]: q for q in r["questions"]}
    assert list(qs) == ["soprintendenza_autorizzata", "fatti", "cambio_uso", "paesaggio", "soprintendenza_autorizzazione"], list(qs)
    assert all("bene_culturale" in qs[k]["only_if"] for k in ("soprintendenza_autorizzata", "soprintendenza_autorizzazione"))
    assert [i["key"] for i in qs["fatti"]["items"]] == ["strutture", "prospetti", "uso_ammesso_prg", "verso_a2_tavola_7a",
                                                        "paesaggio_eseguiti", "bene_culturale"], qs["fatti"]
    assert "permesso_per_scelta" not in str(r["questions"])  # the recipe's: a CILA is no choice
    # The seismic filing is the person's, at the Genio Civile: in their steps, never a refusal.
    r = sue("scia-fittizia", "answers-strutture.json")
    assert r["ready"] and r["yours"][-1] == ("Da presentare a parte, al suo ufficio: "
                                             + run.procedure_name("napoli/genio-civile/deposito-autorizzazione-sismica")), r["yours"]
    assert not [y for y in sue("scia-fittizia")["yours"] if y.startswith("Da presentare a parte")]


def sue_proposals():
    """The forms' own boxes (what the SCIA, permesso or SCIA alternativa files) are proposed
    from the table's answers, for the person to confirm: never asked again, never guessed."""
    form = ["scia_tipo", "scia_cambio_uso", "cambio_uso_tipo", "pdc_tipo", "scia_alt_tipo"]
    drop = {k: None for k in form}
    proposed = lambda r: {p["key"]: p["proposal"] for p in r["proposals"] if p["key"] in form}
    asked = lambda r: [q["key"] for q in r["questions"]]
    r = sue("scia-fittizia", **drop)
    assert proposed(r) == {"scia_tipo": "manutenzione straordinaria", "scia_cambio_uso": "no"}, proposed(r)
    # While the table's facts are still asked, the box waits for them instead of being asked cold.
    r = sue("scia-fittizia", intervento=None, **drop)
    assert "intervento" in asked(r) and "scia_tipo" not in set(asked(r)) | set(proposed(r)), r["questions"]
    assert proposed(r)["scia_cambio_uso"] == "no"  # cambio_uso is answered already
    r = sue("scia-fittizia", "answers-cambio-unita-senza-tra.json", **drop)
    assert proposed(r)["scia_tipo"] == "cambio uso" and proposed(r)["cambio_uso_tipo"] == "unita senza opere tra categorie"
    assert proposed(sue("pdc-fittizio", **drop)) == {"scia_cambio_uso": "no", "pdc_tipo": "ristrutturazione edilizia"}
    # SCIA works asked as a permesso by choice (art. 22 c. 7) ...
    assert proposed(sue("pdc-fittizio", intervento="manutenzione_straordinaria", **drop))["pdc_tipo"] == "facolta scia"
    # ... but not when Campania's law makes it a permesso anyway (zona E): then it's asked.
    r = sue("pdc-fittizio", intervento="manutenzione_straordinaria", cambio_uso="zona_agricola",
            fatti=["uso_ammesso_prg"], **drop)
    assert "pdc_tipo" in asked(r) and "pdc_tipo" not in proposed(r), r
    assert proposed(sue("scia-alternativa-fittizia", **drop))["scia_alt_tipo"] == "ristrutturazione edilizia"
    # A variant to a SCIA, essential or not: the table doesn't say, so the box is asked.
    assert "scia_tipo" in asked(sue("scia-fittizia", "answers-variante-essenziale.json", **drop))


def raises(fn, words, error=run.StepError):
    try:
        fn()
    except error as e:
        assert words in str(e), str(e)
        return
    raise AssertionError(f"no error ({words!r} expected)")


def gen_checks():
    asks, groups = {"insegna": {"type": "text", "question": "Il nome sull'insegna"}}, {}
    raises(lambda: gen.rules_block({"table": "suap-napoli", "facts": {"attivita": "somministrazione"}}, copy.deepcopy(asks), {}),
           "the fact insegna is also asks.insegna, a text", gen.GenError)
    raises(lambda: gen.rules_block({"table": "suap-napoli", "facts": {"tipo": "x"}}, {}, {}), "has no fact tipo", gen.GenError)
    raises(lambda: gen.rules_block({"table": "suap-napoli", "facts": {"evento": "riapertura"}}, {}, {}),
           "isn't a value of the fact evento", gen.GenError)
    raises(lambda: gen.rules_block({"table": "nessuna"}, {}, {}), "no rules table nessuna", gen.GenError)
    asks = {}
    block = gen.rules_block({"table": "suap-napoli", "facts": {"attivita": "somministrazione", "insegna": "{{ask.x}}"},
                             "handles": ["napoli/comune/insegna-esercizio"]}, asks, groups)
    assert block["facts"]["attivita"] == "somministrazione" and block["facts"]["insegna"] == "{{ask.x}}"
    assert block["facts"]["zona"] == "{{ask.zona}}" and block["handles"] == ["napoli/comune/insegna-esercizio"]
    assert asks["alcolici"]["group"] == "fatti" and "fatti" in groups and "insegna" not in asks, asks
    # An ask's options are the table's values written with spaces ("senza autorizzazione"); a
    # combination's `main` is passed on, and the recipe words the checklist.
    asks, groups = {"paesaggio": {"type": "choice", "options": ["no", "senza autorizzazione", "semplificata", "ordinaria"]}}, {}
    block = gen.rules_block({"table": "sue-napoli", "main": "napoli/comune/cila-lavori-edilizi", "question": "Per i lavori?",
                             "facts": {"permesso_per_scelta": "false"}}, asks, groups)
    assert block["facts"]["paesaggio"] == "{{ask.paesaggio}}" and block["main"] == "napoli/comune/cila-lavori-edilizi"
    assert groups["fatti"]["question"] == "Per i lavori?" and "question" not in block, (block, groups)
    raises(lambda: gen.rules_block({"table": "sue-napoli"}, {"paesaggio": {"type": "choice", "options": ["no", "forse"]}}, {}),
           "the fact paesaggio is also asks.paesaggio", gen.GenError)


def tables_are_the_librarys():
    """The runner reads library/rules/ itself: no copy to drift (until 2026-11-11 portal/rules/ was one)."""
    assert not (HERE.parent / "rules").exists(), "portal/rules/ was a copy of the library's: read library/rules/"
    lib = os.environ.get("PRATICHE_NAPOLI_DIR")
    assert rules.TABLES == (Path(lib) / "rules" if lib else HERE.parents[4] / "library" / "rules"), rules.TABLES
    assert sorted(p.name for p in rules.TABLES.glob("*.yaml")) >= ["sue-napoli-adempimenti.yaml", "sue-napoli.yaml", "suap-napoli.yaml"]


def main():
    os.chdir(REHEARSALS.parent)  # the rehearsals' files are paths from the repository
    tests = [every_case_decided_once, decide_answers, ready_as_proven, facts_asked, refused_by_the_table, other_pratiche,
             gen_checks, sue_every_case_decided_once, sue_rehearsals_ready, sue_another_pratica, sue_asks_and_apart, sue_proposals,
             tables_are_the_librarys]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
