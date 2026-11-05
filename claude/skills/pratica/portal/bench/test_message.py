#!/usr/bin/env python3
"""Pre-flight's `message`, the one the skill sends as it is: for every rehearsal, it holds every
question (one under a proposal only counted), proposal and missing detail, refers only to questions it numbers, and shows no field id
or role code. Also the small cases by hand: a follow-up under its question, one under a proposal,
a proposal per answer.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_message.py
"""
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402
import run  # noqa: E402

ROOT = HERE.parents[4]
REH = ROOT / "rehearsals"
# A field id (bianchi:identity.first_name, residenza.cap) or a role code (c:, cr:) in the text.
LEAK = re.compile(r"\b[a-z][a-z0-9-]*:[a-z_]+\.[a-z_]+\b|(?<![\w/])(?:t|c|cr|o|r|p|f\d?):(?=\w)")


def holds(m, report):
    """What the message lacks or shows that it mustn't."""
    bad = []
    # A question that hangs on a proposal is counted under it ("se la cambia, le farò altre 2
    # domande"), not printed: asked only if the tecnico changes that proposal. So are its own.
    counted = {p["key"] for p in report["proposals"]}
    for q in report["questions"]:
        if q["question"].rstrip("?:. ") not in m:
            if set(q.get("only_if", [])) & counted:
                counted.add(q["key"])
                continue
            bad.append(f"question {q['key']} missing")
        for i in q.get("items", []):
            if i["item"] not in m:
                bad.append(f"item {i['key']} missing")
    for p in report["proposals"]:
        if run.head(p["question"]) not in m:
            bad.append(f"proposal {p['key']} missing")
    for x in report["missing"]:
        line = next((ln for ln in m.splitlines() if ln.startswith(f"– {run.whose_of(x['field'])}:")), "")
        if not x["field"].startswith("*:") and run.missing_label(x["for"]) not in line:
            bad.append(f"missing {x['field']} not asked")
    if "alla ?" in m:
        bad.append("refers to a question it doesn't number")
    leak = LEAK.search(m)
    if leak:
        bad.append(f"shows {leak.group(0)!r}")
    return bad


def by_hand():
    asks = {"impianti": {"type": "yes_no", "question": "Ci sono impianti?"},
            "quali": {"type": "text", "question": "Quali impianti?"},
            "tolleranze": {"type": "yes_no", "question": "Ci sono tolleranze?"},
            "classe": {"type": "choice", "options": ["a", "b"], "question": "La classe"},
            "stato": {"type": "choice", "options": ["in corso", "realizzato"], "question": "I lavori sono iniziati?"},
            "diritti": {"type": "number", "question": "I diritti"}}
    report = {"questions": [{"key": "impianti", "type": "yes_no", "question": "Ci sono impianti?"},
                            {"key": "quali", "type": "text", "question": "Quali impianti?", "only_if": ["impianti"]},
                            {"key": "classe", "type": "choice", "options": ["a", "b"], "question": "La classe",
                             "only_if": ["tolleranze"]},
                            {"key": "stato", "type": "choice", "options": ["in corso", "realizzato"],
                             "question": "I lavori sono iniziati?"}],
              "proposals": [{"key": "tolleranze", "question": "Ci sono tolleranze?", "proposal": "false"},
                            {"key": "diritti", "question": "I diritti",
                             "cases": [{"if": {"stato": "in corso"}, "proposal": "166"},
                                       {"if": {"stato": "realizzato"}, "proposal": "166"}]}],
              "missing": [{"field": "bianchi:identity.codice_fiscale", "why": "empty in the vault",
                           "for": "Scheda anagrafica: Cod.Fiscale"}]}
    m = run.message(report, asks, held_need={"impianti": [], "stato": []})
    want = ["1. Ci sono impianti? (sì/no)", "   1.a. Quali impianti?", "2. I lavori sono iniziati? (in corso / realizzato)",
            "– Ci sono tolleranze? → no", "   (se la cambia, le farò un'altra domanda)",
            "– I diritti → 166 se alla 2 risponde in corso o realizzato",
            "– Suoi e dello studio (una volta sola: valgono per le prossime pratiche): Cod.Fiscale"]
    return [f"by hand: no line {w!r} in:\n{m}" for w in want if w not in m.splitlines()]


def main():
    fields = dict(json.loads((REH / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    # Without the codici fiscali, so every message also asks for details no document holds.
    some = {k: v for k, v in fields.items() if "codice_fiscale" not in k}
    names = sorted(d.name for d in REH.iterdir() if (d / "recipe.yaml").exists() and (d / "answers-p6.json").exists())
    here, bad = os.getcwd(), by_hand()
    os.chdir(ROOT)
    try:
        for name in names:
            steps = gen.generate(gen.load_yaml(REH / name / "recipe.yaml"))
            full = json.loads((REH / name / "answers-p6.json").read_text())
            facts = set((steps.get("rules") or {}).get("facts", {}))
            answers = {k: v for k, v in full.items() if k in ("people", "descrizione", "fatti") or k in facts}
            for vals in (fields, some):
                r = run.preflight(steps, run.Values(dict(answers), fields=vals, asks=steps.get("asks")), made_up=True)
                if r["unsupported"]:
                    continue
                m = r.get("message")
                if (r["questions"] or r["proposals"] or r["missing"]) and not m:
                    bad.append(f"{name}: no message")
                    continue
                bad += [f"{name}: {b}" for b in holds(m or "", r)]
            print(f"ok    {name}")
    finally:
        os.chdir(here)
    for b in bad:
        print("FAIL ", b)
    print(f"{len(names)} rehearsals, {len(bad)} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
