#!/usr/bin/env python3
"""A new rehearsal case: one of a rehearsal's answers files changed by a few answers, through
pre-flight until it is ready, then written as answers-NAME.json beside the others.

    ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/new_case.py \\
        REHEARSAL BASE NAME '{"key": value, ...}' [--drop k1,k2] [--write] [--force]

BASE names answers-BASE.json (p6, tolleranze-autorizzazione...: the base nearest the case, so
fewer questions come back). The overrides' `people` merges into the base's; --drop removes keys
first (a tolerance case's seismic answers, for one with none). The made-up people are the
fixture's (rehearsals/cila-fittizia/fixture-p6.json). It prints pre-flight's questions (`Q`, with
a checklist's other items), missing values (`M`), refusals (`U`) and proposals (`P`); answer them
in the overrides and run it again. --write writes the file only when the case is ready. Run from
the repo's root, as the answers name their files from there. How 32 cases were written this way
(2026-11-04): the mapped boxes no case ticked (schema_branches.py, "Portal-only boxes untaken"),
each one's condition read from a steps file, then a case per realistic set of them; then
schema_branches.py table counts them as "a case, no recorded run" until rerun.py --record.
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import run  # noqa: E402

ROOT = HERE.parents[4]
FIXTURE = ROOT / "rehearsals" / "cila-fittizia" / "fixture-p6.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rehearsal")
    ap.add_argument("base")
    ap.add_argument("name")
    ap.add_argument("overrides", help="JSON: the answers that differ from the base's")
    ap.add_argument("--drop", default="", help="comma-separated keys to remove from the base first")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true", help="--write over an existing file")
    a = ap.parse_args()
    d = ROOT / "rehearsals" / a.rehearsal
    steps = yaml.safe_load((d / "portal-steps.generated.yaml").read_text())
    fields = dict(json.loads(FIXTURE.read_text())["fields"])
    answers = json.loads((d / f"answers-{a.base}.json").read_text())
    for k in filter(None, a.drop.split(",")):
        answers.pop(k, None)
    over = json.loads(a.overrides)
    if "people" in over:
        answers["people"] = {**answers.get("people", {}), **over.pop("people")}
    answers.update(over)
    values = run.Values(dict(answers), fields=fields, asks=steps.get("asks"))
    r = run.preflight(steps, values, made_up=True)
    for q in r["questions"]:
        items = [i["key"] for i in q.get("items", [])]
        print("Q", q["key"], "|", q.get("type"), "|", (q.get("question") or "")[:150], "|", q.get("error", ""),
              "|", items or "")
    for p in r["proposals"]:
        print("P", p.get("key"), "=", p.get("proposal"))
    for m in r["missing"]:
        print("M", m)
    for u in r["unsupported"]:
        print("U", u)
    if not r["ready"]:
        print("not ready")
        return 1
    print("ready:", len(run.plan(run.rehearsal(steps, values), values)), "fields planned")
    if a.write:
        out = d / f"answers-{a.name}.json"
        if out.exists() and not a.force:
            sys.exit(f"{out} exists (--force to replace it)")
        out.write_text(json.dumps(answers, ensure_ascii=False, indent=1) + "\n")
        print("wrote", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
