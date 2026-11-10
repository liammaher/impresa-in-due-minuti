#!/usr/bin/env python3
"""After Claude prepares a pratica: for a portal draft, what Claude says in the chat; for a form,
one page for the person to review.

  review.py OUT [--prova] [--job DIR] [--route ROUTE.json]

OUT is the folder run.py page wrote, with the pane's `__pv.last()` saved there as report.json (its
private/shown.json adds the pratica's title and what comes after: the second compilation, what is
filed apart), or the one run.py run or fill.py run wrote. For a portal draft it prints JSON:
{"result", "message", "warnings", "steps", "yours"}; `message` is what Claude says, as written: did it
work, what the tecnico must check, what is left to them, each step with what the sportello adds to it (the
report's `details`). --prova: made-up data, a line, the check's ✅, who did what and «dettagli». It
reads two more files of a real job:

- OUT/check.json, Claude's check of the portal's own preview (portal/preview_text.js) against
  the job's documents: {"rows": [{"section", "label", "portal", "document", "source", "ok",
  "note"}], "not_in_preview": [section, ...]}. Each value that doesn't match is a warning.
- OUT/portal-files.json, what portal/attachments.js returned ({"files": [{"slot", "name",
  "size", "sha256"}]}): each file is matched by its bytes to a file of the job (--job, default
  OUT's parent folder), hashed here; one no file of the job has is a warning.

For a form (fill.py's report, --route `fill.py route --json`: where it goes and the person's
steps) it writes OUT/review.html: one self-contained file, the form's pages inlined, to show the
person before they sign anything.
"""

import argparse
import base64
import hashlib
import html
import json
import re
import sys
from pathlib import Path

CSS = """
:root { --bg:#fff; --fg:#1d1d1f; --muted:#6e6e73; --line:#e5e5ea; --ok:#1a7f37; --bad:#c62828;
        --you:#fff8e1; --you-line:#f0c36d; --card:#f7f7f8; }
@media (prefers-color-scheme: dark) { :root { --bg:#161618; --fg:#f2f2f7; --muted:#a1a1a6;
        --line:#2c2c2e; --ok:#3fb950; --bad:#ff6b6b; --you:#2a2414; --you-line:#8a6d2b; --card:#1f1f22; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
       font:15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
main { max-width: 860px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 22px; margin: 0 0 4px; }
h2 { font-size: 16px; margin: 28px 0 8px; }
.sub { color: var(--muted); margin: 0 0 16px; }
.status { display:inline-block; font-weight:600; padding:2px 10px; border-radius:999px; border:1px solid; }
.status.ok { color: var(--ok); } .status.bad { color: var(--bad); }
.you { background: var(--you); border: 1px solid var(--you-line); border-radius: 10px; padding: 12px 16px; }
.you ol { margin: 0; padding-left: 20px; } .you li { margin: 4px 0; }
.facts { display:grid; grid-template-columns: max-content 1fr; gap: 4px 16px; margin: 0; }
.facts dt { color: var(--muted); } .facts dd { margin: 0; overflow-wrap: anywhere; }
ul.checks { list-style: none; padding: 0; margin: 0; }
ul.checks li::before { content: "✓ "; color: var(--ok); font-weight: 700; }
ul.checks li.bad::before { content: "✗ "; color: var(--bad); }
details { border: 1px solid var(--line); border-radius: 10px; margin: 8px 0; background: var(--card); }
summary { cursor: pointer; padding: 10px 14px; font-weight: 600; }
table { width: 100%; border-collapse: collapse; }
td { padding: 6px 14px; border-top: 1px solid var(--line); vertical-align: top; overflow-wrap: anywhere; }
td:first-child { color: var(--muted); width: 42%; }
.blank { color: var(--muted); font-style: italic; }
img.page { width: 100%; border: 1px solid var(--line); border-radius: 6px; margin: 8px 0; background: #fff; }
"""


def esc(x):
    return html.escape("" if x is None else str(x))


def page(title, subtitle, ok, status, yours, facts, checks, groups, extra=""):
    out = [f"<!doctype html><html lang='it'><head><meta charset='utf-8'>"
           f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>{esc(title)}</title><style>{CSS}</style></head><body><main>",
           f"<h1>{esc(title)}</h1><p class='sub'>{esc(subtitle)}</p>",
           f"<span class='status {'ok' if ok else 'bad'}'>{esc(status)}</span>"]
    if yours:
        out.append("<h2>Cosa resta da fare a te</h2><div class='you'><ol>"
                   + "".join(f"<li>{esc(y)}</li>" for y in yours) + "</ol></div>")
    if facts:
        out.append("<h2>Dove va</h2><dl class='facts'>"
                   + "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in facts if v) + "</dl>")
    out.append("<h2>Cosa è stato controllato</h2><ul class='checks'>"
               + "".join(f"<li class='{'' if c_ok else 'bad'}'>{esc(c)}</li>" for c, c_ok in checks) + "</ul>")
    out.append("<h2>Ogni valore</h2>")
    for name, rows in groups:
        out.append(f"<details open><summary>{esc(name)}</summary><table>"
                   + "".join(f"<tr><td>{esc(label)}</td><td{' class=blank' if blank else ''}>{esc(value)}</td></tr>"
                             for label, value, blank in rows) + "</table></details>")
    out.append(extra + "</main></body></html>")
    return "".join(out)


def text(v):
    if isinstance(v, list):
        return "; ".join(", ".join(f"{k}: {x}" for k, x in r.get("cells", r).items()) if isinstance(r, dict) else str(r)
                         for r in v)
    return v


def form_review(out, report, route):
    checks = report["checks"]
    ok = all(c["ok"] for c in checks)
    rows = [(r["label"], text(r.get("value")) if r["status"] in ("value", "answered") else
             f"lasciato vuoto ({r.get('reason', 'niente da scrivere')})", r["status"] not in ("value", "answered"))
            for r in report["rows"]]
    yours, facts = [], []
    if route:
        # Every step but filling in the form, which the library words "Compilare ..." and
        # fill.py just did; a step for anyone (the planimetria, the F24) is still to do.
        yours = [s["do"] for s in route["steps"] if not s["do"].startswith("Compilare")]
        facts = [("Canale", route["route"]), ("Destinatario", "; ".join(w.get("address", "") for w in route.get("where", []))),
                 ("Firma", "; ".join(s["text"] for s in route.get("signing", []))),
                 ("Allegati", "; ".join(route.get("attach", []))), ("Scadenza", route.get("deadline"))]
    pages = "".join(f"<img class='page' alt='{esc(p.name)}' src='data:image/png;base64,"
                    f"{base64.b64encode(p.read_bytes()).decode()}'>" for p in sorted(out.glob("page-*.png")))
    return page(route["title"] if route else report["entry"], f"{report['entry']} · {report['form']}", ok,
                "Pronto da rivedere: ogni controllo è andato bene" if ok else "Non pronto: un controllo non è andato",
                yours, facts, [(c["check"] + (f": {c['detail']}" if c.get("detail") and not c["ok"] else ""), c["ok"])
                               for c in checks],
                [("Campi del modulo", rows)], f"<h2>Il modulo compilato</h2>{pages}" if pages else "")


def mismatches(out):
    """Claude's check of the portal's preview against the documents (OUT/check.json): a line for
    each value that doesn't match, with what the portal and the document each say."""
    f = out / "check.json" if out else None
    rows = json.loads(f.read_text()).get("rows", []) if f and f.exists() else []
    return [f"{section(r.get('section'))}, {r.get('label')}: sul portale «{r.get('portal')}», nel documento "
            f"«{r.get('document')}»" + (f" ({r['source']})" if r.get("source") else "") + "."
            for r in rows if not r.get("ok")]


def job_hashes(out, job):
    """The sha256 of each file of the job (not the run's own folder, not hidden files)."""
    local = set()
    for p in sorted(job.rglob("*")):
        # Not the run's own folder, not hidden files; a file that can't be read is skipped.
        if out in p.parents or any(part.startswith(".") for part in p.relative_to(job).parts):
            continue
        try:
            if p.is_file() and p.stat().st_size <= 50 * 2**20:
                local.add(hashlib.sha256(p.read_bytes()).hexdigest())
        except OSError:
            continue
    return local


def not_read_back(out, attached):
    """The files the compilation attached that the portal's «Allega documenti» doesn't list (one sits in a
    quadro of the form, such as the receipt of a sanction): not read back, so the tecnico looks at them."""
    f = out / "portal-files.json" if out else None
    if not (f and f.exists() and attached):
        return []
    on_portal = {x.get("sha256") for x in json.loads(f.read_text()).get("files", [])}
    return [f"Il file «{a['name']}» sta in un quadro del modulo, non in «Allega documenti»: non l'ho riletto sul portale, "
            "controllalo tu sul portale." for a in attached if a["sha256"] not in on_portal]


def stray_files(out, job):
    """The draft's files as the portal holds them (OUT/portal-files.json), each matched by its bytes
    to a file of the job: a line for each that no file of the job has."""
    f = out / "portal-files.json" if out else None
    if not (f and f.exists() and job):
        return []
    files = json.loads(f.read_text()).get("files", [])
    local = job_hashes(out, job)
    return [f"Allegato «{x.get('slot')}»: il file sul portale ({x.get('name')}) non è nessuno dei tuoi file."
            for x in files if x.get("sha256") not in local]


def verified(out, job, prova=False, attached=None):
    """The ✅ lines of the check against the documents: what the preview read held equal (OUT/check.json),
    and the attached files that are the job's own (OUT/portal-files.json). [] when it wasn't done:
    `unchecked` says so, never silence."""
    lines = []
    f = out / "check.json" if out else None
    if f and f.exists():
        rows = json.loads(f.read_text()).get("rows", [])
        ok = sum(1 for r in rows if r.get("ok"))
        if rows:
            source = "con il caso di prova" if prova else "con i tuoi documenti"
            lines.append(f"✅ Anteprima PDF del portale letta e confrontata {source}: "
                         + ("un dato corrisponde." if len(rows) == 1 and ok else f"tutti i {ok} dati corrispondono." if ok == len(rows) else f"{ok} dati su {len(rows)} corrispondono."))
    g = out / "portal-files.json" if out else None
    if g and g.exists():
        on_portal = {x.get("sha256") for x in json.loads(g.read_text()).get("files", [])}
        local = job_hashes(out, job) if job else set()
        # Distinct files, as the card counts them: one file may fill several slots. `attached` is what the
        # compilation attached (run.py page); without it (an older run) the portal's own list is all there is.
        read = {a["sha256"] for a in attached if a["sha256"] in on_portal} if attached else {h for h in on_portal if h in local}
        total, m = (len(attached) if attached else len(read)), len(read)
        if m:
            who = ("del caso di prova", "del caso di prova") if prova else ("il tuo", "i tuoi")
            what = (f"{'quello' if m == 1 else 'quelli'} {who[0]}" if prova else f"{who[0] if m == 1 else who[1]}")
            if total > m:  # some attached file isn't on the screen read: not_read_back names it
                lines.append(f"✅ Dei {total} file allegati ne ho {'riletto 1' if m == 1 else f'riletti {m}'} sul portale: "
                             f"{'è' if m == 1 else 'sono'} proprio {what} (stessi byte).")
            else:
                lines.append(f"✅ {m} file allegat{'o' if m == 1 else 'i'} sul portale {'è' if m == 1 else 'sono'} proprio {what} (stessi byte).")
    return lines


def unchecked(out):
    """Why there is no ✅ for the preview: the check was not done or the preview couldn't be read."""
    f = out / "check.json" if out else None
    rows = json.loads(f.read_text()).get("rows", []) if f and f.exists() else []
    return [] if rows else ["Il confronto con l'anteprima del portale non è stato fatto: leggila tu prima di firmare."]


def section(name):
    """A section's name as a sentence: the portal writes some in capitals ("DOMICILIO ELETTRONICO")."""
    name = name or ""
    return name[:1] + name[1:].lower() if name.isupper() else name


# The pratiche whose name is masculine ("il permesso di costruire"): the rest are feminine (CILA,
# SCIA, comunicazione, proroga, autorizzazione...), as the message's past participle agrees.
MASCULINE = re.compile(r"(Permesso|PdC|Accertamento|Ampliamento|Cambio|Inizio|Rinnovo|Parere|Subingresso)\b")


def pratica_name(report):
    """The pratica as the tecnico calls it: the steps file's title without the sportello and the
    role ("CILA: lavori interni non strutturali, SUE Napoli (tecnico con procura)" is "CILA")."""
    t = report.get("title") or report.get("procedure") or "La pratica"
    return re.sub(r",\s*SU[AE]P? Napoli\b.*$", "", t).split(":")[0].strip()


def duration(s):
    s = round(s or 0)
    return f"{s} secondi" if s < 120 else f"{round(s / 60)} minuti"


def tu_steps(later, reopened=False):
    """The tecnico's steps, in order, as the card says them (bench/test_card.py holds run.tu_steps to the same
    list): only what they do. later: what the second compilation attaches (the procura, the quadro riepilogativo
    and the receipt of what is paid first, the diritti), which the second line of the signing step names."""
    pay_first = any(re.search(r"versament|ricevut|pagament", x, re.I) for x in later)
    if reopened:  # the second compilation: the declarations are ticked, the signed files are on the portal
        return ["controlla l'anteprima della bozza", "firma"] + ([] if pay_first else ["paga"]) + ["invia"]
    steps = ["controlla l'anteprima della bozza", "spunta le dichiarazioni"]
    if later:
        what = (["la procura"] if any(re.search(r"procura", x, re.I) for x in later) else []) \
            + (["la ricevuta del pagamento"] if pay_first else [])
        rest = [x for x in later if not re.search(r"procura|versament|ricevut|pagament", x, re.I)]
        what += ["gli altri documenti" if what else "i documenti da firmare"] if rest else []
        steps += (["paga i diritti"] if pay_first else []) + [
            f"firma {' e '.join([', '.join(what[:-1]), what[-1]] if len(what) > 1 else what)} e scrivimi «ho firmato»"]
    return steps + ["firma"] + ([] if pay_first and later else ["paga"]) + ["invia"]


def numbered(steps, details, then=None):
    """The steps a line each, with what the sportello adds in brackets (where the diritti are paid, the order of
    the signatures, what comes back after sending). `then`: a line of Claude's own under the step that hands the
    signed files over."""
    lines = []
    for i, s in enumerate(steps, 1):
        lines.append(f"{i}. {s[0].upper()}{s[1:]}" + (f" ({details[s]})" if details.get(s) else ""))
        if then and s.endswith("«ho firmato»"):
            lines.append(f"   {then}")
    return lines


def summary(report, out=None, job=None, prova=False):
    """What Claude says in the chat once a portal compilation ends: did it work, what the tecnico
    must check (the portal's warnings beside values it kept, a value or a file that doesn't match
    the documents), and what is left to them. `message` is said as written. A Prova (made-up
    data) says who did what instead of the steps: its warnings are expected, and nothing of it is sent."""
    if report.get("result") != "filled":
        return {"result": report.get("result") or "stopped", "message": None, "warnings": [], "steps": []}
    name = pratica_name(report)
    done = "compilato" if MASCULINE.match(name) else "compilata"
    if prova:
        # The portal's own warnings on made-up values (the PEC) are expected; a value that doesn't match
        # the case, or a file that isn't the Prova's, is not.
        warns = mismatches(out) + stray_files(out, job) + not_read_back(out, report.get("attached")) + unchecked(out)
        lines = [f"✅ {name} di prova {done} in {duration(report.get('total_seconds'))}, con dati inventati."]
        lines += verified(out, job, prova=True, attached=report.get("attached")) + [f"⚠️ {w}" for w in warns]
        # Who does what in a real filing, in two lines; every answer and its source are one word away.
        n = report.get("quadri")
        lines.append("Io: " + (f"ho compilato {n} quadri" if n and n > 1 else "ho compilato il modulo")
                     + ", allegato i file e riletto tutto dal portale.")
        lines.append("Tu, in una pratica vera: controlli l'anteprima, spunti le dichiarazioni, paghi, firmi e invii.")
        lines.append("Per vedere ogni risposta e da dove viene, scrivi «dettagli».")
        lines.append("Nulla da inviare: cancella la bozza da «Pratiche in bozza».")
        return {"result": "filled", "warnings": warns, "steps": [], "message": "\n".join(lines)}
    # One line for each warning in a section, by the section alone: the portal shows it beside the
    # box, and its labels read badly out of the page ("se non presente indicare il numero 0"). On
    # made-up data the catasto's comes four times, one for each box of the parcel (2026-11-07).
    warnings = list(dict.fromkeys(f"{section(a['section'])}: il portale segnala «{a['text'].strip()}». Controllalo."
                                  for a in report.get("alerts", [])))
    warnings += mismatches(out) + stray_files(out, job) + not_read_back(out, report.get("attached"))
    # The second compilation (after the declarations) attaches what the portal makes only then, signed:
    # the procura, the quadro riepilogativo, and the receipt of what is paid first (the diritti).
    later = list(dict.fromkeys(report.get("second_run") or []))
    reopened = bool(report.get("reopened"))  # this is the second compilation: the declarations are ticked
    if reopened:
        head = f"✅ {name}: file firmati allegati sul portale in {duration(report.get('total_seconds'))}; ogni valore è stato riletto."
    else:
        head = f"✅ {name} {done} sul portale in {duration(report.get('total_seconds'))}: ogni valore è stato riletto."
    steps = tu_steps(later, reopened)
    lines = [head] + [f"⚠️ {w}" for w in warnings]
    lines.append("Tocca a te:")
    lines += numbered(steps, report.get("details") or {}, None if reopened else "Io poi li allego con una seconda compilazione.")
    lines += [f"{a}." for a in report.get("apart") or []]
    # `yours`, the steps file's own steps in full (how the diritti are paid, the files' rules), is
    # not said: Claude answers from it when the tecnico asks how.
    return {"result": "filled", "warnings": warnings, "steps": steps, "yours": report.get("yours", []),
            "message": "\n".join(lines)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--route", type=Path)
    ap.add_argument("--prova", action="store_true", help="the skill's Prova: made-up data, the check's ✅, who did what")
    ap.add_argument("--job", type=Path, help="the job's folder, whose files the portal's are matched to "
                    "(default: OUT's parent)")
    a = ap.parse_args()
    report = json.loads((a.out / "report.json").read_text())
    if "rows" in report:  # fill.py's form
        route = json.loads(a.route.read_text()) if a.route else None
        (a.out / "review.html").write_text(form_review(a.out, report, route), encoding="utf-8")
        print(a.out / "review.html")
        return 0
    shown = a.out / "private" / "shown.json"  # run.py page: the pane's report has only the run
    if shown.exists():
        report |= json.loads(shown.read_text())
    job = (a.job or a.out.resolve().parent).resolve()
    print(json.dumps(summary(report, a.out.resolve(), job, a.prova), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
