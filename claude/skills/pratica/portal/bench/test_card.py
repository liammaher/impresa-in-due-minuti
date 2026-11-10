#!/usr/bin/env python3
"""The card ("Cosa succede") pre-flight gives a case that is ready: for every rehearsal that gets one, it
is Italian, short, shows no field id, role code or personal value, names what stays the tecnico's in
the order review.py's closing lines give it, and says it reads the PDF preview back only when the skill
does. The Prova's, by hand: the made-up marker, the whole real journey, nothing to send.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_card.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1]))  # review.py
sys.dont_write_bytecode = True
import gen  # noqa: E402
import review  # noqa: E402
import run  # noqa: E402

ROOT = HERE.parents[4]
REH = ROOT / "rehearsals"
LEAK = re.compile(r"\b[a-z][a-z0-9-]*:[a-z_]+\.[a-z_]+\b|(?<![\w/])(?:t|c|cr|o|r|p|f\d?):(?=\w)")
CF = re.compile(r"\b[A-Z]{6}\d\d[A-Z]\d\d[A-Z]\d{3}[A-Z]\b")
ENGLISH = re.compile(r"\b(the|your|you|and|of|was|draft|saved|every|value|left|filled|sign|send|pay)\b")
MAX_LINES = 34


def problems(card, fields, later, sportello):
    bad = []
    lines = card.splitlines()
    if len(lines) > MAX_LINES:
        bad.append(f"{len(lines)} lines (max {MAX_LINES})")
    if LEAK.search(card):
        bad.append(f"shows {LEAK.search(card).group(0)!r}")
    if CF.search(card):
        bad.append("shows a codice fiscale")
    if ENGLISH.search(card):
        bad.append(f"English: {ENGLISH.search(card).group(0)!r}")
    personal = {v for k, v in fields.items()
                if re.search(r"first_name|last_name|codice_fiscale|\.civico|\.via$", k) and len(str(v)) > 3}
    bad += [f"shows the value {v!r}" for v in personal if str(v) in card]
    for sect in ("Che pratica è", "Cosa compilo", "Come controllo", "Cosa non faccio mai"):
        if sect not in card:
            bad.append(f"no {sect!r}")
    # What stays theirs, in the order the closing lines say it.
    start = next((i for i, x in enumerate(lines) if "a Lei, in ordine" in x), None)
    mine = [re.sub(r"^\d+\. ", "", ln) for ln in lines[(start or 0) + 1:] if re.match(r"\d+\. ", ln)]
    want = [s[:1].upper() + s[1:] for s in run.lei_steps(later)]
    if start is None or len(mine) != len(want) or not all(m.startswith(w) for m, w in zip(mine, want)):
        bad.append(f"their steps {mine} are not {want}")
    if sportello and sportello.get("card", {}).get("sign") and sportello["card"]["sign"] not in card:
        bad.append("the sportello's signing detail is missing")
    return bad


def main():
    fields = dict(json.loads((REH / "cila-fittizia" / "fixture-p6.json").read_text())["fields"])
    names = sorted(d.name for d in REH.iterdir() if (d / "recipe.yaml").exists() and (d / "answers-p6.json").exists())
    here, bad, n = os.getcwd(), [], 0
    os.chdir(ROOT)
    try:
        for name in names:
            steps = gen.generate(gen.load_yaml(REH / name / "recipe.yaml"))
            answers = json.loads((REH / name / "answers-p6.json").read_text())
            values = run.Values(dict(answers), fields=fields, asks=steps.get("asks"))
            r = run.preflight(steps, values, made_up=True)
            if r["unsupported"] or "card" not in r:
                continue
            n += 1
            later = run.card_later(run.expand(steps, values), values, True)  # made-up, as pre-flight ran
            found = problems(r["card"], fields, later, run.filing_rules(steps))
            # review.py's closing lines for the same case say the same steps, word for word.
            said = review.summary({"result": "filled", "title": steps["title"], "second_run": later}, None, None)["steps"]
            if said != run.lei_steps(later):
                found.append(f"review.py says {said}, the card {run.lei_steps(later)}")
            bad += [f"{name}: {b}" for b in found]
            print(("ok    " if not found else "FAIL  ") + name)

        # The Prova by hand.
        steps = gen.generate(gen.load_yaml(REH / "cila-fittizia" / "recipe.yaml"))
        values = run.Values(json.loads((REH / "cila-fittizia" / "answers-p6.json").read_text()),
                            fields=fields, asks=steps.get("asks"))
        r = run.preflight(steps, values, made_up=True)
        card = r["card"]
        for want in ("(prova, dati inventati)", "In una pratica vera restano a Lei", "Leggo l'anteprima PDF",
                     "con il caso di prova", "Qui non c'è nulla da inviare", "c/c postale 57060964", "Firma"):
            if want.lower() not in card.lower():
                bad.append(f"Prova card lacks {want!r}")
        if "Paghi i diritti" not in card:
            bad.append("Prova card doesn't show the diritti before the second compilation (the real journey)")
        plain = run.card(run.expand(steps, values), values, r, True, r.get("riepilogo_rows"), preview_check=False)
        if "Leggo l'anteprima" in plain:
            bad.append("promises the preview check when the skill won't do it")
        # The command a skill runs prints the very card pre-flight makes (2026-11-10: it once phased the steps first
        # and lost the second compilation), with and without the preview check.
        with tempfile.TemporaryDirectory() as t:
            sf = Path(t) / "steps.yaml"
            sf.write_text(gen.dump(steps))
            for flag, check in (([], True), (["--no-preview-check"], False)):
                cli = subprocess.run([sys.executable, "-I", str(HERE.parent / "run.py"), "card", "--steps", str(sf),
                                      "--answers", str(REH / "cila-fittizia" / "answers-p6.json"),
                                      "--values", str(REH / "cila-fittizia" / "fixture-p6.json"), "--made-up", *flag],
                                     capture_output=True, text=True)
                want = run.preflight(steps, run.Values(json.loads((REH / "cila-fittizia" / "answers-p6.json").read_text()),
                                                       fields=fields, asks=steps.get("asks")),
                                     made_up=True, preview_check=check)["card"]
                if cli.returncode or cli.stdout.rstrip("\n") != want:
                    bad.append(f"`run.py card {' '.join(flag)}` prints another card than pre-flight's:\n{cli.stdout}{cli.stderr}")
                if ("Leggo l'anteprima" in want) != check:
                    bad.append(f"preview_check={check}, but the card says otherwise")
        real = run.card(run.expand(steps, values), values, r, False, r.get("riepilogo_rows"))
        if "(prova" in real or "Qui non c'è nulla da inviare" in real:
            bad.append("a real job's card carries the Prova's words")
    finally:
        os.chdir(here)
    if n < 20:
        bad.append(f"only {n} rehearsals got a card")
    for b in bad:
        print("FAIL ", b)
    print(f"{n} cards, {len(bad)} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
