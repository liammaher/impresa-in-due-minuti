#!/usr/bin/env python3
"""From a case's facts to the one steps file that files it, before any pre-flight.

  route.py --table sue-napoli [--answers A.json] [--pratiche DIR]

Asks the rules table's own facts (rules/<table>.yaml), as pre-flight would: the first fact
(what the works are) alone, then every other one the case needs in one message, the yes/no
ones as one checklist (`fatti`). Once the table decides, the case's pratiche (its main one
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
next to this skill. Two steps files for one combination is an error: the index is read
from them every time, so a new recipe is routed once its steps file is generated.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import rules  # noqa: E402
import run  # noqa: E402  (Values, ruled, refs_in: a steps file's own reading of its facts)

CHECKLIST = "Quali di queste cose valgono per i lavori? Spunta quelle vere, anche nessuna."
GROUP = "fatti"


def default_dir():
    repo = HERE.parents[3] / "rehearsals"
    return repo if repo.is_dir() else HERE.parent / "pratiche"


def steps_files(root):
    """(name, path) of each steps file under root, as bench/rerun.py and plugin/build.py pick them."""
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


_indexes = {}


def index(table, root):
    """{(main, also): (name, path, steps)} for the steps files that read this rules table."""
    if (table, root) not in _indexes:
        _indexes[table, root] = _index(table, root)
    return _indexes[table, root]


def _index(table, root):
    out = {}
    for name, path in steps_files(root):
        steps = yaml.safe_load(path.read_text())
        r = (steps or {}).get("rules") or {}
        if r.get("table") != table:
            continue
        k = key(r.get("main", steps["procedure"]), r.get("handles", []))
        if k in out:
            raise run.StepError(f"{out[k][0]} and {name} both file {k[0]} with {list(k[1]) or 'nothing else'}: "
                                "one steps file per combination")
        out[k] = (name, path, steps)
    return out


def shown(t, answers):
    """The facts asked so far: the first alone, then those the table needs once it is known."""
    first = next(iter(t["facts"]))
    v = rules.fact_value(t["facts"][first], answers[first]) if answers.get(first) is not None else None
    return {first} | (set(rules.decide(t, {first: v})["ask"]) if v is not None else set())


def read_facts(t, answers):
    """The facts answered, and why an answer doesn't fit. A yes/no asked in the checklist and
    not answered on its own is ticked or not in answers["fatti"]."""
    facts, errors = {}, {}
    ticked = answers.get(GROUP)
    if ticked is not None and (not isinstance(ticked, list) or set(ticked) - set(t["facts"])):
        errors[GROUP] = "answer with a list of the keys of the items that apply ([] for none)"
        ticked = None
    asked = shown(t, answers)
    for name, fact in t["facts"].items():
        v = answers.get(name)
        if v is None and fact["type"] == "yes_no" and isinstance(ticked, list) and name in asked:
            v = name in ticked
        if v is None:
            continue
        fv = rules.fact_value(fact, v)
        if fv is None:
            errors[name] = ("answer with one of: " + ", ".join(fact["values"])) if fact["type"] == "choice" \
                else f"answer with a {'yes or no' if fact['type'] == 'yes_no' else fact['type']}"
        else:
            facts[name] = fv
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


def questions(t, ask, errors, checklist=CHECKLIST, facts=None):
    out, items = [], []
    for name in ask:
        fact = t["facts"][name]
        extra = {"how": fact["how"]} if "how" in fact else {}
        if facts is not None and hangs(t, facts, name, ask):
            extra["only_if"] = hangs(t, facts, name, ask)
        if fact["type"] == "yes_no":
            items.append({"key": name, "item": fact["question"]} | extra)
            continue
        q = {"key": name, "type": fact["type"], "question": fact["question"]} | extra
        if fact["type"] == "choice":
            q |= {"options": list(fact["values"]), "labels": dict(fact["values"])}
        out.append(q | ({"error": errors[name]} if name in errors else {}))
    if items:
        out.append({"key": GROUP, "type": "checklist", "question": checklist, "items": items}
                   | ({"error": errors[GROUP]} if GROUP in errors else {}))
    return out


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
        if k in answers and k not in t["facts"]:
            out[k] = answers[k]  # answered in its own words already
            continue
        if a.get("type") not in ("choice", "yes_no"):
            if tmpl.strip() == "{{ask.%s}}" % name:
                out[k] = answers[name]
            else:
                again.append({"fact": name, "ask": k, "fits": []})
            continue
        options = a.get("options") or [True, False]
        fits = [o for o in options
                if rules.fact_value(fact, run.Values({**out, k: o}, fields={}, asks=asks).render(tmpl) or "") == want]
        if len(fits) == 1:
            out[k] = fits[0]
        else:
            again.append({"fact": name, "ask": k, "fits": fits})
    return out, again


def route(table, answers, root=None):
    t = rules.table(table)
    root = root or default_dir()
    idx = index(table, root)
    report = {"routed": False, "questions": [], "unsupported": [], "steps": None, "pratica": None,
              "answers": {}, "asked_again": [], "apart": []}
    facts, errors = read_facts(t, answers)
    d = rules.decide(t, facts)
    if d["conflict"]:
        raise run.StepError(f"rules table {table}: rules {', '.join(d['conflict'])} disagree (validate the library)")
    if d["refused"]:  # as pre-flight: a refusal ends the case, whatever is still unknown
        report["unsupported"] = [x["reason"] for x in d["refused"]]
        return report
    first = next(iter(t["facts"]))
    if d["ask"] or errors:
        if first in errors or (d["ask"] and d["ask"][0] == first):
            ask = {first}  # which of the others matter depends on it
        else:
            ask = set(d["ask"]) | set(errors) - {GROUP}
            if GROUP in errors:  # a checklist answered wrong is asked again whole
                ask |= {f for f in shown(t, answers) if t["facts"][f]["type"] == "yes_no"}
        # The recipes word the checklist (their rules.question, gen.py's groups.fatti).
        group = next((s["groups"][GROUP]["question"] for _, _, s in idx.values() if GROUP in s.get("groups", {})),
                     CHECKLIST)
        report["questions"] = questions(t, [f for f in t["facts"] if f in ask], errors, group, facts)
        return report
    if d["none"]:
        report["unsupported"] = [f"This case needs no pratica: {d['none']['reason']}"]
        return report
    m = d["main"]
    if not m:
        report["unsupported"] = [f"The rules table {table} names no pratica for this case."]
        return report
    also = [a["procedure"] for a in d["also"]]
    report["main"], report["also"] = m["procedure"], also
    report["apart"] = [f"File apart, with its own office: {a['procedure']} ({a['regime']})" for a in d["apart"]]
    hit = idx.get(key(m["procedure"], also))
    if not hit:
        report["unsupported"] = [f"Not mapped yet: {m['procedure']} ({m['regime']})"
                                 + (f" filed with {', '.join(also)}" if also else "") + "."]
        return report
    name, path, steps = hit
    carried, again = carry(t, steps, facts, answers)
    # The steps file's own reading of the case must agree: its fixed facts, its wizard.
    out, _ = run.ruled(steps, run.Values(carried, fields={}, asks=steps.get("asks", {})))
    if out:
        report["unsupported"] = [f"{name}: {x}" for x in out]
        return report
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
    except (run.StepError, ValueError) as e:
        print(f"stopped: {e}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["routed"] else 3


if __name__ == "__main__":
    sys.exit(main())
