#!/usr/bin/env python3
"""The card ("Cosa succede") pre-flight gives a case that is ready: for every rehearsal that gets one, it
is two lines in Italian (the pratica and why, what Claude does), in tu, shows no field id, role code or
personal value, none of the machine workings (wizard path, sources, quadri, byte for byte), of what the tecnico
does (the verdict and review.py's closing lines say it) or of a real filing's details (c/c, signing order, PEC),
and says it reads the PDF preview back only when the skill does. review.py's closing lines carry those details
next to the steps, and say the same steps. The Prova's, by hand: the made-up marker, nothing to send.

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
MAX_LINES = 3  # heading, what Claude does, and in a Prova (made up, as these run) that nothing is sent
GONE = re.compile(r"settore|operazione|byte|c/c|PEC|distinta|«tutte»|Lei\b|Sua\b|Suoi?\b|\bPerché è questa|i fatti che|quadr|\bTu\b|\btu\b")


def problems(card, fields, later, sportello, rows):
    bad = []
    lines = [x for x in card.splitlines() if x.strip()]
    if len(lines) > MAX_LINES:
        bad.append(f"{len(lines)} lines (max {MAX_LINES})")
    if LEAK.search(card):
        bad.append(f"shows {LEAK.search(card).group(0)!r}")
    if CF.search(card):
        bad.append("shows a codice fiscale")
    if ENGLISH.search(card):
        bad.append(f"English: {ENGLISH.search(card).group(0)!r}")
    if GONE.search(card):
        bad.append(f"says {GONE.search(card).group(0)!r}: it belongs to the closing lines, or nowhere")
    personal = {v for k, v in fields.items()
                if re.search(r"first_name|last_name|codice_fiscale|\.civico|\.via$", k) and len(str(v)) > 3}
    bad += [f"shows the value {v!r}" for v in personal if str(v) in card]
    if not (lines[0].startswith("**") and lines[1].startswith("Io compilo la bozza")):
        bad.append("not the heading and «Io compilo la bozza …»")
    asked = {s.split(" ")[0] for s in run.tu_steps(later)}
    if not {"controlla", "spunta", "paga", "firma", "invia"} <= asked:
        bad.append(f"the steps {run.tu_steps(later)} lack a verb of the real filing")
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
            later = run.after_declarations(run.expand(steps, values), values)
            found = problems(r["card"], fields, later, run.filing_rules(steps), r.get("riepilogo_rows"))
            # review.py's closing lines for the same case say the same steps, word for word.
            said = review.summary({"result": "filled", "title": steps["title"], "second_run": later}, None, None)["steps"]
            if said != run.tu_steps(later):
                found.append(f"review.py says {said}, the runner {run.tu_steps(later)}")
            bad += [f"{name}: {b}" for b in found]
            print(("ok    " if not found else "FAIL  ") + name)

        # The Prova by hand.
        steps = gen.generate(gen.load_yaml(REH / "cila-fittizia" / "recipe.yaml"))
        values = run.Values(json.loads((REH / "cila-fittizia" / "answers-p6.json").read_text()),
                            fields=fields, asks=steps.get("asks"))
        r = run.preflight(steps, values, made_up=True)
        card = r["card"]
        for want in ("(prova, dati inventati)", "Io compilo la bozza", "file di prova", "Qui non c'è nulla da inviare",
                     "cancella la bozza"):
            if want.lower() not in card.lower():
                bad.append(f"Prova card lacks {want!r}")
        plain = run.card(run.expand(steps, values), values, r, True, r.get("riepilogo_rows"), preview_check=False)
        if "rileggo ogni casella" not in plain or "tutto dal portale" in plain:
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
                if ("tutto dal portale" in want) != check:
                    bad.append(f"preview_check={check}, but the card says otherwise")
            # «dettagli»: every answer and where it comes from, the same rows as the summary's, and no «sì» to wait for.
            cli = subprocess.run([sys.executable, "-I", str(HERE.parent / "run.py"), "details", "--steps", str(sf),
                                  "--answers", str(REH / "cila-fittizia" / "answers-p6.json"),
                                  "--values", str(REH / "cila-fittizia" / "fixture-p6.json"), "--made-up"],
                                 capture_output=True, text=True)
            rows = run.summary_rows(steps, values)
            if cli.returncode or cli.stdout.count("\n– ") != len(rows) or "«sì»" in cli.stdout or "Lei" in cli.stdout:
                bad.append(f"`run.py details --made-up` isn't the answers' list:\n{cli.stdout[:400]}{cli.stderr}")
        real = run.card(run.expand(steps, values), values, r, False, r.get("riepilogo_rows"))
        if "(prova" in real or "Qui non c'è nulla da inviare" in real or "di prova" in real:
            bad.append("a real job's card carries the Prova's words")
        if not real.splitlines()[0].startswith("**CILA, "):
            bad.append(f"a real job's card doesn't say why it is this pratica: {real.splitlines()[0]!r}")
        # What the sportello adds goes next to each step in the closing lines, never in the card.
        det = run.step_details(steps)
        if set(det) != {"paga i diritti", "paga", "firma la pratica", "invia"} or any(v in real or v in card for v in det.values()):
            bad.append(f"step details {det}: missing, or in the card")
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
