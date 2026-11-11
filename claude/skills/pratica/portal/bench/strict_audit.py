#!/usr/bin/env python3
"""The radios and checkboxes the dictionary doesn't name, per crawled section: what gen.fill lets through.

    ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/strict_audit.py [CRAWL ...]

gen.fill never flags a radio or a checkbox that no field names (only an entry with `strict: true` does), so
"fillable" can hide a required one: the sign SCIA's two Si/No facts ran on the portal as "il valore è
obbligatorio" (2026-11-11). For each section of each crawl named (default: every stored SUAP crawl, a few
minutes), this fills the entry that fits it as `strict` and prints what it then flags. Most lines are right:
the person's declaration checkboxes (`theirs`), the option a case doesn't take (NCT, a director "SI"), what a
recipe refuses (a shopping centre's types, a company's changes). Read the rest on the portal. Nothing is written.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True
import catalogue as cat  # noqa: E402
import gen  # noqa: E402

stored = cat.crawls()
dictionary = gen.load_yaml(HERE.parent / "dictionary" / "fnsuap.yaml")
for name in sys.argv[1:] or [n for n in stored if cat.sportello(n) == "suap"]:
    for s in stored[name]["sections"]:
        if s.get("skipped") or s.get("error") or s.get("scelta"):
            continue
        sec = {**(cat.resolve(s["same_as"], stored) if s.get("same_as") else s), "section": s["section"]}
        chosen = None
        for entry, as_name in gen.dictionary_entries(dictionary["sections"], s["section"]):
            for subject in (None, "impresa"):
                if entry.get("subject", subject) == subject and not gen.fill(entry, as_name, sec, {"subject": subject} if subject else {}, s["section"])[1]:
                    chosen = (entry, as_name, subject)
                    break
            if chosen:
                break
        if not chosen:
            continue
        entry, as_name, subject = chosen
        problems = gen.fill({**entry, "strict": True}, as_name, sec, {"subject": subject} if subject else {}, s["section"])[1]
        if problems:
            print(f"{name[:42]} | {s['section'][:45]} | {[p.split(': ', 1)[1][:70] for p in problems][:4]}")
