#!/usr/bin/env python3
"""One page for the person to review a pratica Claude prepared: what's left for them, what
was checked, and every value as it went on the form or portal.

  review.py OUT [--route ROUTE.json] [--job DIR]

OUT is the folder fill.py run or run.py run wrote (its report.json), or the one run.py page
wrote with the pane's `__pv.last()` saved there as report.json (its private/shown.json adds the
values and the person's steps; private/declarations.json the declarations' own text, and
private/anteprima.pdf the portal's PDF preview, which only `run.py run` copies); --route is
`fill.py route --json` for a form, for where it goes and the person's steps. Writes
OUT/review.html: one self-contained file (the form's pages inlined), to show the person
before they sign anything. It reads only those files, and for a portal draft two more:

- OUT/check.json, Claude's check of the portal's own preview (portal/preview_text.js) against
  the job's documents: {"rows": [{"section", "label", "portal", "document", "source", "ok",
  "note"}], "not_in_preview": [section, ...]}. The mismatches come first on the page.
- OUT/portal-files.json, what portal/attachments.js returned ({"files": [{"slot", "name",
  "size", "sha256"}]}): each file is matched by its bytes to a file of the job (--job, default
  OUT's parent folder), hashed here.
"""

import argparse
import base64
import hashlib
import html
import json
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
.decl { white-space: pre-wrap; padding: 6px 14px 10px; border-top: 1px solid var(--line); overflow-wrap: anywhere; }
.decl ul { list-style: none; margin: 8px 0 0; padding: 0; } .decl li.on { color: var(--bad); font-weight: 600; }
a.dl { display:inline-block; margin: 4px 0 8px; }
img.page { width: 100%; border: 1px solid var(--line); border-radius: 6px; margin: 8px 0; background: #fff; }
"""


def esc(x):
    return html.escape("" if x is None else str(x))


def page(title, subtitle, ok, status, yours, facts, checks, groups, extra="", top=""):
    out = [f"<!doctype html><html lang='it'><head><meta charset='utf-8'>"
           f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>{esc(title)}</title><style>{CSS}</style></head><body><main>",
           f"<h1>{esc(title)}</h1><p class='sub'>{esc(subtitle)}</p>",
           f"<span class='status {'ok' if ok else 'bad'}'>{esc(status)}</span>"]
    if yours:
        out.append("<h2>Cosa resta da fare a Lei</h2><div class='you'><ol>"
                   + "".join(f"<li>{esc(y)}</li>" for y in yours) + "</ol></div>")
    out.append(top)
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


def decisions(report):
    """Choices the form took in the person's name (run.py DECIDED), apart from the long table of
    values: they state how an obligation will be met, so the person confirms each. html."""
    items = report.get("decisions") or []
    if not items:
        return ""
    out = ["<h2>Scelto a suo nome</h2><p class='sub'>Il modulo è stato compilato con queste scelte. Ognuna dice "
           "come adempirà a un obbligo: controlli che sia ciò che farà.</p><div class='you'><ul>"]
    for d in items:
        out.append(f"<li><b>{esc(d['section'])}</b><ul>" + "".join(f"<li>{esc(c)}</li>" for c in d["choices"])
                   + "</ul></li>")
    return "".join(out) + "</ul></div>"


def declarations(report, folder):
    """The declarations' own text, as the runner copied it from the portal (private/declarations.json):
    the page shows these, never Claude's summary of them. (html, checks)."""
    f = folder / "declarations.json" if folder else None
    items = json.loads(f.read_text()) if f and f.exists() else None
    note = report.get("declarations_note")
    checks = []
    if items:
        ticked = [i["section"] for i in items if any(b["ticked"] for b in i["boxes"])]
        checks.append((f"Dichiarazioni: {len(items)} copiate parola per parola dal portale; nessuna spuntata" if not ticked
                       else "Dichiarazioni già spuntate prima che Lei le aprisse (non da questa compilazione): "
                       + "; ".join(ticked), not ticked))
    elif items is not None and not note:
        checks.append(("Dichiarazioni: nessuna nel menu del portale; le legga lì una per una prima di spuntarle", False))
    elif items is None:
        checks.append(("Dichiarazioni: non copiate in questa compilazione; le legga nel portale una per una prima di "
                       "spuntarle", False))
    if note:
        checks.append(("Dichiarazioni: non tutte copiate; legga le altre nel portale", False))
    if not items:
        return "", checks
    out = ["<h2>Le dichiarazioni che spunterà</h2><p class='sub'>Le parole del portale, copiate così come sono, "
           "non un riassunto. Le legga prima di spuntarle: le rende a suo nome, e una dichiarazione falsa è "
           "un reato (DPR 445/2000, art. 76).</p>"]
    for i in items:
        boxes = "".join(f"<li class='{'on' if b['ticked'] else ''}'>{'☑ già spuntata' if b['ticked'] else '☐'} "
                        f"{esc(b['label'])}</li>" for b in i["boxes"])
        out.append(f"<details open><summary>{esc(i['section'])}</summary><div class='decl'>{esc(i['text'])}"
                   + (f"<ul>{boxes}</ul>" if boxes else "") + "</div></details>")
    return "".join(out), checks


def preview(report, folder):
    """The portal's PDF preview of the draft (private/anteprima.pdf): pages as images when PyMuPDF is
    there, always a download. (html, checks)."""
    f = folder / "anteprima.pdf" if folder else None
    if not (f and f.exists()):
        return "", [("L'anteprima PDF del portale non è stata copiata: apra Visualizza anteprima nel portale e la "
                     "legga prima di firmare", False)]
    data = f.read_bytes()
    out = ["<h2>L'anteprima del portale</h2><p class='sub'>Il documento che il portale depositerà, così come lo mostra.</p>",
           f"<a class='dl' download='anteprima.pdf' href='data:application/pdf;base64,"
           f"{base64.b64encode(data).decode()}'>Scarica il PDF</a>"]
    try:
        import fitz  # noqa: PLC0415  (optional, as in fill.py)
        with fitz.open(stream=data, filetype="pdf") as doc:
            for n, pg in enumerate(doc):
                if n == 20:
                    out.append(f"<p class='sub'>Altre {len(doc) - 20} pagine nel PDF.</p>")
                    break
                png = pg.get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).tobytes("png")
                out.append(f"<img class='page' alt='pagina {n + 1}' src='data:image/png;base64,"
                           f"{base64.b64encode(png).decode()}'>")
    except Exception:
        out.append("<p class='sub'>(Apra il PDF per leggerlo.)</p>")
    return "".join(out), [("L'anteprima PDF del portale copiata", True)]


def check(out):
    """Claude's check of the portal's preview against the documents (OUT/check.json): (html, checks)."""
    f = out / "check.json" if out else None
    if not (f and f.exists()):
        return "", [("Anteprima del portale non ancora confrontata con i documenti", False)]
    c = json.loads(f.read_text())
    rows = c.get("rows", [])
    bad = [r for r in rows if not r.get("ok")]
    checks = [(f"Anteprima del portale confrontata con i documenti: {len(rows)} valori, tutti coincidono" if not bad
               else f"Anteprima del portale confrontata con i documenti: {len(bad)} valori su {len(rows)} da guardare",
               not bad and bool(rows))]
    if not rows:
        checks[0] = ("Anteprima del portale: nessun valore confrontato", False)
    out_ = ["<h2>Controllo con i documenti</h2><p class='sub'>Ogni valore come lo mostra l'anteprima del portale, "
            "il documento che riceverà il Comune, accanto a ciò che dice il documento da cui viene.</p>"]
    if bad:
        out_.append("<div class='you'><b>Da guardare</b><ul>" + "".join(
            f"<li>{esc(r.get('section'))}, {esc(r.get('label'))}: sul portale «{esc(r.get('portal'))}», "
            f"{esc(r.get('source') or 'nei documenti')} «{esc(r.get('document'))}»"
            + (f" ({esc(r['note'])})" if r.get("note") else "") + "</li>" for r in bad) + "</ul></div>")
    groups = {}
    for r in rows:
        groups.setdefault(r.get("section") or "", []).append(r)
    for name, rs in groups.items():
        out_.append(f"<details><summary>{esc(name)} ({sum(1 for r in rs if r.get('ok'))}/{len(rs)})</summary><table>"
                    + "".join(f"<tr><td>{'✓' if r.get('ok') else '✗'} {esc(r.get('label'))}</td><td>{esc(r.get('portal'))}"
                              f"<br><span class='blank'>{esc(r.get('source'))}"
                              + (f": «{esc(r.get('document'))}»" if r.get("document") != r.get("portal") else "")
                              + (f" · {esc(r['note'])}" if r.get("note") else "") + "</span></td></tr>" for r in rs)
                    + "</table></details>")
    missing = c.get("not_in_preview") or []
    if missing:
        out_.append("<p class='sub'>Non compaiono nell'anteprima del portale, e sono stati confrontati con ciò che la "
                    "compilazione ha scritto e riletto: " + esc("; ".join(missing)) + ".</p>")
    return "".join(out_), checks


def attachments(out, job):
    """The draft's files as the portal holds them (OUT/portal-files.json), each matched by its bytes
    to a file of the job: (html, checks)."""
    f = out / "portal-files.json" if out else None
    if not (f and f.exists()):
        return "", [("Allegati non riscaricati dal portale per il confronto", False)]
    files = json.loads(f.read_text()).get("files", [])
    local = {}
    for p in sorted(job.rglob("*")) if job else []:
        if p.is_file() and out not in p.parents and p.stat().st_size <= 50 * 2**20:
            local.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(), p.relative_to(job).as_posix())
    rows, bad = [], 0
    for x in files:
        same = local.get(x.get("sha256"))
        bad += not same
        rows.append(f"<tr><td>{'✓' if same else '✗'} {esc(x.get('slot'))}</td><td>{esc(x.get('name'))}<br>"
                    f"<span class='blank'>{'uguale byte per byte a ' + esc(same) if same else 'nessun file del lavoro ha questi byte'}"
                    "</span></td></tr>")
    checks = [(f"Allegati: {len(files)} file sul portale, ognuno uguale byte per byte a un file del lavoro" if files and not bad
               else "Allegati: nessun file sul portale" if not files
               else f"Allegati: {bad} file sul portale diversi da ogni file del lavoro", bool(files) and not bad)]
    return ("<h2>Gli allegati sul portale</h2><p class='sub'>Riscaricati dal portale e confrontati con i file del "
            "lavoro.</p><details open><summary>Allegati</summary><table>" + "".join(rows) + "</table></details>"), checks


def portal_review(report, out=None, job=None):
    ok = report.get("result") == "filled"
    # The runner's own reasons are for Claude, who recovers a stop; the person reads where.
    checks = [(f"{s['section']}: salvata, ogni campo riletto ({s['seconds']} s)"
               if not s["errors"] and not s["bad"] else f"{s['section']}: un valore non è rimasto come doveva",
               not s["errors"] and not s["bad"]) for s in report.get("sections", [])]
    if report.get("wizard_seconds") is not None:
        checks.insert(0, (f"Procedura guidata: ogni schermata confermata ({report['wizard_seconds']} s)", True))
    if report.get("verify_seconds") is not None:
        checks.append((f"Bozza riaperta dal portale: ogni valore è ancora lì ({report['verify_seconds']} s)"
                       if ok else "Bozza riaperta dal portale: un valore non è rimasto", ok))
    if report.get("error"):
        checks.append(("La compilazione si è fermata prima della fine: Claude sa dove e perché", False))
    # The portal's warnings beside boxes it kept (inpage.js alerts()): the person checks each.
    for a in report.get("alerts", []):
        checks.append((f"{a['section']}, {a.get('label') or 'una casella'}: il portale segnala «{a['text']}» (valore salvato: lo controlli)", False))
    # The report says only why a read-back failed; the person sees what it wanted and found.
    for d in report.get("details", []):
        checks.append((f"{d['section']}, {d['label']}: doveva essere «{d['want']}», il portale ha «{d['got']}»", False))
    groups = {}
    for v in report.get("values", []):
        groups.setdefault(v["section"], []).append((v["label"], v["value"], False))
    folder = out / "private" if out else None
    # A stopped run hasn't reached either, so it says nothing about them.
    decl_html, decl_checks = declarations(report, folder) if ok else ("", [])
    prev_html, prev_checks = preview(report, folder) if ok else ("", [])
    check_html, check_checks = check(out) if ok else ("", [])
    files_html, files_checks = attachments(out, job) if ok else ("", [])
    if out and (out / "check.json").exists():
        prev_checks = []  # the preview was read and checked: that line says more than "not copied"
    checks += check_checks + files_checks + decl_checks + prev_checks
    return page(report.get("title") or report["procedure"], "Bozza sul portale", ok,
                f"Bozza salvata in {report.get('total_seconds')} s: pronta da rivedere" if ok
                else "Si è fermata prima della fine", report.get("yours", []), [("Bozza", report.get("url"))],
                checks, list(groups.items()), prev_html, check_html + files_html + decisions(report) + decl_html)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--route", type=Path)
    ap.add_argument("--job", type=Path, help="the job's folder, whose files the portal's are matched to "
                    "(default: OUT's parent)")
    a = ap.parse_args()
    report = json.loads((a.out / "report.json").read_text())
    shown = a.out / "private" / "shown.json"  # run.py page: the pane's report has only the run
    if shown.exists():
        report |= json.loads(shown.read_text())
    route = json.loads(a.route.read_text()) if a.route else None
    job = (a.job or a.out.resolve().parent).resolve()
    doc = form_review(a.out, report, route) if "rows" in report else portal_review(report, a.out.resolve(), job)
    (a.out / "review.html").write_text(doc, encoding="utf-8")
    print(a.out / "review.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
