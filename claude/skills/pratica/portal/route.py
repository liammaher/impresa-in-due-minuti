#!/usr/bin/env python3
"""From a case's facts to the one steps file that files it, before any pre-flight.

  route.py --table sue-napoli [--answers A.json] [--pratiche DIR]
  route.py --table sue-napoli-adempimenti ...   (a filing on a title held: proroga, fine lavori, ...)
  route.py --table suap-napoli ...              (a business: a shop, a bar or restaurant, ...)

Asks the rules table's own facts (rules/<table>.yaml) in one message, as pre-flight would: the
first fact (what the works are), then every other one some kind of works needs, each one not
every kind needs with `only_for` (the works' answers it is asked for), the yes/no ones as one
checklist (`fatti`). Once the table decides, the case's pratiche (its main one
and those filed with it) name exactly one steps file: the one whose `rules:` has that main
(`main`, else its procedure) and those `handles`. Prints JSON and exits 0 only when `routed`:
- `questions`: what to ask, in pre-flight's format (a checklist's reply is the list of the
  ticked items' keys under `fatti`; the other replies under each `key`);
- `unsupported`: why no steps file files this case (the table refuses it, it needs no
  pratica, or the combination isn't mapped yet);
- `steps`, `answers`: the steps file, and the answers to start its answers file with, so
  pre-flight doesn't ask them again (a fact it reads its own way, as the CILA reads
  `sanatoria` from `cila_stato`, becomes that ask's answer when only one fits, else is in
  `asked_again`, for pre-flight to ask); `apart`: what the person files with another office.

DIR holds the steps files: rehearsals/ (each folder's portal-steps.generated.yaml, else
portal-steps.yaml) or the plugin's pratiche/ (<name>.json). The default is whichever is
next to this skill. In the repo the generated ones are gen.py's build outputs, never committed:
a missing one (a fresh clone, a pull) is generated first (gen.ensure). Two steps files for one
combination is an error, unless the facts their recipes fix (`rules.facts` given as values, not
asks) tell their cases apart, as the SUAP's `evento` does: the index is read from them every
time, so a new recipe is routed once its steps file is generated.
"""

import argparse
import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import rules  # noqa: E402
import run  # noqa: E402  (Values, ruled, refs_in: a steps file's own reading of its facts)

CHECKLIST = "Quali di queste cose valgono per i lavori? Spunta quelle vere, anche nessuna."
GROUP = "fatti"


# The plugin's coverage.json (beside this folder): every pratica's status. In the repo there is none.
COVERAGE = HERE.parent / "coverage.json"
NOT_AVAILABLE = {"mapped": "è in arrivo: non è ancora stata provata sul portale, quindi non la compilo",
                 "coming": "è in arrivo: non è ancora stata provata sul portale, quindi non la compilo",
                 "paused": "è sospesa: il portale è cambiato dall'ultima prova, quindi non la compilo"}


def not_available(name):
    """Why a pratica that is routed to still isn't prepared: the plugin's coverage.json says its status
    isn't `available` (never filled on the real portal, or the portal changed). None when it is, or
    where there is no coverage.json (the repo): the skill's own rule, held in code too, so a mapped
    pratica is never compiled because a rules table happens to route to it."""
    try:
        entries = json.loads(COVERAGE.read_text())["pratiche"]
    except (OSError, ValueError, KeyError):
        return None
    status = next((e["status"] for e in entries if e.get("name") == name), None)
    return NOT_AVAILABLE.get(status)


def default_dir():
    repo = HERE.parents[3] / "rehearsals"
    return repo if repo.is_dir() else HERE.parent / "pratiche"


def steps_files(root):
    """(name, path) of each steps file under root, as bench/rerun.py and plugin/build.py pick them."""
    if (root / "steps.lock").is_file():  # the repo's rehearsals: their steps files are built
        import gen  # noqa: E402  (beside this file in the repo; the plugin has no rehearsals)
        gen.ensure(root=root)
    for p in sorted(root.iterdir()):
        if p.is_dir():
            for n in ("portal-steps.generated.yaml", "portal-steps.yaml"):
                if (p / n).is_file():
                    yield p.name, p / n
                    break
        elif p.suffix == ".json" and p.stem != "catalog":
            yield p.stem, p


def key(main, also):
    return main, tuple(sorted(also))


def fixed_facts(t, steps):
    """The facts a steps file's recipe fixes (a value, not an ask): a case is this file's only
    if it agrees. The SUAP files one procedure at several events (the restaurant's SCIA opens,
    moves, enlarges: `evento`), so its pratiche share their procedures and differ only here."""
    out = {}
    for name, v in ((steps.get("rules") or {}).get("facts") or {}).items():
        if name in t["facts"] and not (isinstance(v, str) and "{{" in v):
            fv = rules.fact_value(t["facts"][name], v)
            if fv is not None:
                out[name] = fv
    return out


def clash(a, b):
    """Whether two indexed steps files could both be one case's: the same wizard choices, and
    no fact both recipes fix differs."""
    return run.wizard_labels(a[2]) == run.wizard_labels(b[2]) and all(a[3][f] == b[3][f] for f in a[3].keys() & b[3].keys()) \
        and via_of(a[2]) == via_of(b[2])


def entries(idx):
    """Every (name, path, steps) indexed."""
    return [e[:3] for es in idx.values() for e in es]


def via_of(steps):
    """Who presents, when the recipe says (`rules.via`): "procura" is the same pratica filed by a
    tecnico for the client, with the portal's procuratore section. It isn't a fact of any rules
    table (it changes no pratica), so the case says it apart (`via` in the answers)."""
    return (steps.get("rules") or {}).get("via")


def find(idx, d, facts, via=None):
    """The (name, path, steps) that files the pratiche of this decision (`rules.decide`'s) for
    this case, or None: its main pratica at the sector and operation the table names, with
    those it adds, whose recipe fixes each choice or number (`evento`) as the case has it; a
    fact the case left unknown doesn't rule one out. The yes/no facts it fixes only choose
    between several: the permesso in sanatoria fixes `permesso_per_scelta`, which the table
    doesn't ask there and a checklist leaves unticked, and run.ruled judges the case after."""
    main = d["main"]["procedure"]
    agree = lambda e, yes_no: all(facts.get(f) is None or facts[f] == v for f, v in e[3].items()
                                  if isinstance(v, bool) == yes_no)
    hits = [e for e in idx.get(key(main, [a["procedure"] for a in d["also"]]), [])
            if run.at_portal(e[2], d["main"]) and agree(e, False) and via_of(e[2]) == via]
    if len(hits) > 1:
        hits = [e for e in hits if agree(e, True)]
    if len(hits) > 1:
        raise run.StepError(f"{' and '.join(e[0] for e in hits)} both fit this case of {main}: "
                            "their recipes' fixed facts must tell them apart")
    return hits[0][:3] if hits else None


def cases(table):
    """Every case the table decides, as the facts it asked on the way (each fact as it asks
    it, the first one first): [(facts, decision)]."""
    t, out = rules.table(table), []

    def values(name):
        f = t["facts"][name]
        if f["type"] == "yes_no":
            return [True, False]
        if f["type"] == "number":
            # One value on each side of every threshold a rule reads (the SUAP's 250 m² of sales area).
            cuts = sorted({float(c[k]) for r in t["rules"] for c in [r["when"].get(name)] if isinstance(c, dict)
                           for k in ("over", "upto") if k in c})
            return sorted({x for c in cuts for x in (c, c + 1)}) or [0.0]
        return list(f["values"])

    def walk(facts):
        d = rules.decide(t, facts)
        if d["ask"]:
            for v in values(d["ask"][0]):
                walk({**facts, d["ask"][0]: v})
        else:
            out.append((facts, d))
    walk({})
    return out


def coverage(table, root):
    """What the table's cases come to: how many reach a steps file under root (`routed`), how
    many it refuses or needs no pratica for (`refused`), and the combinations of pratiche no
    steps file files yet, with their cases, most first (`unmapped`): the mapping still to do.
    A combination is its main pratica and those filed with it; scoreboard.py prints this."""
    idx, routed, refused, unmapped = index(table, root), 0, 0, {}
    for facts, d in cases(table):
        if d["refused"] or d["none"]:
            refused += 1
            continue
        if find(idx, d, facts):
            routed += 1
        else:
            k = key(d["main"]["procedure"], [a["procedure"] for a in d["also"]])
            unmapped[k] = unmapped.get(k, 0) + 1
    return {"cases": routed + refused + sum(unmapped.values()), "routed": routed, "refused": refused,
            "unmapped": sorted(unmapped.items(), key=lambda kv: (-kv[1], kv[0])),
            "combinations": sorted({k for k in idx if k[1]})}


_indexes = {}


def index(table, root):
    """{(main, also): [(name, path, steps, fixed facts)]} for the steps files that read this
    rules table (`find` picks a case's)."""
    if (table, root) not in _indexes:
        _indexes[table, root] = _index(table, root)
    return _indexes[table, root]


def _index(table, root):
    t, out = rules.table(table), {}
    for name, path in steps_files(root):
        steps = rules.load(path)
        r = (steps or {}).get("rules") or {}
        if r.get("table") != table:
            continue
        k, fixed = key(r.get("main", steps["procedure"]), r.get("handles", [])), fixed_facts(t, steps)
        other = next((e for e in out.get(k, []) if clash(e, (name, path, steps, fixed))), None)
        if other:
            raise run.StepError(f"{other[0]} and {name} both file {k[0]} with {list(k[1]) or 'nothing else'}: "
                                "one steps file per combination (or recipes whose fixed facts differ)")
        out.setdefault(k, []).append((name, path, steps, fixed))
    return out


def read_facts(t, answers):
    """The facts answered, and why an answer doesn't fit. A yes/no not answered on its own is
    ticked or not in answers["fatti"]: ticked is yes, and unticked is no only for an item the
    checklist could have shown, one the table still needs once the other answers are in (it
    needs no more as answers come: the checklist showed these and maybe others, never fewer),
    and not one shown only under an item left unticked (`only_if`: never answered). Another
    unticked item stays unknown, for the steps file to ask if it reads it. If the first
    answer changes, the checklist is asked again (SKILL.md): it showed another case's items."""
    facts, errors = {}, {}
    for name, fact in t["facts"].items():
        v = answers.get(name)
        if v is None:
            continue
        fv = rules.fact_value(fact, v) if isinstance(v, (str, bool, int, float)) else None
        if fv is None:
            errors[name] = ("answer with one of: " + ", ".join(fact["values"])) if fact["type"] == "choice" \
                else f"answer with a {'yes or no' if fact['type'] == 'yes_no' else fact['type']}"
        else:
            facts[name] = fv
    items = {n for n, f in t["facts"].items() if f["type"] == "yes_no"}
    ticked = answers.get(GROUP)
    if ticked is not None and (not isinstance(ticked, list) or not all(isinstance(x, str) for x in ticked)
                               or set(ticked) - items):
        errors[GROUP] = "answer with a list of the keys of the items that apply ([] for none)"
        ticked = None
    # The checklist comes after the first fact: before it, nothing was shown.
    if isinstance(ticked, list) and next(iter(t["facts"])) in facts:
        before = dict(facts)
        could = set(rules.decide(t, before)["ask"])
        for name in sorted(items - set(facts)):
            if name in ticked:
                facts[name] = True
                errors.pop(name, None)  # its own answer was wrong; the tick is the answer
            elif name in could and name not in errors and all(g in ticked for g in hangs(t, before, name, could)):
                facts[name] = False
    return facts, errors


def hangs(t, facts, name, ask):
    """The checklist items a fact matters only under: every rule still live that reads it
    wants them ticked (the seismic filing, once the works touch the structures)."""
    need = None
    for rule in t["rules"]:
        w = rule["when"]
        if name not in w or any(rules._holds(c, facts.get(g)) is False for g, c in w.items()):
            continue
        ticked = {g for g, c in w.items() if c is True and g != name and facts.get(g) is None}
        need = ticked if need is None else need & ticked
    return sorted(g for g in need or () if g in ask and t["facts"][g]["type"] == "yes_no")


def works_and_facts(t, facts, first):
    """The works' own question and every fact some kind of works then needs, for one message:
    {fact: the kinds that need it} for the facts not every kind needs."""
    needs, open_ = {}, 0
    for kind in t["facts"][first]["values"]:
        d = rules.decide(t, facts | {first: kind})
        if not (d["refused"] or d["none"] or d["conflict"]):  # a kind decided at once needs nothing more
            open_ += 1
            for f in d["ask"]:
                needs.setdefault(f, []).append(kind)
    return {first} | set(needs), {f: k for f, k in needs.items() if len(k) < open_}


def questions(t, ask, errors, checklist=CHECKLIST, facts=None, works=None):
    out, items = [], []
    for name in ask:
        fact = t["facts"][name]
        extra = {"how": fact["how"]} if "how" in fact else {}
        if works and name in works:
            # Asked only for those kinds of works (the first fact's answers: its labels name them).
            first = next(iter(t["facts"]))
            extra["only_for"] = {first: works[name]}
        under = hangs(t, facts, name, ask) if facts is not None else []
        if under:
            extra["only_if"] = under
        if fact["type"] == "yes_no":
            items.append({"key": name, "item": fact["question"]} | extra
                         | ({"error": errors[name]} if name in errors else {}))
            continue
        q = {"key": name, "type": fact["type"], "question": fact["question"]} | extra
        if fact["type"] == "choice":
            q |= {"options": list(fact["values"]), "labels": dict(fact["values"])}
        out.append(q | ({"error": errors[name]} if name in errors else {}))
    if items:
        out.append({"key": GROUP, "type": "checklist", "question": checklist, "items": items}
                   | ({"error": errors[GROUP]} if GROUP in errors else {}))
    return out


def for_works(t, q):
    """A question asked only for some kinds of works (`only_for`), saying so in the fewer words:
    the kinds it is for, or those it isn't."""
    if "only_for" not in q:
        return q
    first = next(iter(t["facts"]))
    kinds = list(t["facts"][first]["values"])
    for_ = q["only_for"][first]
    name = lambda ks: "; ".join(run.said({"type": "choice", "labels": dict(t["facts"][first]["values"])}, k) for k in ks)
    rest = [k for k in kinds if k not in for_]
    note = f"solo per: {name(for_)}" if len(for_) <= len(rest) else f"non serve per: {name(rest)}"
    return {**q, "question": q["question"] + f" ({note})"}


def carry(t, steps, facts, answers):
    """The answers file for this steps file: each fact under the ask it reads it from, in
    that ask's own options; a fact read through another ask (with a filter) becomes that
    ask's answer when only one of its options gives the fact, else it is asked again."""
    asks, out, again = steps.get("asks", {}), {}, []
    for name, tmpl in steps["rules"]["facts"].items():
        if name not in facts or not isinstance(tmpl, str) or "{{" not in tmpl:
            continue  # unknown, or fixed by the recipe (ruled() checks it agrees)
        refs = [r[4:] for r, _ in run.refs_in(tmpl) if r.startswith("ask.")]
        fact, want = t["facts"][name], facts[name]
        if len(refs) != 1 or refs[0] not in asks:
            again.append({"fact": name, "reads": refs})
            continue
        k, a = refs[0], asks[refs[0]]
        gives = lambda o: rules.fact_value(fact, run.Values({**out, k: o}, fields={}, asks=asks).render(tmpl) or "")
        given = answers.get(k) if k not in t["facts"] else None
        if given is not None:
            # Answered in its own words already: kept if it fits its ask and says the same,
            # else asked again, never replaced by what the facts say.
            if run.check_answer(a, given) is None and gives(given) == want:
                out[k] = given
            else:
                again.append({"fact": name, "ask": k, "given": given,
                              "why": f"doesn't fit, or says otherwise than the answer to {name}"})
            continue
        if a.get("type") not in ("choice", "yes_no"):
            if tmpl.strip() == "{{ask.%s}}" % name:
                out[k] = answers.get(name, want)
            else:
                again.append({"fact": name, "ask": k, "fits": []})
            continue
        fits = [o for o in a.get("options") or [True, False] if gives(o) == want]
        if len(fits) == 1:
            out[k] = fits[0]
        else:
            again.append({"fact": name, "ask": k, "fits": fits})
    return out, again


def route(table, answers, root=None):
    t = rules.table(table)
    root = root or default_dir()
    idx = index(table, root)
    report = {"routed": False, "questions": [], "unsupported": [], "steps": None, "pratica": None, "main": None,
              "also": [], "answers": {}, "asked_again": [], "apart": []}
    if not isinstance(answers, dict):
        raise run.StepError("answers: a JSON object, each fact's answer under its key")
    facts, errors = read_facts(t, answers)
    via = answers.get("via")
    if via not in (None, "procura"):
        raise run.StepError('via: "procura" when a tecnico files for the client with a procura, else leave it out')
    d = rules.decide(t, facts)
    if d["conflict"]:
        raise run.StepError(f"rules table {table}: rules {', '.join(d['conflict'])} disagree (validate the library)")
    if d["refused"]:  # as pre-flight: a refusal ends the case, whatever is still unknown
        report["unsupported"] = [x["reason"] for x in d["refused"]]
        report["message"] = run.refusal_text(report)
        return report
    # A wrong answer is asked again only if the case needs it: one it doesn't is dropped,
    # and a checklist answered wrong leaves its items unknown, so they are asked again whole.
    first = next(iter(t["facts"]))
    if d["ask"]:
        ask, works = set(d["ask"]), {}
        if d["ask"][0] == first:
            # Which others matter depends on the works: they are asked with it, in the same
            # message, each fact some kinds of works don't need saying which do (`only_for`).
            ask, works = works_and_facts(t, facts, first)

        # The recipes word the checklist (their rules.question, gen.py's groups.fatti).
        group = next((s["groups"][GROUP]["question"] for _, _, s in entries(idx) if GROUP in s.get("groups", {})),
                     CHECKLIST)
        report["questions"] = questions(t, [f for f in t["facts"] if f in ask], errors, group, facts, works)
        # In pre-flight's format, for Claude to send as it is (with what it read in the documents).
        report["message"] = run.message({"questions": [for_works(t, q) for q in report["questions"]],
                                         "proposals": [], "missing": []}, {q["key"]: q for q in report["questions"]})
        return report
    if d["none"]:
        report["unsupported"] = [f"Per questo caso non serve alcuna pratica: {d['none']['reason']}"]
        report["message"] = run.refusal_text(report)
        return report
    m = d["main"]
    if not m:
        report["unsupported"] = ["Le regole del SUE non indicano alcuna pratica per questo caso."]
        report["message"] = run.refusal_text(report)
        return report
    also = [a["procedure"] for a in d["also"]]
    report["main"], report["also"] = m["procedure"], also
    report["apart"] = [f"Da presentare a parte, al suo ufficio: {run.procedure_name(a['procedure'])}" for a in d["apart"]]
    hit = find(idx, d, facts, via)
    if not hit:
        report["unsupported"] = [f"Non ancora prevista{' con procura' if via else ''}: {run.procedure_name(m['procedure'])}"
                                 + (f", insieme a {', '.join(map(run.procedure_name, also))}" if also else "") + "."]
        report["message"] = run.refusal_text(report)
        return report
    name, path, steps = hit
    why = not_available(name)
    if why:
        report["unsupported"] = [f"Questa pratica ({run.procedure_name(m['procedure'])}) {why}."]
        report["message"] = run.refusal_text(report)
        return report
    carried, again = carry(t, steps, facts, answers)
    # The steps file's own reading of the case must agree: its fixed facts, its wizard.
    out, _ = run.ruled(steps, run.Values(carried, fields={}, asks=steps.get("asks", {})))
    if out:
        report["unsupported"] = out
        report["message"] = run.refusal_text(report)
        return report
    # The route in a line or two, for the one message: the pratica and what goes apart.
    # A procedure several steps files share (the SUAP's SCIA opens, moves, enlarges: `evento`) is named by
    # the steps file's own title, which says which: «trasferimento di un bar o ristorante», not «Aprire».
    shared = len([e for e in idx[key(m["procedure"], also)] if via_of(e[2]) == via]) > 1
    what = re.sub(r",? SUAP \w+$", "", steps["title"]) if shared and steps.get("title") else run.procedure_name(m["procedure"])
    report["message"] = "\n".join([f"La pratica: {what}"
                                   + (f", insieme a {', '.join(map(run.procedure_name, also))}" if also else "") + "."]
                                  + report["apart"])
    report.update(routed=True, pratica=name, steps=str(path), answers=carried, asked_again=again)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--table", required=True)
    ap.add_argument("--answers", type=Path, help="the facts' answers as JSON (none yet: the first question)")
    ap.add_argument("--pratiche", type=Path, help="where the steps files are (default: rehearsals/ or pratiche/)")
    a = ap.parse_args()
    try:
        answers = json.loads(a.answers.read_text()) if a.answers else {}
        report = route(a.table, answers, a.pratiche)
    except (run.StepError, ValueError, OSError) as e:  # bad JSON is a ValueError; no file, an OSError
        print(f"stopped: {e}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["routed"] else 3


if __name__ == "__main__":
    sys.exit(main())
