#!/usr/bin/env python3
"""A new SUAP rehearsal from the closest sibling's recipe: the recipe, a made-up answers file and a fixture.

    ~/.cache/pratica-portal/venv/bin/python claude/skills/pratica/portal/bench/derive_recipe.py \\
        NEW TEMPLATE CRAWL [--fixture REHEARSAL] [--no-fill]

NEW is the rehearsal to make (rehearsals/NEW/), TEMPLATE the sibling whose recipe it copies (same operation, nearest
sector: the shops' from a shop's, the bars' from a bar's), CRAWL the stored crawl it is generated from
(catalogue/F839/sections/CRAWL.json). Written 2026-11-11 for the 33 wedge cells that had no rehearsal, and then run on the
portal in the pane (README, "The wedge's cells run on the portal"). What it changes in the copy:

- the crawl, the operation and the wizard's sector and operation labels (the crawl's `pratica` names both; a sector the
  tree repeats is `{leaf, nth}`, as bench/test_gen.py holds every SUAP recipe to), and the interventi screen as the crawl has it;
- the title and the header comment;
- it drops the template's `after:`, `slots`, `rules:`, `scelte:` and `first:`: the attachments and payment screens aren't read
  (their slots need a filled draft), the SUAP rules table has no event for a suspension or a change of people, and a second
  recipe for a case that one already holds makes route.py ambiguous. Add `rules:` by hand where the table decides a case no
  recipe holds yet;
- the fixture is copied from --fixture (default: the template's own, else the family's: README).
Then, unless --no-fill, it generates the steps file and runs pre-flight, answering what it asks from the values the other
rehearsals use (a choice, a date, a file), up to four rounds, and prints what is left for a person: a case's own answers
(a food workshop's Reg. 852 list, a take-over's deed) and the refusals pre-flight names. Wording that names the template's
sector in a question stays: read the recipe. A draft's name is 60 characters at most ("PROVA NON INVIARE - " included).
"""
import argparse
import glob
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORTAL = HERE.parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(PORTAL))
sys.dont_write_bytecode = True

WIZARD = json.loads((PORTAL / "catalogue" / "F839" / "suap-wizard.json").read_text())["sectors"]
SHORT = {4: "panificio", 5: "laboratorio alimentare", 16: "negozio non alimentare", 17: "negozio alimentare o misto",
         18: "negozio alimentare, zone tutelate", 56: "struttura ricettiva extralberghiera", 60: "bar o ristorante", 61: "bar o ristorante, zone tutelate"}
FIXTURE = {4: "panificio-fittizio", 5: "panificio-fittizio", 11: "negozio-fittizio", 16: "negozio-fittizio", 17: "negozio-fittizio",
           18: "negozio-fittizio", 56: "affittacamere-fittizio", 60: "pizzeria-fittizia", 61: "ristorante-centro-storico-fittizio"}


def derive(new, template, crawl_name, fixture=None):
    crawl = json.loads((PORTAL / "catalogue" / "F839" / "sections" / f"{crawl_name}.json").read_text())
    m = re.search(r"› ([^›]+?) \(sector (.+)\)$", crawl["pratica"])
    op, sector = m.group(1).strip(), m.group(2).strip()
    idx = int(re.match(r"suap-(\d+)", crawl_name)[1])
    assert WIZARD[idx]["sector"] == sector, (crawl_name, sector)
    nth = sum(1 for s in WIZARD[:idx + 1] if s["sector"] == sector)
    repeated = sum(1 for s in WIZARD if s["sector"] == sector) > 1
    tree = '{leaf: "%s", nth: %d}' % (sector, nth) if repeated else ('"%s"' % sector if re.search(r"[:,#]", sector) else sector)
    screens = [s["screen"] for s in (crawl.get("screens") or [])]
    lines = (ROOT / "rehearsals" / template / "recipe.yaml").read_text(encoding="utf-8").split("\n")
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    out, skip = [], False
    for ln in lines:
        if re.match(r"^(after|slots|rules|scelte|first):", ln) or (skip and ln[:1] in (" ", "\t")):
            skip = True
            continue
        skip = False
        out.append(ln)
    text = "\n".join(out)
    text = re.sub(r"(^#.*\n)+(?=wizard:|groups:|asks:|yours:|supports:)", "", text, flags=re.M)
    text = re.sub(r"^crawl: .*$", f"crawl: {crawl_name}", text, flags=re.M)
    text = re.sub(r"^operation: .*$", "operation: " + (json.dumps(op, ensure_ascii=False) if ":" in op else op), text, flags=re.M)
    text = re.sub(r"^(  - \{screen: Scelta settore attività, tree: )\[.*?\](, confirm: CONFERMA\})", lambda k: k[1] + "[" + tree + "]" + k[2], text, flags=re.M)
    text = re.sub(r"^(  - \{screen: Scelta operazioni, tree: )\[.*\](, confirm: CONFERMA\})", lambda k: k[1] + "[" + json.dumps(op, ensure_ascii=False) + "]" + k[2], text, flags=re.M)
    text = re.sub(r"^  - \{screen: Scelta interventi eventuali.*\n", "", text, flags=re.M)
    if "scelta interventi eventuali" in screens:
        text = text.replace("  - {screen: Scelta del destinatario della pratica", "  - {screen: Scelta interventi eventuali, confirm: CONFERMA}\n  - {screen: Scelta del destinatario della pratica", 1)
    # A short Italian sector name: the wizard's own is long ("Strutture ricettive extralberghiere (affittacamere, bed and ...") and a
    # title cut at 60 characters read as English to bench/test_gen.py's check of what the tecnico reads.
    text = re.sub(r"^title: .*$", "title: " + json.dumps(f"{op}, {SHORT.get(idx, 'acconciatori, estetisti e tatuatori')}, SUAP Napoli", ensure_ascii=False), text, flags=re.M)
    header = (f"# {op} ({sector}), as gen.py writes its steps file from the batch crawl\n# (catalogue/F839/sections/{crawl_name}.json), for the made-up business of this folder's fixture.json.\n"
              f"# Derived from rehearsals/{template} (bench/derive_recipe.py): no `rules:` and no `after:`; the attachments and payment screens are not read.\n")
    folder = ROOT / "rehearsals" / new
    folder.mkdir(exist_ok=True)
    (folder / "recipe.yaml").write_text(header + text, encoding="utf-8")
    answers = {}
    for name in ("answers.json", "answers-p1.json"):
        if (ROOT / "rehearsals" / template / name).exists():
            answers = json.loads((ROOT / "rehearsals" / template / name).read_text())
            break
    short = re.sub(r"-fittizi[oa]$", "", new).replace("-", " ")[:28].rstrip()
    answers["descrizione"] = f"PROVA NON INVIARE - {short} generato"
    answers["oggetto"] = f"{op}: pratica di prova con dati inventati."
    (folder / "answers.json").write_text(json.dumps(answers, ensure_ascii=False, indent=1) + "\n")
    source = fixture or (template if (ROOT / "rehearsals" / template / "fixture.json").exists() else FIXTURE[idx])
    shutil.copy(ROOT / "rehearsals" / source / "fixture.json", folder / "fixture.json")
    return folder


def pool():
    values = {}
    for f in sorted(glob.glob(str(ROOT / "rehearsals" / "*" / "answers*.json"))):
        try:
            for k, v in json.loads(Path(f).read_text()).items():
                values.setdefault(k, v)
        except ValueError:
            pass
    return values


def fill(folder):
    py = sys.executable
    gen = subprocess.run([py, str(PORTAL / "gen.py"), str(folder / "recipe.yaml"), "--out", str(folder / "portal-steps.generated.yaml")], capture_output=True, text=True)
    if gen.returncode or gen.stderr.strip():
        return {"gen": (gen.stderr or gen.stdout)[-400:]}
    values = pool()
    for _ in range(4):
        r = subprocess.run([py, str(PORTAL / "run.py"), "preflight", "--made-up", "--values", str(folder / "fixture.json"), "--steps", str(folder / "portal-steps.generated.yaml"),
                            "--answers", str(folder / "answers.json")], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
        except ValueError:
            return {"preflight": (r.stdout + r.stderr)[-400:]}
        answers = json.loads((folder / "answers.json").read_text())
        added = False
        for q in d["questions"]:
            if q["key"] not in answers and q["key"] in values:
                answers[q["key"]], added = values[q["key"]], True
        for p in d["proposals"]:
            if p.get("key") and p["key"] not in answers and (p.get("key") in values or "value" in p):
                answers[p["key"]], added = p.get("value", values.get(p["key"])), True
        if not added:
            return {"ready": d["ready"], "unsupported": d["unsupported"], "questions": [q["key"] for q in d["questions"]], "proposals": [p.get("key") for p in d["proposals"]],
                    "files": [f["for"] for f in d["files"] if not f["exists"]]}
        (folder / "answers.json").write_text(json.dumps(answers, ensure_ascii=False, indent=1) + "\n")
    return {"ready": False, "note": "still asking after four rounds"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("new")
    ap.add_argument("template")
    ap.add_argument("crawl")
    ap.add_argument("--fixture", help="the rehearsal whose fixture.json the new one copies")
    ap.add_argument("--no-fill", action="store_true")
    a = ap.parse_args()
    folder = derive(a.new, a.template, a.crawl, a.fixture)
    print(f"wrote {folder.relative_to(ROOT)}: recipe.yaml, answers.json, fixture.json")
    if not a.no_fill:
        print(json.dumps(fill(folder), ensure_ascii=False))


if __name__ == "__main__":
    main()
