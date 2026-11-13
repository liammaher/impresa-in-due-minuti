#!/usr/bin/env python3
"""Offline tests of what the portal taught about combined SUAP pratiche (2026-11-13): the sign, the acoustic nulla osta and the
dehors filed with an opening, a move or a take-over.

  ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/test_combos.py

No browser, vault or network. Each test is a thing the portal cost a run (or a crawl) to find; see README, "SUAP combinations".
"""
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import catalogue as cat  # noqa: E402
import derive_combos as dc  # noqa: E402
import gen  # noqa: E402

ROOT = HERE.parents[4]
REHEARSALS = ROOT / "rehearsals"


def recipe(name):
    return yaml.safe_load((REHEARSALS / name / "recipe.yaml").read_text(encoding="utf-8"))


def steps(name):
    return yaml.safe_load((REHEARSALS / name / "portal-steps.generated.yaml").read_text(encoding="utf-8"))


def no_recipe_rests_on_a_ticked_crawl():
    """A crawl taken with an «interventi» option left ticked has its sections in its base. gen.py refuses a recipe on one unless it
    says `crawl_ticked`; the stored crawls that are such are named here, so a new one is noticed."""
    known = {"suap-004-aprire-l-attivita-interventi", "suap-016-aprire-l-attivita-interventi",
             "suap-017-aprire-l-attivita-interventi", "suap-056-aprire-l-attivita-interventi"}
    ticked = {p.stem for p in cat.SECTIONS.glob("*.json") if cat.ticked_interventi(json.loads(p.read_text()).get("screens"))}
    assert ticked == known, f"crawls taken with a tick left: {sorted(ticked ^ known)}"
    for f in REHEARSALS.glob("*/recipe.yaml"):
        r = yaml.safe_load(f.read_text(encoding="utf-8"))
        if r.get("crawl") in ticked:
            assert r.get("crawl_ticked"), f"{f.parent.name} rests on {r['crawl']}, taken with a tick: say why in `crawl_ticked`, or use the plain crawl"
    # import refuses one
    assert cat.ticked_interventi([{"screen": "scelta interventi eventuali", "options": [{"label": "x", "selected": True}]}]) == ["x"]
    assert not cat.ticked_interventi([{"screen": "scelta interventi eventuali", "options": [{"label": "x"}]}])
    assert not cat.ticked_interventi([{"screen": "scelte eventuali", "options": [{"label": "x", "selected": True}]}])  # a scelta's tick is the batch's own


def gen_refuses_a_ticked_crawl():
    r = recipe("alimentari-insegna-fittizio")
    r["crawl"] = "suap-017-aprire-l-attivita-interventi"
    r.pop("crawl_ticked", None)
    try:
        gen.generate(r)
        raise AssertionError("a recipe on a crawl with a leftover tick should be refused")
    except gen.GenError as e:
        assert "ticked" in str(e), e
    r["crawl_ticked"] = "for the test"
    try:
        gen.generate(r)  # allowed past the guard; it may still fail on the crawl's own sections, but not on the tick
    except gen.GenError as e:
        assert "ticked" not in str(e), e


def every_reference_resolves():
    """A section's `same_as` names a crawl that is in the repo and holds it (import names the first crawl with a fingerprint: a crawl deleted
    afterwards, the contaminated dehors ones, left the take-overs' sign sections pointing at nothing: gen.py "isn't in the catalogue")."""
    crawls = {p.stem: json.loads(p.read_text()) for p in cat.SECTIONS.glob("*.json")}
    for name, d in crawls.items():
        for s in d["sections"]:
            ref = s.get("same_as")
            if not ref or "#" not in ref:
                continue
            target, section = ref.split("#", 1)
            if target == name:
                continue
            assert target in crawls, f"{name}: {s['section']} is the same as {ref}, a crawl that is not in the repo"
            assert section in {x["section"] for x in crawls[target]["sections"]}, f"{name}: {ref} holds no such section"


def combinations_are_what_the_probe_took():
    """Every recipe that selects two operations in the wizard (the dehors' area, the sign) is a pair the probe took together."""
    probed = {tuple(p["operations"]) for p in json.loads((cat.CAT / "suap-pairs.json").read_text())["pairs"] if p["accepted"]}
    leaves = {main for main, _ in probed} | {other for _, other in probed}
    two = 0
    for f in REHEARSALS.glob("*/recipe.yaml"):
        r = yaml.safe_load(f.read_text(encoding="utf-8"))
        for st in r.get("wizard") or []:
            tree = st.get("tree") if isinstance(st, dict) and st.get("screen") == "Scelta operazioni" else None
            if tree and len(tree) > 1 and (dc.SIGN_OP in tree or dc.DEHORS_OP in tree):
                two += 1
                assert (tree[0], tree[1]) in probed, f"{f.parent.name}: {tree} is not a pair the wizard probe took together"
    assert two >= 9, two


def every_combination_has_a_filled_run_and_its_rules():
    """Each recipe derive_combos.py builds files the library's SUAP table's case (its `rules:` block says which procedures it files), and
    has a run on the portal that filled. A combination whose run stopped is left out of routing (no rules block) and named in
    catalogue/F839/suap-unrouted.yaml, never routed on a guess."""
    for name, c in dc.COMBOS.items():
        r = recipe(name)
        assert r["rules"]["handles"] == c["handles"], (name, r["rules"]["handles"])
        runs = json.loads((REHEARSALS / name / "runs.json").read_text())
        assert any(x["result"] == "filled" for x in runs["runs"] if "result" in x) if isinstance(runs, dict) and "runs" in runs else \
            any(x.get("result") == "filled" for x in runs), f"{name}: no filled run on the portal"


def one_bollo_when_two_adempimenti_want_it():
    """The dehors' area and the nulla osta each want the bollo declaration: the draft shows one, under the tick's title."""
    for name in ("ristorante-dehors-musica-fittizio", "ristorante-dehors-insegna-musica-fittizio"):
        titles = [s["section"] for s in steps(name)["sections"] if "bollo" in s["section"].lower()]
        assert titles == ["dichiarazione relativa all'imposta di bollo"], (name, titles)
    # without the tick the base's own title stays
    titles = [s["section"] for s in steps("ristorante-dehors-fittizio")["sections"] if "bollo" in s["section"].lower()]
    assert titles == ["Dichiarazione relativa all'assolvimento dell'imposta di bollo"], titles


def the_signs_form_is_the_pages_when_both_ticks_are_ticked():
    """The bar's opening with the sign and the nulla osta, on the opening's `-interventi` crawl, got the other dictionary entry for «Caratteristiche
    del manufatto» and stopped on «num. progressivo» (2026-11-13); the page shows «Tipologia» first, as in every sign recipe that filled."""
    for name in ("ristorante-insegna-fittizio", "ristorante-insegna-musica-fittizio", "trasferimento-ristorante-insegna-musica-fittizio",
                 "ristorante-dehors-insegna-musica-fittizio"):
        sec = next(s for s in steps(name)["sections"] if s["section"] == "Caratteristiche del manufatto da installare")
        assert sec["fields"][0]["label"] == "Tipologia", (name, sec["fields"][0]["label"])
    assert recipe("ristorante-insegna-musica-fittizio")["crawl"] == "suap-060-aprire-l-attivita"


def the_pane_code_keeps_what_it_learned():
    """Text checks of the pane's scripts: a leftover interventi tick is cleared by the wizard, a stale busy flag doesn't hold the next bundle,
    a pair can name its sector, a batch's skips are shown."""
    wiz = (HERE.parent / "wizard.js").read_text()
    assert 'title().includes("scelte eventuali") || title().includes("interventi eventuali")' in wiz
    assert "a.sector || opts.sector" in wiz
    src = (HERE.parent / "catalogue.py").read_text()
    assert "window.__crawlBusy && window.__crawl && (window.__crawl.report() || {}).done === false" in src
    assert "skipped: r.skipped" in src
    assert "--base-only" in src and "--interventi" in src and "--suap" in src


def main():
    for t in (no_recipe_rests_on_a_ticked_crawl, gen_refuses_a_ticked_crawl, every_reference_resolves, combinations_are_what_the_probe_took,
              every_combination_has_a_filled_run_and_its_rules, one_bollo_when_two_adempimenti_want_it, the_signs_form_is_the_pages_when_both_ticks_are_ticked, the_pane_code_keeps_what_it_learned):
        t()
        print("ok ", t.__name__)
    print("done")


if __name__ == "__main__":
    main()
