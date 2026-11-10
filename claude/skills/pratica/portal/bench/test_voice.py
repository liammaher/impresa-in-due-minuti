#!/usr/bin/env python3
"""The tecnico is addressed as tu, never Lei: nothing they read keeps a Lei form (Lei, Suo/Sua/Suoi, a formal
imperative such as «Spunti», «Paghi», «Firmi», «Apra», a pronoun such as «Le dico», «come Le indica»). Looks at
the texts that reach them: the steps files (questions, `yours`, refusals, defects, rules), the dictionary and the
rules tables they are written from, the runner's own Italian (run.py, review.py, route.py, check.py ...) and the
plugin's hand-written texts (SKILL.md, prova.md, setup, README) and evals. What the law or the portal says in its
own words (a quoted label) is the portal's and never matches these forms.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_voice.py
"""
import ast
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import gen  # noqa: E402

ROOT = HERE.parents[4]
PRATICA = ROOT / "claude" / "skills" / "pratica"
LEI = re.compile(
    r"\b(Lei|Suo|Suoi|Sua|Sue)\b"
    r"|\b(Spunti|Paghi|Firmi|Invii|Alleghi|Faccia|Scriva|Apra|Controlli|Conservi|Chieda|Segnali|Nomini|Verifichi|"
    r"Risponda|Indichi|Scelga|Acceda|Clicchi|Legga|Metta|Inserisca|Selezioni|Vuole|Tenga|Lasci|Mandi|Dica)\b"
    r"|\b[Mm]i (mandi|dica|scriva)\b|\bLe (dico|scrivo|chiedo|prepari|propongo|serve|servono|basterà|dice|scrive)\b"
    r"|\b[Ll][aoie] (rilegga|scriva|consenta|faccia)\b|\b[Ll]e servono\b"
    r"|\bcome Le\b|\bnon (apra|tocchi)\b|\bse vuole\b|\bsua parte\b|\b(Riprovi|riprovi|riapra|Lo installi|li installi|lo installi|lo riscriva|a Lei)\b")
# (A verb such as «firmi», «paghi», «alleghi» is the same in tu and in the formal imperative: only a capital at
# the start of a sentence, or a clitic, gives the formal one away, which is what is looked for.)
# The rule itself names Lei, in English, to forbid it.
ALLOWED = ("never Lei", "as tu", "never as Lei", "addressing them as tu (never Lei)", "not Lei")


def strings(node):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from strings(k)
            yield from strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v)
    elif isinstance(node, str):
        yield node


def code_strings(path):
    tree = ast.parse(path.read_text())
    docs = {id(n.body[0].value) for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Module)) and ast.get_docstring(n, clean=False) is not None}
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
            yield n.value


def main():
    bad = []

    def look(where, text):
        for allowed in ALLOWED:
            text = text.replace(allowed, "")
        for m in LEI.finditer(text):
            bad.append(f"{where}: «{m.group(0)}» in «{text[max(0, m.start() - 40):m.end() + 40]!r}»")

    n = 0
    for f in sorted((ROOT / "rehearsals").glob("*/portal-steps*.yaml")):
        for s in strings(gen.load_yaml(f)):
            look(f"{f.parent.name}/{f.name}", s)
        n += 1
    for f in [*sorted((PRATICA / "portal" / "rules").glob("*.yaml")), *sorted((PRATICA / "portal" / "parts").glob("*.yaml")),
              PRATICA / "portal" / "defects.yaml", *sorted((PRATICA / "portal" / "dictionary").glob("*.yaml"))]:
        for s in strings(gen.load_yaml(f)):
            look(f.name, s)
        n += 1
    for f in [PRATICA / "portal" / "run.py", PRATICA / "review.py", PRATICA / "portal" / "route.py",
              PRATICA / "portal" / "rules.py", PRATICA / "portal" / "gen.py", PRATICA / "intake" / "intake.py",
              PRATICA / "fill" / "fill.py", ROOT / "plugin" / "impresa-in-un-minuto" / "skills" / "pratiche" / "check.py",
              ROOT / "plugin" / "impresa-in-un-minuto" / "skills" / "pratiche" / "report.py"]:
        for s in code_strings(f):
            look(f.name, s)
        n += 1
    texts = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *sorted((ROOT / "plugin" / "impresa-in-un-minuto").rglob("*.md")),
             ROOT / "plugin" / "impresa-in-un-minuto" / "skills" / "pratiche" / "py",
             ROOT / "plugin" / "impresa-in-un-minuto" / ".claude-plugin" / "plugin.json", PRATICA / "portal" / "inpage.js",
             *sorted((ROOT / "plugin" / "impresa-in-un-minuto" / "skills" / "setup").glob("install-pvault.*")),
             *sorted((ROOT / "plugin" / "evals").rglob("*.md")), *sorted((ROOT / "plugin" / "evals").rglob("*.yaml"))]
    for f in texts:
        look(str(f.relative_to(ROOT)), f.read_text())
        n += 1
    for b in bad[:60]:
        print("FAIL", b)
    print(f"{n} files read, {len(bad)} Lei forms")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
