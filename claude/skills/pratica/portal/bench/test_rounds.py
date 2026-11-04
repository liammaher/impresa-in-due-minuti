#!/usr/bin/env python3
"""One message of questions: every rehearsal's pre-flight is ready after the person answers once.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_rounds.py

For each rehearsal with a recipe and answers-p6.json: the rules table's facts come answered (route.py
asks them, in one message of its own), then pre-flight runs; the person answers what it asks (the
rehearsal's own answers), confirms every proposal, and a proposal given per answer (`cases`) is
resolved from the answers given in the same message. Pre-flight must then be ready: nothing left for
a second message. A case refused on purpose (a Napoli or portal limit) stays refused. No browser,
vault or network.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402
import run  # noqa: E402

ROOT = HERE.parents[4]
REH = ROOT / "rehearsals"
REFUSED = {"parere-esonero-fittizio", "pdc-sanatoria-accertamento-fittizio"}  # test_preflight says why


def resolve(proposal, values):
    """What the person's "ok" gives a proposal: its value, or the one its case for these answers names."""
    if "cases" not in proposal:
        return proposal["proposal"]
    same = lambda k, v: str(values.raw(k)) == str(v) or (
        v in ("true", "false") and run.truthy(str(values.raw(k) or "false")) == (v == "true"))
    for case in proposal["cases"]:
        if all(same(k, v) for k, v in case["if"].items()):
            return case["proposal"]
    return None  # an answer with no proposal: the question itself was asked (`otherwise`)


def main():
    fields = dict(json.loads((REH / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    names = sorted(d.name for d in REH.iterdir() if (d / "recipe.yaml").exists() and (d / "answers-p6.json").exists())
    here, bad, seconds = os.getcwd(), [], 0
    os.chdir(ROOT)  # the answers name their files from the repo's root
    try:
        for name in names:
            steps = gen.generate(gen.load_yaml(REH / name / "recipe.yaml"))
            full = json.loads((REH / name / "answers-p6.json").read_text())
            facts = set((steps.get("rules") or {}).get("facts", {}))
            answers = {k: v for k, v in full.items() if k in ("people", "descrizione", "fatti") or k in facts}
            values = lambda: run.Values(dict(answers), fields=fields, asks=steps.get("asks"))
            r = run.preflight(steps, values(), made_up=True)
            if name in REFUSED:
                if not r["unsupported"]:
                    bad.append(f"{name}: no longer refused")
                continue
            asked = [q["key"] for q in r["questions"]] + [i["key"] for q in r["questions"] for i in q.get("items", [])]
            for k in asked:
                if k in full:
                    answers[k] = full[k]
            corrected = []
            for p in r["proposals"]:
                v = resolve(p, values())
                if p["key"] in full or v is not None:
                    answers[p["key"]] = full.get(p["key"], v)
                    if p["key"] in full and v is not None and str(full[p["key"]]) != str(v):
                        corrected.append(p["key"])
            again = run.preflight(steps, values(), made_up=True)
            if again["ready"]:
                continue
            left = [q["key"] for q in again["questions"]] + [i["key"] for q in again["questions"] for i in q.get("items", [])] \
                + [p["key"] for p in again["proposals"]]
            # Changing a proposal may open what it was holding (`if_changed`, and what that opens in
            # turn): one more message then, never without a change.
            if not corrected:
                bad.append(f"{name}: a second message for {left or again['unsupported'] or again['missing']}"
                           + (f" (corrected {corrected})" if corrected else ""))
                continue
            seconds += 1
            for k in left:
                if k in full:
                    answers[k] = full[k]
            for p in again["proposals"]:
                answers[p["key"]] = full.get(p["key"], resolve(p, values()))
            if not run.preflight(steps, values(), made_up=True)["ready"]:
                bad.append(f"{name}: not ready after the follow-ups of the corrected {corrected}")
    finally:
        os.chdir(here)
    for b in bad:
        print("FAIL ", b)
    print(f"{len(names) - len(bad)}/{len(names)} rehearsals ready after one message"
          f" ({seconds} after one more, each because the rehearsal changed a proposal)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
