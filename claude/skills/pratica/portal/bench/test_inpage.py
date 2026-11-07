#!/usr/bin/env python3
"""Offline tests of inpage.js on a fake portal: no network, no vault, no model.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_inpage.py

A local server plays the portal (portal.html, an attachments screen): it stores what Salva
and the upload boxes send and shows it again on every load, so the runner's fresh load of
the draft reads what the "portal" kept. Each case runs run.py's page scripts in headless
Chromium, as the browser pane runs them, and checks the report and the bytes that arrived.
"""

import base64
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import threading
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
import run  # noqa: E402
import yaml  # noqa: E402


DEN, IMPRESA = "form:r0c1:dynaForm:den_txt", "form:r4c1:dynaForm:impresa_txt"


class Portal:
    """What the fake portal stored. drop: it shows Denominazione after Salva but never stores it.
    slow: the next that many loads of ?flaky=1 come without the second section's box, as
    the real portal sometimes shows a section before its boxes. bounce: the draft's second load
    passes through another origin (localhost for 127.0.0.1) and back, as the portal's sign-in
    can (2026-11-03)."""

    def reset(self, drop=False, slow=0, bounce=False):
        self.fields, self.files, self.drop, self.sent, self.slow = {}, [], drop, False, slow
        self.bounce, self.loads = bounce, 0


PORTAL = Portal()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, body, ctype="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self.send(b"<!doctype html><title>bench</title>", "text/html")
        elif path == "/portal.html":
            PORTAL.loads += 1
            if PORTAL.bounce and PORTAL.loads == 2:
                port = self.server.server_port
                self.send_response(302)
                self.send_header("Location", f"http://localhost:{port}/sso?back=" + quote(f"http://127.0.0.1:{port}{self.path}", safe=""))
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            html = (HERE / "portal.html").read_bytes()
            if "flaky=1" in self.path and PORTAL.slow > 0:
                PORTAL.slow -= 1
                html = html.replace(b'<tr><td><label class="labelDynaFormControl" id="impresa-label">Impresa esecutrice</label></td>\n'
                                    b'        <td><input type="text" id="form:r4c1:dynaForm:impresa_txt"></td></tr>', b"")
                assert b"impresa_txt" not in html, "the bench page changed: update the flaky cut"
            self.send(html, "text/html; charset=utf-8")
        elif path == "/fnsuap/cmd/home":  # Pratiche in bozza: one draft, opened on its attachments
            self.send(b"<!doctype html><title>Bozze</title><table><tr><td>PROVA NON INVIARE - seconda</td>"
                      b"<td><a title='Apri' href='/portal.html?screens=1&more=1'>APRI</a></td></tr></table>", "text/html")
        elif path == "/sso":  # the sign-in's origin, sending the frame back, as an SSO does
            back = parse_qs(self.path.split("?", 1)[1])["back"][0]
            self.send(b"<!doctype html><title>SSO</title><script>setTimeout(() => location.replace("
                      + json.dumps(back).encode() + b"), 300)</script>", "text/html")
        elif path == "/login":  # where an expired sign-in lands (the portal's identity provider)
            self.send(b"<!doctype html><title>Accedi</title><p>Entra con SPID", "text/html")
        elif path == "/anteprima.pdf":
            self.send(b"%PDF-1.4\nl'anteprima del portale finto\n", "application/pdf")
        elif path == "/state":
            self.send(json.dumps({"fields": PORTAL.fields, "files": [f["name"] for f in PORTAL.files],
                                  "boxes": {f["box"]: f["name"] for f in PORTAL.files}}).encode())
        else:
            self.send_error(404)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/save":
            PORTAL.fields = json.loads(body)["fields"]
            if PORTAL.drop:
                PORTAL.fields.pop(DEN, None)
        elif self.path == "/upload":
            msg = BytesParser(policy=default).parsebytes(
                b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + body)
            for part in msg.iter_parts():
                data = part.get_payload(decode=True) or b""
                PORTAL.files.append({"name": part.get_filename(), "type": part.get_content_type(),
                                     "sha256": hashlib.sha256(data).hexdigest(),
                                     "box": part.get_param("name", header="content-disposition")})
        elif self.path == "/sent":
            PORTAL.sent = True
        self.send(b"{}")


def steps(base, start="/portal.html", **over):
    sec = {"section": "Allega documenti", "open": False, "fields": [
        {"id": "den_txt", "kind": "text", "label": "Denominazione", "value": "{{ask.den}}"},
        {"id": "planimetria_input", "kind": "file", "label": "Planimetria quotata", "value": "{{ask.planimetria}}"},
        {"id": "ricevuta_input", "kind": "file", "label": "Ricevuta ASL", "value": "{{ask.ricevuta}}"},
    ]} | over
    tecnici = {"section": "Dati tecnici", "fields": [
        {"id": "impresa_txt", "kind": "text", "label": "Impresa esecutrice", "value": "{{ask.impresa}}"}]}
    return {"procedure": "test/allegati", "start": base + start, "logged_in": base + "/", "wizard": [],
            "sections": [sec, tecnici]}


FILES = "[data-pv=files] input[type=file]:not([webkitdirectory])"


def fill(browser, base, st, answers, files_limit=None, resume=None, sizes=None, held=None, pick=None):
    """pick: the files the person chooses in the page's box (a second run's are always picked)."""
    values = run.Values(answers, fields={"x:ruolo.tipo": "titolare"})
    install, run_js = run.page_scripts(st, values, files_limit, resume=resume)
    if sizes is not None:
        sizes.append(len(run_js))
    page = browser.new_page()
    try:
        page.goto(base + "/")
        page.evaluate(install)
        page.evaluate(run_js)
        if pick:
            page.wait_for_selector(FILES, state="attached")
            page.set_input_files(FILES, [str(p) for p in pick])
        while (report := page.evaluate("__pv.wait(5000)"))["result"] == "running":
            pass
        if held is not None:  # what the report leaves out, as run.py reads it for the person
            held.append(page.evaluate("__pv.held()"))
        return report
    finally:
        page.close()


def type_code(page, code):
    """The person types the code into the box the runner opened."""
    page.wait_for_selector('[data-pv="code"] input')
    page.fill('[data-pv="code"] input', code)


def settle(page):
    """Polls as the skill does, until the run is neither running nor waiting for the code."""
    while (report := page.evaluate("__pv.wait(5000)"))["result"] in ("running", "waiting"):
        pass
    return report


def main():
    from playwright.sync_api import sync_playwright
    tmp = Path(tempfile.mkdtemp(prefix="inpage-bench-"))
    planimetria, ricevuta = tmp / "planimetria.pdf", tmp / "ricevuta-asl.pdf.p7m"
    planimetria.write_bytes(b"%PDF-1.4\n" + os.urandom(3 * 1024 * 1024))
    ricevuta.write_bytes(b"finta ricevuta firmata\n")
    sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (planimetria, ricevuta)}
    answers = {"den": "PIZZERIA FITTIZIA DI GENNARO FITTIZIO", "planimetria": str(planimetria),
               "ricevuta": str(ricevuta), "impresa": "EDIL FITTIZIA DI MARCO ESEMPIO"}
    # What the pane can carry (256 KB of files at most), for the sealed runs that stop and resume:
    # the tab keeps the sealed values in sessionStorage, which a 3 MB drawing would overflow.
    tiny = tmp / "tiny.pdf"
    tiny.write_bytes(b"%PDF-1.4 tiny\n")
    small = answers | {"planimetria": str(tiny), "ricevuta": str(tiny)}
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    failed, ran = [], []

    def case(name, check):
        ran.append(name)
        try:
            check()
            print(f"ok    {name}")
        except AssertionError as e:
            failed.append(name)
            print(f"FAIL  {name}: {e}")

    def stops(report, words):
        assert report["result"] == "stopped", f"result {report['result']}"
        assert words in report.get("error", ""), f"error {report.get('error')!r}"
        assert not PORTAL.sent, "Firma e invio was clicked"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        def kept():
            PORTAL.reset()
            r = fill(browser, base, steps(base), answers)
            assert r["result"] == "filled", r.get("error")
            assert r.get("verify_seconds") is not None, "no fresh load of the draft"
            assert PORTAL.fields.get(DEN) == answers["den"], f"stored {PORTAL.fields}"
            assert PORTAL.fields.get(IMPRESA) == answers["impresa"], f"stored {PORTAL.fields}"
            got = {f["name"]: f["sha256"] for f in PORTAL.files}
            assert got == sha, f"received {got}"
            assert {f["type"] for f in PORTAL.files} == {"application/pdf", "application/pkcs7-mime"}
            assert not PORTAL.sent, "Firma e invio was clicked"
        case("fills, attaches 3 MB byte-exact, and the fresh load finds it all", kept)

        def dropped():
            PORTAL.reset(drop=True)
            stops(fill(browser, base, steps(base), answers), "fresh load of the draft: not kept")
        case("a value the portal shows but never stores stops the run", dropped)

        def wrong_label():
            PORTAL.reset()
            st = steps(base)
            st["sections"][0]["fields"][2]["label"] = "Visura camerale"
            stops(fill(browser, base, st, answers), "expected the label Visura camerale")
        case("a file box with another label stops the run", wrong_label)

        def moved_id():
            # An id that names another box now (an earlier choice shifted the rows) goes by
            # its label: each file lands in the box its label names, and the report says so.
            PORTAL.reset()
            st = steps(base)
            f = st["sections"][0]["fields"]
            f[1]["id"], f[2]["id"] = f[2]["id"], f[1]["id"]
            r = fill(browser, base, st, answers)
            assert r["result"] == "filled", r.get("error")
            boxes = {f["box"]: f["name"] for f in PORTAL.files}
            assert boxes.get("form:r1c1:dynaForm:planimetria_input") == planimetria.name, boxes
            assert boxes.get("form:r2c1:dynaForm:ricevuta_input") == ricevuta.name, boxes
            assert [m["label"] for m in r.get("moved", [])] == ["Planimetria quotata", "Ricevuta ASL"], r.get("moved")
            assert "loose" not in r, r.get("loose")
        case("an id that names another box now goes by its label, and the report names the move", moved_id)

        def signed_out():
            # The sign-in expired: the frame lands on a login page. The run says so, not "busy".
            PORTAL.reset()
            st = steps(base)
            st["sections"][1]["open"] = False
            r = fill(browser, base, {**st, "start": base + "/login"}, answers)
            assert r["result"] == "stopped" and r["error"].startswith("signed out"), r.get("error")
            assert not r.get("retries"), r.get("retries")
        case("an expired sign-in stops the run saying so, not as the portal staying busy", signed_out)

        def sso_bounce():
            # The fresh load of the draft passes through the sign-in's origin and back: the run
            # waits for the portal again instead of stopping on "Blocked a frame with origin".
            PORTAL.reset(bounce=True)
            r = fill(browser, base, steps(base), answers)
            assert r["result"] == "filled", r.get("error")
            assert PORTAL.loads >= 3, f"no bounce: {PORTAL.loads} loads"
            assert r.get("verify_seconds") is not None, "no fresh load of the draft"
        case("a load that passes through another origin and back is waited for, not a stop", sso_bounce)

        def anchored():
            # A block's start is a box the anchor is the own label of: the "(specificare)" box
            # beside a tick box reads it as its cell before, and must not start a block itself.
            PORTAL.reset()
            st = steps(base, start="/portal.html?deroga=1")
            st["sections"][1]["fields"] += [
                {"kind": "checkbox", "label": "alla densità edilizia"},
                {"kind": "text", "label": "(specificare)", "anchor": "alla densità edilizia", "value": "{{ask.den}}"},
                {"kind": "checkbox", "label": "all'altezza"},
                {"kind": "text", "label": "(specificare)", "anchor": "all'altezza", "value": "{{ask.impresa}}"}]
            r = fill(browser, base, st, answers)
            assert r["result"] == "filled", r.get("error")
            assert PORTAL.fields.get("form:r5c2:dynaForm:dens_txt") == answers["den"], PORTAL.fields
            assert PORTAL.fields.get("form:r5c2:dynaForm:alt_txt") == answers["impresa"], PORTAL.fields
        case("a box beside an anchor's tick box, labelled by it from the cell before, doesn't start a block", anchored)

        def two_lists():
            # Two lists in one section, each with its "+" after its rows: a block of the first is
            # added by the first "+", not the page's last. The second list is a template, as
            # gen.py writes one (an `add` with `each`, its fields with `block: "#N"`), three rows
            # by its count.
            PORTAL.reset()
            st = steps(base, start="/portal.html?liste=1")
            st["sections"][1]["fields"] += [
                {"kind": "text", "label": "Comunicazioni", "anchor": "Comunicazioni", "block": 1, "value": "{{ask.den}}"},
                {"kind": "add", "anchor": "Comunicazioni", "block": 2},
                {"kind": "text", "label": "Comunicazioni", "anchor": "Comunicazioni", "block": 2, "value": "{{ask.impresa}}"},
                {"kind": "text", "label": "Tipologia di atto", "anchor": "Tipologia di atto", "block": 1, "value": "{{ask.atto_1}}"},
                {"kind": "add", "anchor": "Tipologia di atto", "block": "#N", "each": {"count": "{{ask.atti}}", "from": 2}},
                {"kind": "text", "label": "Tipologia di atto", "anchor": "Tipologia di atto", "block": "#N", "value": "{{ask.atto_#K}}"}]
            r = fill(browser, base, st, answers | {"atti": "3", "atto_1": "uno", "atto_2": "due", "atto_3": "tre"})
            assert r["result"] == "filled", r.get("error")
            got = {k.split(":")[-1]: v for k, v in PORTAL.fields.items() if ":dynaForm:" in k and k.endswith(("com1_txt", "com2_txt")) or "atto" in k}
            assert got == {"com1_txt": answers["den"], "com2_txt": answers["impresa"], "atto1_txt": "uno", "atto2_txt": "due", "atto3_txt": "tre"}, got
        case("two lists in a section: each \"+\" adds to its own list, as many rows as the count says", two_lists)

        def cadastral_units():
            # Dati catastali (2026-11-04): two units by the unit's "+", never the group's after it;
            # the subalterno found by its title, since by label "subalterno" another box ties with it.
            def unit(n, sub_label):
                block = n if n == 1 else "#N"
                return [{"kind": "text", "label": "foglio", "anchor": "foglio", "block": block, "value": "{{ask.fog_#K}}"},
                        {"kind": "text", "label": "particella/mappale", "anchor": "foglio", "block": block, "value": "{{ask.par_#K}}"},
                        {"kind": "text", "label": sub_label, "anchor": "foglio", "block": block, "value": "{{ask.sub_#K}}"}]
            vals = {"unita": "2", "fog_1": "12", "par_1": "345", "sub_1": "7", "fog_2": "12", "par_2": "345", "sub_2": "8"}

            def run_with(sub_label):
                PORTAL.reset()
                st = steps(base, start="/portal.html?catasto=1")
                st["sections"][1]["fields"] += [*run.nth_block(unit(1, sub_label), 1),
                                                 {"kind": "add", "anchor": "foglio", "block": "#N", "each": {"count": "{{ask.unita}}", "from": 2}},
                                                 *unit(2, sub_label)]
                return fill(browser, base, st, answers | vals)
            r = run_with("se non presente indicare il numero 0")
            assert r["result"] == "filled", r.get("error")
            got = {k.split(":")[-1]: v for k, v in PORTAL.fields.items() if ":dynaForm:cat" in k and "_" in k and v != "on"}
            assert got == {"cat1g1_fog": "12", "cat1g1_par": "345", "cat1g1_sub": "7", "cat2g1_fog": "12", "cat2g1_par": "345", "cat2g1_sub": "8"}, got
            assert not any("catg2" in k for k in PORTAL.fields), "pressed the group's +"
            # By the label the crawl gives it, the subalterno lands in another box: never filled.
            r = run_with("subalterno")
            assert r["result"] != "filled", "the subalterno by label filled: the tie is gone, the title may not be needed"

            # A flat, then two plots: the group's "+" (the second after the last unit) where the
            # catasto changes, the new group's own NCT (the page's last: every radio reads NCEU or
            # NCT once a "+" has checked the section), and the
            # third unit by the first "+" after the second, which is now the second group's own.
            PORTAL.reset()
            st = steps(base, start="/portal.html?catasto=1")
            box = lambda label, n, v: {"kind": "text", "label": label, "anchor": "foglio", "block": n, "value": v}
            st["sections"][1]["fields"] += [
                # By id, as the steps file has it: after a "+" its long name is gone from the page.
                {"id": "catg1_nceu", "kind": "radio", "label": "Nuovo Catasto Edilizio Urbano"},
                box("foglio", 1, "12"), box("particella/mappale", 1, "678"), box("se non presente indicare il numero 0", 1, "3"),
                {"kind": "add", "anchor": "foglio", "block": 2, "nth": 2},
                {"kind": "radio", "label": "NCT", "last": True},
                box("foglio", 2, "12"), box("particella/mappale", 2, "679"),
                {"kind": "add", "anchor": "foglio", "block": 3},
                box("foglio", 3, "12"), box("particella/mappale", 3, "680")]
            r = fill(browser, base, st, answers)
            assert r["result"] == "filled", r.get("error")
            got = {k.split(":")[-1]: v for k, v in PORTAL.fields.items() if ":dynaForm:cat" in k}
            assert got == {"catg1_nceu": "on", "cat1g1_fog": "12", "cat1g1_par": "678", "cat1g1_sub": "3", "catg2_nct": "on",
                           "cat2g2_fog": "12", "cat2g2_par": "679", "cat2g2_sub": "", "cat3g2_fog": "12", "cat3g2_par": "680",
                           "cat3g2_sub": ""}, got

            # A flat, a plot, a garage: a third group back to the first catasto. The second group's
            # NCT is the page's last NCT when it's ticked, not once the third group is there: its
            # read-back goes to where it was (2026-11-05: "not kept NCT" on the portal, the third
            # group's NCT read in its place).
            PORTAL.reset()
            st = steps(base, start="/portal.html?catasto=1")
            st["sections"][1]["fields"] += [
                {"id": "catg1_nceu", "kind": "radio", "label": "Nuovo Catasto Edilizio Urbano"},
                box("foglio", 1, "12"), box("particella/mappale", 1, "678"), box("se non presente indicare il numero 0", 1, "3"),
                {"kind": "add", "anchor": "foglio", "block": 2, "nth": 2},
                {"kind": "radio", "label": "NCT", "last": True},
                box("foglio", 2, "12"), box("particella/mappale", 2, "679"),
                {"kind": "add", "anchor": "foglio", "block": 3, "nth": 2},
                {"kind": "radio", "label": "NCEU", "last": True},
                box("foglio", 3, "12"), box("particella/mappale", 3, "678"), box("se non presente indicare il numero 0", 3, "5")]
            r = fill(browser, base, st, answers)
            assert r["result"] == "filled", r.get("error")
            got = {k.split(":")[-1]: v for k, v in PORTAL.fields.items() if ":dynaForm:catg" in k}
            assert got == {"catg1_nceu": "on", "catg2_nct": "on", "catg3_nceu": "on"}, got
        case("cadastral units: each unit by its own \"+\", a new catasto by the group's, the subalterno by its title; three groups", cadastral_units)

        def crawl_reveals():
            # A choice that opens an employer's block repeating labels above it (Cognome, Via):
            # its boxes are revealed, counted per label, never read as the ones above moving.
            page = browser.new_page()
            try:
                page.goto(base + "/")
                page.evaluate((HERE.parent / "crawl.js").read_text())
                box = lambda i, label: {"id": i, "kind": "text", "label": label}
                before = [box("r9c1", "Cognome"), box("r23c1", "Via, Piazza, ecc."), box("r30c2", "si")]
                now = [box("r9c1", "Cognome"), box("r23c1", "Via, Piazza, ecc."), box("r30c2", "si"),
                       box("r36c1", "Ragione sociale"), box("r42c1", "Via, Piazza, ecc."), box("r45c1", "Cognome")]
                got = page.evaluate("([b, n]) => __crawl.revealed(b, n).map((f) => f.id)", [before, now])
                assert got == ["r36c1", "r42c1", "r45c1"], got
                # Two of a label before, three now, every id renumbered: the last one is the new box.
                moved = [box("a1", "N."), box("a2", "N.")]
                got = page.evaluate("([b, n]) => __crawl.revealed(b, n).map((f) => f.id)",
                                    [moved, [box("b1", "N."), box("b2", "N."), box("b3", "N.")]])
                assert got == ["b3"], got
                # A full store: the result stays in the tab (export.js saves it), the call says so.
                kept = page.evaluate("""() => { const real = Storage.prototype.setItem;
                    Storage.prototype.setItem = () => { throw new DOMException("full", "QuotaExceededError"); };
                    try { return [__crawl.save("crawl:op:prova", "{}"), window.__crawlUnsaved["crawl:op:prova"]]; }
                    finally { Storage.prototype.setItem = real; } }""")
                assert kept == [False, "{}"], kept
            finally:
                page.close()
        case("the crawl counts a revealed box whose label repeats one above it (an employer's address)", crawl_reveals)

        def banner():
            PORTAL.reset()
            stops(fill(browser, base, steps(base, start="/portal.html?banner=1"), answers), "covered by div#consenso")
        case("a consent banner over the form stops the run", banner)

        def switched_off():
            PORTAL.reset()
            stops(fill(browser, base, steps(base, start="/portal.html?off=1"), answers), "Impresa esecutrice: switched off")
        case("a box greyed until an earlier choice stops the run, named as switched off", switched_off)

        def radio_switched_off():
            PORTAL.reset()
            st = steps(base, start="/portal.html?offradio=1")
            st["sections"][1]["fields"].append({"id": "scomputo:radio:1_clone", "kind": "radio", "label": "NO"})
            stops(fill(browser, base, st, answers), "NO: switched off")
        case("a greyed radio, its drawn box under its wrapper, is named as switched off, not covered", radio_switched_off)

        def fading_list():
            PORTAL.reset()
            r = fill(browser, base, steps(base, start="/portal.html?fade=1"), answers)
            assert r["result"] == "filled", r
        case("a suggestion list still fading out over the next box is closed, not a stop", fading_list)

        def street_lookup():
            # The street's first word is its type, whatever it is: until 2026-11-04 only VIA,
            # VIALE, PIAZZA, CORSO and LARGO were, and a Vico (a third of Naples' streets aren't
            # those five) matched nothing in the list.
            VIA = "form:r11c1:dynaForm:via:txtws_input"
            for value, chosen in (("VICO LUNGO GELSO", "VICO LUNGO GELSO"), ("VIA GELSO", "VIA GELSO"),
                                  ("VIA FORIA", "VIA FORIA"), ("CUPA CAIAFA", "CUPA CAIAFA")):
                PORTAL.reset()
                st = steps(base, start="/portal.html?via=1")
                st["sections"][0]["fields"].insert(0, {"id": "via:txtws_input", "kind": "lookup",
                                                       "label": "Via, Viale, Piazza", "value": "{{ask.via}}"})
                r = fill(browser, base, st, answers | {"via": value})
                assert r["result"] == "filled", (value, r.get("error"))
                assert PORTAL.fields.get(VIA) == chosen, (value, PORTAL.fields.get(VIA))
        case("a street lookup takes a street of any type (a Vico, a Cupa), and the exact one among similar", street_lookup)

        def calendar_left_open():
            # A typed date leaves the calendar open over the next box; a person's click elsewhere
            # would close it, so the runner does (the permesso's sanatoria quadro, 2026-11-02).
            PORTAL.reset()
            r = fill(browser, base, steps(base, start="/portal.html?calendar=1"), answers)
            assert r["result"] == "filled", r
        case("a calendar a typed date left open over the next box is closed, not a stop", calendar_left_open)

        def signed_slot():
            # The portal's "required" under a slot that takes only signed files is the person's;
            # under a plain one it stops the run, and the snapshot names the slot by its title.
            PORTAL.reset()
            r = fill(browser, base, steps(base, start="/portal.html?slot=signed"), answers)
            assert r["result"] == "filled", r
            PORTAL.reset()
            r = fill(browser, base, steps(base, start="/portal.html?slot=plain"), answers)
            assert r["result"] == "stopped" and "obbligatorio" in r["error"], r
            box = next(b for b in r["snapshot"]["boxes"] if b["id"] == "procura_input")
            # A box the portal flags reads by its label, not by the message, and says it's required.
            PORTAL.reset()
            r2 = fill(browser, base, steps(base, start="/portal.html?slot=plain&req=1"), answers)
            rs = next(b for b in r2["snapshot"]["boxes"] if b["id"] == "rs_txt")
            assert rs["label"] == "ragione sociale" and rs.get("required") and rs["state"] == "empty", rs
            assert box["label"] == "procura speciale" and box["required"] and box["accepts"] == "pdf;pdf.p7m", box
            assert box["state"] == "empty", box
            # A slot the portal hasn't flagged: named by its title, not its wrapper's "false"; not
            # required for the "OBBLIGATORIO" in its title; filled, since its cell names a file.
            held = next(b for b in r["snapshot"]["boxes"] if b["id"] == "fibra_input")
            assert held["label"].startswith("elaborato dimostrativo della fibra") and not held.get("required") \
                and held["state"] == "filled", held
            assert ".pdf" not in json.dumps(r["snapshot"]), "a file's name in the snapshot"
        case("a required slot taking only signed files is the person's; a plain one stops, named by its title", signed_slot)

        def refused_upload():
            # A file the portal refuses on upload (a made-up digital signature, 2026-11-03) shows
            # only in a growl that fades: the run stops on it, naming the slot and the portal's words.
            PORTAL.reset()
            r = fill(browser, base, steps(base, start="/portal.html?refuse=1"), answers)
            stops(r, "Ricevuta ASL: the portal refused")
            assert "firme digitali" in r["error"] and "ricevuta-asl" not in json.dumps(PORTAL.files), r
        case("a file the portal refuses on upload, in a growl that fades, stops the run with its words", refused_upload)

        def after_declarations():
            # The second run: the first two sections' fields stay as filled, the attachments
            # screen is reached from the menu's step on a reopened draft, and only what waits
            # for the declarations is attached.
            PORTAL.reset()
            st = steps(base, start="/portal.html?screens=1")
            st["sections"][1]["fields"][0]["after_declarations"] = True  # not on a go screen: kept
            go = {"section": "Gestione degli allegati", "go": "Prosegui", "step": "Allega Documenti", "fields": [
                {"id": "planimetria_input", "kind": "file", "label": "Planimetria quotata", "value": "{{ask.planimetria}}"},
                {"id": "ricevuta_input", "kind": "file", "label": "Ricevuta ASL", "value": "{{ask.ricevuta}}",
                 "accepts": "pdf.p7m", "after_declarations": True}]}
            st["sections"].append(go)
            first, second = run.phase(st), run.phase(st, after=True)
            assert [f["label"] for f in first["sections"][2]["fields"]] == ["Planimetria quotata"]
            assert [f["label"] for f in second["sections"][2]["fields"]] == ["Ricevuta ASL"]
            assert len(second["sections"][1]["fields"]) == 1, "a section before the screens lost a field"
            assert run.reopening(second)["from"] == {"section": 2}
            assert not run.phase(st, after=True, made_up=True)["sections"][2]["fields"], "made-up: a signed-only slot kept"
            r = fill(browser, base, second, small, resume={"url": base + "/portal.html?screens=1", "from": {"section": 2}})
            assert r["result"] == "filled", r
            assert [f["box"].rsplit(":", 1)[-1] for f in PORTAL.files] == ["ricevuta_input"], PORTAL.files
        case("the second run reaches the attachments screen by its step and attaches only what waited", after_declarations)

        def after_declarations_reopened():
            # The second run as run.py starts it: the draft by its name from Pratiche in bozza, then
            # Allegati liberi, whose first box the first run filled: the file goes in a new box ("+").
            PORTAL.reset()
            PORTAL.files.append({"name": "relazione-tecnica.pdf", "type": "application/pdf", "sha256": "",
                                 "box": "form:r21c1:dynaForm:liberi1_input"})
            st = {"procedure": "test/seconda", "start": base + "/portal.html", "logged_in": base + "/", "wizard": [],
                  "sections": [{"section": "Gestione degli allegati", "go": "Prosegui", "step": "Allega Documenti",
                                "fields": [{"kind": "file", "label": "Allegati liberi", "value": "{{ask.ricevuta}}",
                                            "describe": "Allegato A", "after_declarations": True},
                                           {"kind": "file", "label": "Allegati liberi", "value": "{{ask.planimetria}}",
                                            "describe": "Modello DP", "after_declarations": True}]}]}
            dp = tmp / "modello-dp.pdf"
            dp.write_bytes(b"%PDF-1.4 dp\n")
            two = small | {"planimetria": str(dp)}
            r = fill(browser, base, st, two, resume={"reopen": "PROVA NON INVIARE - seconda", "from": {"section": 0}},
                     pick=[tiny, dp])
            assert r["result"] == "filled", r
            boxes = [f["box"].rsplit(":", 1)[-1] for f in PORTAL.files]
            # Each its own new box: the second never replaces the first (an upload into a box that
            # holds a file replaces it, on the portal).
            assert boxes == ["liberi1_input", "liberi2_input", "liberi3_input"], boxes
            # The same run again (a retry after a stop): what is there already is left, nothing twice.
            r = fill(browser, base, st, two, resume={"reopen": "PROVA NON INVIARE - seconda", "from": {"section": 0}},
                     pick=[tiny, dp])
            assert r["result"] == "filled" and len(PORTAL.files) == 3, (r, PORTAL.files)
        case("the second run reopens the draft by its name and takes a slot's next empty box", after_declarations_reopened)

        def second_run_carries_nothing():
            # One code a pratica: the second run's run.js carries none of the first run's values,
            # isn't sealed, and names its files only (picked in the page, never in the conversation).
            st = steps(base, start="/portal.html?screens=1")
            st["sections"].append({"section": "Gestione degli allegati", "go": "Prosegui", "step": "Allega Documenti",
                                   "fields": [{"id": "ricevuta_input", "kind": "file", "label": "Ricevuta ASL",
                                               "value": "{{ask.ricevuta}}", "after_declarations": True}]})
            second = run.phase(st, after=True)
            values = run.Values(small, fields={"x:ruolo.tipo": "titolare"})
            run_js = run.page_files(second, values, resume=run.reopening(second))["run.js"]
            assert small["den"] not in run_js and small["impresa"] not in run_js, run_js
            assert "startSealed" not in run_js and '"picked":true' in run_js, run_js
            assert base64.b64encode(tiny.read_bytes()).decode() not in run_js, "a file's bytes in run.js"
        case("the second run carries no value and no file's bytes, so it needs no code", second_run_carries_nothing)

        def twin_slots():
            # The screen's `theirs` names the signed-only "Relazione Paesaggistica Semplificata";
            # the plain slot whose title starts with it is Claude's: left empty, it stops the run.
            # The attachments screen alone: on this one-page portal a later section would see the message too.
            PORTAL.reset()
            st = steps(base, start="/portal.html?twins=1", theirs=["Relazione Paesaggistica Semplificata"])
            st["sections"] = st["sections"][:1]
            r = fill(browser, base, st, answers)
            assert r["result"] == "stopped" and r["error"].startswith("Allega documenti") and "obbligatorio" in r["error"], r
        case("a person's slot whose title starts another's covers only its own: the other, empty and required, stops", twin_slots)

        def flagged():
            # The portal's warning beside a box it kept ("Indirizzo Pec non valido"; "Indirizzo
            # sconosciuto" under every address): never a stop, listed by section and the box's label,
            # no value. The attachments section alone: the warning is page-wide on this fake page.
            st = steps(base, start="/portal.html?pec=1")
            st["sections"] = st["sections"][:1]
            st["sections"][0]["fields"].append({"id": "pec_txt", "kind": "text", "label": "Posta elettronica certificata",
                                               "value": "{{ask.pec}}"})
            PORTAL.reset()
            r = fill(browser, base, st, {**answers, "pec": "prova@pec.example.it"})
            assert r["result"] == "filled", r
            assert r["alerts"] == [{"section": "Allega documenti", "label": "Posta elettronica certificata",
                                    "text": "Indirizzo Pec non valido"}], r
            assert "pec.example" not in json.dumps(r), "a value in the report"
        case("the portal's warning beside a box it kept is reported, by label and without the value, never a stop", flagged)

        def more_files():
            # A slot named again takes its next box: its "+" adds one with no label under the last
            # (the portal's Allegati liberi, 2026-11-03); each file goes in its own box, described,
            # the fresh load finds them all by name, and a file a case doesn't attach takes no box.
            extra, third = tmp / "autorizzazione.pdf", tmp / "comunicazioni.pdf"
            extra.write_bytes(b"%PDF-1.4 autorizzazione\n")
            third.write_bytes(b"%PDF-1.4 comunicazioni\n")
            st = steps(base, start="/portal.html?more=1")
            st["sections"] = st["sections"][:1]
            st["sections"][0]["fields"] += [
                {"kind": "file", "label": "Allegati liberi", "value": "{{ask.rel}}", "describe": "Relazione tecnica"},
                {"kind": "file", "label": "Allegati liberi", "value": "{{ask.none}}", "describe": "Nulla", "optional": True},
                {"kind": "file", "label": "Allegati liberi", "value": "{{ask.extra}}", "describe": "Autorizzazione"},
                {"kind": "file", "label": "Allegati liberi", "value": "{{ask.third}}", "describe": "Comunicazioni"}]
            PORTAL.reset()
            r = fill(browser, base, st, {**small, "rel": str(tiny), "extra": str(extra), "third": str(third)})
            assert r["result"] == "filled", r.get("error")
            boxes = {f["box"]: f["name"] for f in PORTAL.files}
            assert [boxes.get(f"form:r2{n}c1:dynaForm:liberi{n}_input") for n in (1, 2, 3)] == \
                ["tiny.pdf", "autorizzazione.pdf", "comunicazioni.pdf"], boxes
            got = {k: v for k, v in PORTAL.fields.items() if k.endswith("_desc")}
            assert got == {f"form:r2{n}c1:dynaForm:liberi{n}_desc": d for n, d in
                           ((1, "Relazione tecnica"), (2, "Autorizzazione"), (3, "Comunicazioni"))}, got
            assert "loose" not in r and "moved" not in r, (r.get("loose"), r.get("moved"))
        case("a slot named again takes its next box: its + adds each, each described, all kept", more_files)

        def theirs():
            PORTAL.reset()
            stops(fill(browser, base, steps(base, save="Firma e invio"), answers), "refused to click")
        case("the person's Firma e invio is never clicked", theirs)

        decl_start = "/portal.html?decl=1"

        def declarations_read():
            PORTAL.reset()
            held = []
            r = fill(browser, base, steps(base, start=decl_start), answers, held=held)
            assert r["result"] == "filled", r.get("error")
            assert r["declarations_read"] == 1 and "declarations_note" not in r, r
            d = held[0]["declarations"]
            assert len(d) == 1 and "consapevolezza" in d[0]["section"], d
            assert "dichiara quanto segue" in d[0]["text"] and "art. 76" in d[0]["text"], d[0]["text"]
            assert d[0]["boxes"] == [{"label": "Per presa visione", "kind": "checkbox", "ticked": False},
                                     {"label": "che i locali possiedono i requisiti di sorvegliabilità", "kind": "radio",
                                      "ticked": False}], d[0]["boxes"]  # one radio, not its clone, with its own label
            assert "SALVA" not in d[0]["text"], d[0]["text"]
            assert "sanzioni penali" not in json.dumps(r), "the report carries the declaration's own text"
            assert not PORTAL.sent, "Firma e invio was clicked"
        case("the declarations' own text is copied into held(), ticked by nothing, and not into the report", declarations_read)

        def declarations_already_ticked():
            PORTAL.reset()
            held = []
            r = fill(browser, base, steps(base, start=decl_start + "&ticked=1"), answers, held=held)
            assert r["result"] == "filled", r.get("error")
            assert held[0]["declarations"][0]["boxes"][0]["ticked"] is True, held[0]["declarations"]
        case("a declaration the portal already shows ticked is reported as ticked", declarations_already_ticked)

        def declarations_stuck():
            PORTAL.reset()
            held = []
            r = fill(browser, base, steps(base, start=decl_start + "&stuck=1"), answers, held=held)
            assert r["result"] == "filled", f"a declaration that won't open stopped the run: {r.get('error')}"
            assert r["declarations_read"] == 0 and "didn't open" in r["declarations_note"], r
            assert held[0]["declarations"] == []
        case("a declarations section that won't open is a note, not a stop", declarations_stuck)

        def no_declarations():
            PORTAL.reset()
            held = []
            r = fill(browser, base, steps(base), answers, held=held)
            assert r["result"] == "filled" and r["declarations_read"] == 0 and held[0]["declarations"] == [], r
        case("a portal with no declarations in its menu reads none", no_declarations)

        def preview_copied():
            PORTAL.reset()
            values = run.Values(answers, fields={"x:ruolo.tipo": "titolare"})
            st = steps(base, start=decl_start) | {"preview_url": "/anteprima.pdf"}
            install, run_js = run.page_scripts(st, values, None)
            folder = tmp / "preview"
            folder.mkdir(exist_ok=True)
            (folder / "anteprima.pdf").unlink(missing_ok=True)
            page = browser.new_page()
            try:
                page.goto(base + "/")
                page.evaluate(install)
                page.evaluate(run_js)
                while (report := page.evaluate("__pv.wait(5000)"))["result"] == "running":
                    pass
                assert report["result"] == "filled", report.get("error")
                assert report["preview_pdf"] is True and "preview_note" not in report, report
                ok, why = run.capture_preview(page, folder)
                assert ok, why
                assert (folder / "anteprima.pdf").read_bytes().startswith(b"%PDF-1.4\n"), "not the portal's PDF"
                assert (folder / "anteprima.pdf").stat().st_mode & 0o777 == 0o600
                assert page.query_selector('[data-pv="review"] iframe[src^="blob:"]'), "the preview isn't on the review"
                assert page.url.startswith(base + "/"), "the preview moved the page"
            finally:
                page.close()
        case("the portal's PDF is fetched with the person's session, kept private and shown on the review, with no navigation", preview_copied)

        def review_drawn():
            PORTAL.reset()
            values = run.Values(answers, fields={"x:ruolo.tipo": "titolare"})
            install, run_js = run.page_scripts(steps(base, start=decl_start), values, None)
            page = browser.new_page()
            try:
                page.goto(base + "/")
                page.evaluate(install)
                page.evaluate(run_js)
                while (report := page.evaluate("__pv.wait(5000)"))["result"] == "running":
                    pass
                assert report["result"] == "filled", report.get("error")
                inside = "document.querySelector('[data-pv=review]').shadowRoot"  # drawn in a shadow root
                text = page.evaluate(f"{inside}.firstElementChild.nextElementSibling.innerText")
                assert "Bozza salvata sul portale" in text and "nulla è stato dichiarato" in text.lower(), text[:200]
                english = re.findall(r"\b(the|your|you|and|was|draft|saved|every|value|declarations?|show|download)\b", text, re.I)
                assert not english, f"English on the review over the portal: {sorted(set(english))}"
                assert "dichiara quanto segue" in text and "Per presa visione" in text, "the declaration isn't on the review"
                assert "che i locali possiedono i requisiti di sorvegliabilità" in text, "the radio's own label is missing"
                everything = page.evaluate(f"{inside}.textContent")  # the values sit in closed <details>
                assert answers["den"] in everything and answers["impresa"] in everything, "the values typed aren't on the review"
                assert "dichiara quanto segue" not in json.dumps(report), "the report carries the declaration"
                page.click("text=Mostra la bozza")
                assert page.query_selector('[data-pv="review"]') is None, "Mostra la bozza left the review up"
                page.evaluate("__pv.review()")
                assert page.query_selector('[data-pv="review"]'), "__pv.review() didn't draw it again"
            finally:
                page.close()
        case("a filled run draws the declarations and every value over the portal, none of it in the report", review_drawn)

        def preview_missing():
            PORTAL.reset()
            values = run.Values(answers, fields={"x:ruolo.tipo": "titolare"})
            install, run_js = run.page_scripts(steps(base), values, None)
            folder = tmp / "no-preview"
            folder.mkdir(exist_ok=True)
            page = browser.new_page()
            try:
                page.goto(base + "/")
                page.evaluate(install)
                page.evaluate(run_js)
                while (report := page.evaluate("__pv.wait(5000)"))["result"] == "running":
                    pass
                assert report["result"] == "filled", f"a missing preview stopped the run: {report.get('error')}"
                assert report["preview_pdf"] is False and "404" in report["preview_note"], report
                ok, why = run.capture_preview(page, folder)
                assert not ok and "no preview" in why, (ok, why)
                assert not (folder / "anteprima.pdf").exists()
                assert "Non sono riuscito a copiarla" in page.evaluate("document.querySelector('[data-pv=review]').shadowRoot.textContent"), \
                    "the review doesn't say it has no preview"
            finally:
                page.close()
        case("a portal that gives no preview is a note on the review, not a stop", preview_missing)


        def recovered():
            # The portal renamed a label: the run stops there and says so, keeping what the
            # first section typed; a fix for that one field resumes it on the same draft,
            # without redoing the first section, and the fresh load checks both.
            PORTAL.reset()
            st = steps(base, start="/portal.html?rename=1")
            h = []
            first = fill(browser, base, st, answers, held=h)
            assert first["result"] == "stopped" and "expected the label Impresa esecutrice" in first["error"], first
            at = first["at"]
            assert (at["phase"], at["index"], at["field"]) == ("section", 1, 0), at
            assert "kept" not in first, "the report carries what the sections typed"
            assert [k["section"] for k in h[0]["kept"]] == [0], h[0]["kept"]
            first = first | {"kept": h[0]["kept"]}  # run.py joins private/kept.json to report.json
            again = fill(browser, base, st, answers, resume=run.resumption(first))
            assert again["result"] == "stopped" and again["at"]["index"] == 1, "resumed without the fix and got past"
            fix = [{"section": 1, "field": 0, "set": {"label": "Ditta esecutrice"}}]
            done = fill(browser, base, st, answers, resume=run.resumption(first, fix))
            assert done["result"] == "filled", done.get("error")
            assert done["verify_seconds"] is not None and done["resumed"], done
            assert [s["section"] for s in done["sections"]] == ["Dati tecnici"], "redid a finished section"
            assert PORTAL.fields.get(DEN) == answers["den"] and PORTAL.fields.get(IMPRESA) == answers["impresa"], \
                PORTAL.fields
            assert len(PORTAL.files) == 2, f"uploaded {len(PORTAL.files)} files, not 2"
            assert not PORTAL.sent, "Firma e invio was clicked"
            out = tmp / "drift"
            out.mkdir()
            run.drift(out, st, run.resumption(first, fix))
            assert json.loads((out / "drift.json").read_text())["fixes"] == fix
        case("a renamed label stops in place; a fix resumes the same draft, checked end to end", recovered)

        def lost_before():
            # A resume whose fresh load finds an earlier section's value gone still stops.
            PORTAL.reset()
            st = steps(base, start="/portal.html?rename=1")
            h = []
            first = fill(browser, base, st, answers, held=h) | {}
            first["kept"] = h[0]["kept"]
            PORTAL.fields.pop(DEN, None)
            fix = [{"section": 1, "field": 0, "set": {"label": "Ditta esecutrice"}}]
            done = fill(browser, base, st, answers, resume=run.resumption(first, fix))
            stops(done, "fresh load of the draft: not kept")
        case("after a resume, a value lost from an earlier section is still caught", lost_before)

        def patched():
            # A steps file changed in one section: the patch sends that one and takes the others
            # from what the pane holds, storing the result only when it comes out byte for byte.
            key = "pv-steps:test/patch"
            dumps = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
            old = {"start": "x", "sections": [{"section": "A", "fields": [1]}, {"section": "Dati catastali", "fields": [2]}]}
            new = {"start": "x", "sections": [{"section": "A", "fields": [1]}, {"section": "Dati catastali", "fields": [2, 3]}]}
            js = run.patch_script(key, dumps(old), dumps(new), "steps/x.js")
            assert '"section":"A"' not in js, "sent a section the pane holds"
            assert run.patch_script(key, dumps(new), dumps(new), "steps/x.js") is None
            page = browser.new_page()
            try:
                page.goto(base + "/portal.html")
                put = lambda v: page.evaluate("([k, v]) => v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v)", [key, v])
                put(dumps(old))
                assert page.evaluate(js) == "installed"
                assert page.evaluate("(k) => localStorage.getItem(k)", key) == dumps(new)
                assert page.evaluate(js) == "stored already"
                put(dumps({**old, "sections": [{"section": "A", "fields": [9]}, old["sections"][1]]}))
                assert page.evaluate(js) == "the pane holds other steps: send steps/x.js"
                put(None)
                assert page.evaluate(js) == "send steps/x.js"
            finally:
                page.close()
        case("a patch sends only the changed sections, and stores nothing unless the whole matches", patched)

        def checked():
            # check.js names what the pane's storage lacks, byte for byte, and nothing once
            # install.js has run; a changed steps file makes only steps.js stale again.
            PORTAL.reset()
            values = run.Values(answers, fields={"x:ruolo.tipo": "titolare"})
            files = run.page_files(steps(base), values, files_limit=None)
            page = browser.new_page()
            try:
                page.goto(base + "/")
                page.evaluate("localStorage.clear()")
                assert page.evaluate(files["check.js"]) == "run runner.js, then steps.js, then run.js"
                page.evaluate(files["install.js"])
                assert page.evaluate(files["check.js"]) == "run run.js"
                other = steps(base)
                other["sections"][1]["fields"][0]["label"] = "Ditta esecutrice"
                again = run.page_files(other, values, files_limit=None)
                assert page.evaluate(again["check.js"]) == "run steps.js, then run.js"
                elsewhere = run.page_files(steps(base) | {"logged_in": "https://example.invalid/"}, values, files_limit=None)
                assert page.evaluate(elsewhere["check.js"]).startswith("go to https://example.invalid"), "wrong origin passed"
            finally:
                page.close()
        case("check.js says which of runner.js and steps.js the pane lacks", checked)

        def resumed_in_tab():
            # A stopped run's report and values stay in the tab: a reloaded runner resumes it
            # on the same draft with one fix, and one frame lies over the page, not two.
            PORTAL.reset()
            st = steps(base, start="/portal.html?rename=1")
            values = run.Values(answers, fields={"x:ruolo.tipo": "titolare"})
            install, run_js = run.page_scripts(st, values, files_limit=None)
            page = browser.new_page()
            try:
                page.goto(base + "/")
                page.evaluate(install)
                page.evaluate(run_js)
                while (first := page.evaluate("__pv.wait(5000)"))["result"] == "running":
                    pass
                assert first["result"] == "stopped", first
                page.evaluate("delete window.__pv; (0, eval)(localStorage.getItem('pv-runner'))")
                assert page.evaluate("__pv.last().result") == "stopped", "the report didn't outlive the runner"
                assert "kept" not in page.evaluate("__pv.last()"), "the stored report carries what the sections typed"
                page.evaluate('__pv.resume({fixes: [{section: 1, field: 0, set: {label: "Ditta esecutrice"}}]})')
                while (done := page.evaluate("__pv.wait(5000)"))["result"] == "running":
                    pass
                assert done["result"] == "filled" and done["resumed"], done.get("error")
                assert [x["section"] for x in done["sections"]] == ["Dati tecnici"], "redid a finished section"
                assert page.evaluate("document.querySelectorAll('iframe').length") == 1, "frames piled up"
                assert PORTAL.fields.get(IMPRESA) == answers["impresa"], PORTAL.fields
            finally:
                page.close()
        case("a stopped run resumes in the tab after the runner reloads, one frame at a time", resumed_in_tab)

        def hiccup():
            # The section shows without its box on the first load: the run picks itself up on
            # the same draft, without redoing the first section or its uploads.
            PORTAL.reset(slow=1)
            r = fill(browser, base, steps(base, start="/portal.html?flaky=1"), answers, resume={"retry_wait_ms": 100})
            assert r["result"] == "filled", r.get("error")
            assert len(r.get("retries", [])) == 1 and "fields with this label" in r["retries"][0]["error"], r.get("retries")
            assert r["verify_seconds"] is not None, "no fresh load of the draft"
            assert PORTAL.fields.get(IMPRESA) == answers["impresa"] and PORTAL.fields.get(DEN) == answers["den"], PORTAL.fields
            assert len(PORTAL.files) == 2, f"uploaded {len(PORTAL.files)} files, not 2"
            assert answers["impresa"] not in json.dumps(r), "a value in the report"
        case("a portal hiccup (a box not shown yet) resumes the same draft by itself, once", hiccup)

        def stubborn():
            # A box that never shows is retried twice, then the run stops and says so; a renamed
            # label (a real change) is never retried.
            PORTAL.reset(slow=99)
            r = fill(browser, base, steps(base, start="/portal.html?flaky=1"), answers, resume={"retry_wait_ms": 100})
            stops(r, "fields with this label")
            assert len(r.get("retries", [])) == 2, r.get("retries")
            PORTAL.reset()
            r = fill(browser, base, steps(base, start="/portal.html?rename=1"), answers, resume={"retry_wait_ms": 100})
            stops(r, "expected the label Impresa esecutrice")
            assert not r.get("retries"), r.get("retries")
            # Some boxes with the label, but not the nth: the page as it is, never retried.
            PORTAL.reset()
            st = steps(base)
            st["sections"][1]["fields"].append({"kind": "text", "label": "Impresa esecutrice", "nth": 2, "value": "x"})
            r = fill(browser, base, st, answers, resume={"retry_wait_ms": 100})
            stops(r, "1 fields with this label")
            assert not r.get("retries"), r.get("retries")
        case("retries are bounded; a renamed label, or a box found but not the nth, is never retried", stubborn)

        def onefield():
            # Two rows the portal keeps as one radio field, each opening its own box: the second's
            # tick hides the first's box. The section's read-back says so, and it isn't retried as a
            # slow portal (the art. 34-ter dating and oblazione, 2026-11-02).
            PORTAL.reset()
            st = steps(base, start="/portal.html?onefield=1")
            st["sections"][1]["fields"] += [
                {"kind": "radio", "label": "dà atto che la data/epoca di realizzazione"},
                {"kind": "text", "label": "è", "value": "1966"},
                {"kind": "radio", "label": "determina l’oblazione dovuta"},
                {"kind": "text", "label": "in euro", "value": "1032"}]
            r = fill(browser, base, st, answers, resume={"retry_wait_ms": 100})
            stops(r, "not kept")
            assert "hidden by a later choice" in r["error"] and not r.get("retries"), (r["error"], r.get("retries"))
        case("a box a later choice hid is not kept, said so, and not retried", onefield)

        def silent():
            # A run that stops on a lost value tells a caller which box and why, never what it
            # held: the report, its snapshot and the stored copy have no value in them, while
            # held() (for the person's review page) has what was wanted.
            PORTAL.reset(drop=True)
            h = []
            r = fill(browser, base, steps(base), answers, held=h)
            assert r["result"] == "stopped" and "fresh load of the draft: not kept" in r["error"], r
            blob = json.dumps(r, ensure_ascii=False).lower()
            for v in (answers["den"], answers["impresa"]):
                assert v.lower() not in blob, f"the report carries {v!r}: {blob[:300]}"
            assert '"want"' not in blob and '"got"' not in blob and '"kept"' not in blob, blob[:300]
            assert '"why":"empty"' in r["error"] or '"why":"missing"' in r["error"], r["error"]
            snap = r["snapshot"]
            assert snap and snap["boxes"], snap
            assert any(b["state"] == "filled" for b in snap["boxes"]), "look() shows no filled box"
            assert all(set(b) <= {"id", "label", "kind", "state", "options"} for b in snap["boxes"]), snap["boxes"][0]
            assert any(d["want"] == answers["den"] for d in h[0]["details"]), "held() lost what was wanted"
        case("a stopped run's report, snapshot and stored copy hold no value; held() has them", silent)

        def echoed():
            # A portal message that repeats a value is scrubbed from the error.
            PORTAL.reset()
            r = fill(browser, base, steps(base, start="/portal.html?rename=1"), answers | {"impresa": "Ditta esecutrice"})
            assert "expected the label Impresa esecutrice" in r["error"], r["error"]
            assert "ditta esecutrice" not in r["error"].lower() and "‹value›" in r["error"], r["error"]
        case("a portal label that repeats a value is scrubbed from the error", echoed)

        def sealed_page(st, code):
            values = run.Values(small, fields={"x:ruolo.tipo": "titolare"})
            install, run_js = run.page_scripts(st, values, files_limit=None, code=code)
            page = browser.new_page()
            page.goto(base + "/")
            page.evaluate(install)
            return page, run_js

        def clean_of_values(page, code):
            dump = page.evaluate("JSON.stringify([localStorage, sessionStorage])")
            for secret in (answers["den"], answers["impresa"], code):
                assert secret not in dump, f"the tab's storage holds {secret!r}"

        def sealed():
            # run.js carries the values sealed; the person's code opens them in the page, a wrong
            # one is refused and asked again, and no storage ever holds them or the code.
            PORTAL.reset()
            code = run.new_code()
            page, run_js = sealed_page(steps(base), code)
            try:
                for secret in (answers["den"], answers["impresa"], base64.b64encode(b"%PDF-1.4 tiny\n").decode()):
                    assert secret not in run_js, f"run.js carries {secret!r}"
                assert page.evaluate(run_js) == "waiting for the code"
                first = page.evaluate("__pv.wait(300)")
                assert first["result"] == "waiting" and first["waiting"], first
                assert page.evaluate("document.querySelector('[data-pv=code] input').type") == "password"
                type_code(page, run.pretty_code(run.new_code()))
                page.wait_for_function("((document.querySelector('[data-pv=code]') || {}).textContent || '').includes(\"non apre\")")
                type_code(page, run.pretty_code(code).lower())
                done = settle(page)
                assert done["result"] == "filled", done.get("error")
                assert PORTAL.fields.get(DEN) == answers["den"] and PORTAL.fields.get(IMPRESA) == answers["impresa"], PORTAL.fields
                assert len(PORTAL.files) == 2 and {f["sha256"] for f in PORTAL.files} == {hashlib.sha256(tiny.read_bytes()).hexdigest()}, PORTAL.files
                assert page.query_selector("[data-pv=code]") is None, "the code box stayed"
                clean_of_values(page, code)
            finally:
                page.close()
        case("a sealed run.js: the person's code opens it in the page, a wrong one is refused, nothing is stored in the clear", sealed)

        def never_opens():
            PORTAL.reset()
            page, run_js = sealed_page(steps(base), run.new_code())
            try:
                page.evaluate(run_js)
                for _ in range(5):
                    type_code(page, run.pretty_code(run.new_code()))
                done = settle(page)
                assert done["result"] == "stopped" and "the code didn't open the values" in done["error"], done
                assert not PORTAL.fields, "a run started on a wrong code"
            finally:
                page.close()
        case("five wrong codes end the sealed run before anything is filled", never_opens)

        def sealed_stopped(reload):
            PORTAL.reset()
            code = run.new_code()
            page, run_js = sealed_page(steps(base, start="/portal.html?rename=1"), code)
            try:
                page.evaluate(run_js)
                type_code(page, code)
                first = settle(page)
                assert first["result"] == "stopped" and "expected the label Impresa esecutrice" in first["error"], first
                clean_of_values(page, code)
                held = json.loads(page.evaluate("sessionStorage.getItem('pv-held')"))
                assert {"n", "c", "t"} <= set(held) and "kept" not in held, "what the first section typed isn't sealed"
                if reload:
                    page.evaluate("delete window.__pv; (0, eval)(localStorage.getItem('pv-runner'))")
                fix = '__pv.resume({fixes: [{section: 1, field: 0, set: {label: "Ditta esecutrice"}}]})'
                assert page.evaluate(fix) == ("waiting for the code" if reload else "started")
                if reload:
                    type_code(page, code)
                else:
                    assert page.query_selector("[data-pv=code]") is None, "asked for the code again in the same runner"
                done = settle(page)
                assert done["result"] == "filled" and done["resumed"], done.get("error")
                assert [s["section"] for s in done["sections"]] == ["Dati tecnici"], "redid a finished section"
                clean_of_values(page, code)
            finally:
                page.close()
        case("a sealed run that stopped resumes in the same runner with no new code", lambda: sealed_stopped(False))
        case("after the runner reloads, a sealed run resumes once the code is typed again", lambda: sealed_stopped(True))

        browser.close()

    def pane_limit():
        # Over 256 KB the pane's run.js carries what to pick, not bytes; a batch (pick=False),
        # with no one to pick for each run, still refuses.
        values = run.Values(answers, fields={"x:ruolo.tipo": "titolare"})
        _, run_js = run.page_scripts(steps(base), values)
        assert len(run_js) < 10_000 and '"picked":true' in run_js, f"run.js is {len(run_js)} bytes"
        try:
            run.page_scripts(steps(base), values, pick=False)
        except run.StepError as e:
            assert "256 KB" in str(e), str(e)
        else:
            raise AssertionError("3 MB of files went into run.js for a batch")
    case("over 256 KB the pane's run.js names the files to pick; a batch still refuses", pane_limit)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        def pick_page():
            values = run.Values(answers, fields={"x:ruolo.tipo": "titolare"})
            install, run_js = run.page_scripts(steps(base), values)
            page = browser.new_page()
            page.goto(base + "/")
            page.evaluate(install)
            assert page.evaluate(run_js) == "waiting for the files"
            first = page.evaluate("__pv.wait(300)")
            assert first["result"] == "waiting" and "choose" in first["waiting"], first
            return page

        def picked_files():
            # Too big for run.js: the person picks the files in the page. One with the right name
            # and other bytes is refused, by name; the right ones attach byte-exact, and no
            # storage of the tab holds them.
            PORTAL.reset()
            other = tmp / "other"
            other.mkdir(exist_ok=True)
            (other / planimetria.name).write_bytes(b"%PDF-1.4\n" + os.urandom(planimetria.stat().st_size - 9))
            page = pick_page()
            try:
                page.set_input_files(FILES, str(other / planimetria.name))
                page.wait_for_function("(document.querySelector('[data-pv=files]') || {}).textContent.includes('Non è il file controllato prima')")
                assert page.evaluate("__pv.wait(200)")["result"] == "waiting"
                page.set_input_files(FILES, [str(planimetria), str(ricevuta)])
                done = settle(page)
                assert done["result"] == "filled", done.get("error")
                assert {f["name"]: f["sha256"] for f in PORTAL.files} == sha, PORTAL.files
                assert page.query_selector("[data-pv=files]") is None, "the files box stayed"
                dump = page.evaluate("JSON.stringify([localStorage, sessionStorage]).length")
                assert dump < 1_000_000, f"the tab's storage holds {dump} characters"
            finally:
                page.close()
        case("files too big for run.js are picked in the page: a wrong one refused by name, the right ones byte-exact", picked_files)

        def picked_folder():
            # The job's folder chosen whole: its other files are passed over.
            PORTAL.reset()
            job = tmp / "pratica"
            job.mkdir(exist_ok=True)
            for f in (planimetria, ricevuta):
                shutil.copy(f, job / f.name)
            (job / "appunti.txt").write_text("non allegare")
            page = pick_page()
            try:
                page.set_input_files("[data-pv=files] input[webkitdirectory]", str(job))
                done = settle(page)
                assert done["result"] == "filled", done.get("error")
                assert {f["name"]: f["sha256"] for f in PORTAL.files} == sha, PORTAL.files
            finally:
                page.close()
        case("the job's folder picked whole: its files attached, its others passed over", picked_folder)

        def picked_bundle():
            # run.py page --bundle: the runner, the steps and run.js in one file the person picks
            # in pick.js's box, for a pane that lacks the runner (too big for one call).
            PORTAL.reset()
            values = run.Values(small, fields={"x:ruolo.tipo": "titolare"})
            files = run.page_files(steps(base), values)
            out = tmp / "bundle-out"
            out.mkdir(exist_ok=True)
            run.bundle(out, out / "pv-run.js", files)
            # The person reads the box: the file by name, where it is, and no "JS".
            box = (out / "pick.js").read_text()
            assert "«pv-run» nella cartella Download" in box and "JS" not in box.split("innerHTML")[1].split(";")[0], box
            page = browser.new_page()
            try:
                page.goto(base + "/")
                assert "box shown" in page.evaluate((out / "pick.js").read_text())
                page.set_input_files("#pv-pick input", str(out / "pv-run.js"))
                page.wait_for_function("window.pvPicked")
                assert page.evaluate("window.pvPicked") == "started", page.evaluate("window.pvPicked")
                done = settle(page)
                assert done["result"] == "filled", done.get("error")
                assert PORTAL.fields.get(DEN) == small["den"], PORTAL.fields
            finally:
                page.close()
        case("run.py page --bundle: runner, steps and run.js picked as one file start the run", picked_bundle)

        def fetched():
            # fetch.js: the page downloads the runner and the steps file from the released plugin
            # (GitHub, two hosts) and rebuilds this case's steps byte for byte, so no one picks a
            # file. A "+" list (expanded by its count) and a section this case drops (`when`),
            # as real cases have; the hosts here are routed to the local files.
            PORTAL.reset()
            st = steps(base, start="/portal.html?liste=1")
            st["sections"][1]["fields"] += [
                {"kind": "text", "label": "Tipologia di atto", "anchor": "Tipologia di atto", "block": 1, "value": "{{ask.atto_1}}"},
                {"kind": "add", "anchor": "Tipologia di atto", "block": "#N", "each": {"count": "{{ask.atti}}", "from": 2}},
                {"kind": "text", "label": "Tipologia di atto", "anchor": "Tipologia di atto", "block": "#N", "value": "{{ask.atto_#K}}"}]
            st["sections"].append({"section": "Solo con altri titolari", "when": "{{ask.altri}}", "fields": [
                {"id": "altri_txt", "kind": "text", "label": "Altri", "value": "{{ask.den}}"}]})
            src = tmp / "fetched-steps.json"
            src.write_text(json.dumps(st, ensure_ascii=False, indent=2))
            vals = run.Values(small | {"atti": "3", "atto_1": "uno", "atto_2": "due", "atto_3": "tre", "altri": ""},
                              fields={"x:ruolo.tipo": "titolare"})
            hosts = ("https://raw.githubusercontent.com/o/p/plugin-v9/", "https://cdn.jsdelivr.net/gh/o/p@plugin-v9/")
            real = run.published
            run.published = lambda path: [h + Path(path).name for h in hosts]
            try:
                files = run.page_files(json.loads(src.read_text()), vals, source=src)
            finally:
                run.published = real
            assert "fetch.js" in files and len(files["fetch.js"]) < 10_000, len(files.get("fetch.js", ""))
            served = {"inpage.js": Path(run.__file__).with_name("inpage.js").read_bytes(), src.name: src.read_bytes()}

            def open_page(down=(), wrong=False):
                page = browser.new_page()

                def serve(route):
                    url = route.request.url
                    if url.startswith(tuple(down)):
                        return route.fulfill(status=404, body="")
                    body = served[url.rsplit("/", 1)[1]]
                    route.fulfill(status=200, body=body + (b"//" if wrong else b""), headers={"Access-Control-Allow-Origin": "*"})
                for h in hosts:
                    page.route(h + "**", serve)
                page.goto(base + "/")
                return page
            page = open_page()
            try:
                assert page.evaluate(files["check.js"]) == "run fetch.js, then run.js"
                assert page.evaluate(files["fetch.js"]) == "installed"
                assert page.evaluate(files["check.js"]) == "run run.js", "the steps or the runner aren't byte for byte"
                page.evaluate(files["run.js"])
                done = settle(page)
                assert done["result"] == "filled", done.get("error")
                got = {k.split(":")[-1]: v for k, v in PORTAL.fields.items() if "atto" in k}
                assert got == {"atto1_txt": "uno", "atto2_txt": "due", "atto3_txt": "tre"}, got
            finally:
                page.close()
            # The first host down: the second serves. Both down, or bytes other than released: the bundle.
            for down, wrong, want in ((hosts[:1], False, "installed"), (hosts, False, "fetch failed"), ((), True, "fetch failed")):
                page = open_page(down, wrong)
                try:
                    got = page.evaluate(files["fetch.js"])
                    assert got.startswith(want), (down, wrong, got)
                    if want != "installed":
                        assert page.evaluate(files["check.js"]) == "run fetch.js, then run.js", "a refused file was stored"
                finally:
                    page.close()
            # Where GitHub serves a file of the installed plugin; none for the repo's own copy.
            plugin = tmp / "plugin"
            (plugin / ".claude-plugin").mkdir(parents=True, exist_ok=True)
            (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": "1.2.3", "repository": "https://github.com/o/p"}))
            (plugin / "skills" / "s").mkdir(parents=True, exist_ok=True)
            (plugin / "skills" / "s" / "inpage.js").write_text("")
            assert run.published(plugin / "skills" / "s" / "inpage.js") == [
                "https://raw.githubusercontent.com/o/p/plugin-v1.2.3/skills/s/inpage.js",
                "https://cdn.jsdelivr.net/gh/o/p@plugin-v1.2.3/skills/s/inpage.js"], run.published(plugin / "skills" / "s" / "inpage.js")
            assert run.published(Path(run.__file__).with_name("inpage.js")) == []
            assert "fetch.js" not in run.page_files(steps(base), vals, source=src)
            # A run.js copied by hand that lost a value starts nothing (2026-11-07 on the portal:
            # four `false` dropped, and the run looked for a box this case hasn't).
            PORTAL.reset()
            page = open_page()
            try:
                page.evaluate(files["fetch.js"])
                garbled = files["run.js"].replace(',"due"', "", 1)
                assert garbled != files["run.js"]
                assert page.evaluate(garbled) == run.RUN_CHANGED
                assert page.evaluate("__pv.last()") is None and not PORTAL.fields, "a changed run.js started a run"
                assert run.run_args(files["run.js"])[0].startswith("test/allegati#")
            finally:
                page.close()
        case("fetch.js: the page downloads the runner and steps from the released plugin, byte for byte, or says to bundle", fetched)

        def bundle_unwritable():
            # Cowork's sandbox can't reach the person's Downloads until they allow it: a clear stop
            # that says to ask for the folder, never a traceback.
            files = run.page_files(steps(base), run.Values(small, fields={"x:ruolo.tipo": "titolare"}))
            locked = tmp / "locked"
            locked.mkdir(exist_ok=True)
            locked.chmod(0o500)
            try:
                run.bundle(tmp, locked / "Downloads" / "pv-run.js", files)
                raise AssertionError("an unwritable Downloads was not refused")
            except run.StepError as e:
                assert "allow the Downloads folder" in str(e), e
            finally:
                locked.chmod(0o700)
        case("run.py page --bundle: a Downloads it can't write says to ask for the folder", bundle_unwritable)

        def pick_stopped():
            PORTAL.reset()
            page = pick_page()
            try:
                page.click("[data-pv=files] button")
                done = settle(page)
                assert done["result"] == "stopped" and "weren't chosen" in done["error"], done
                assert not PORTAL.fields and not PORTAL.files, "something was filled"
            finally:
                page.close()
        case("Stop in the files box ends the run before anything is filled", pick_stopped)

        browser.close()


    def sealing():
        code = run.new_code()
        assert len(code) == 15 and set(code) <= set(run.SEAL_ALPHABET), code
        plain = "Mario Rossi RSSMRA80A01F839Y".encode()
        s = run.seal(plain, code)
        assert run.unseal(s, code) == plain and plain not in base64.b64decode(s["c"])
        for other in (run.new_code(), code.lower()):
            try:
                run.unseal(s, other)
            except run.StepError:
                pass
            else:
                raise AssertionError("a wrong code opened it")
        ct = bytearray(base64.b64decode(s["c"]))
        ct[0] ^= 1
        try:
            run.unseal(s | {"c": base64.b64encode(bytes(ct)).decode()}, code)
        except run.StepError:
            pass
        else:
            raise AssertionError("a changed ciphertext opened")
    case("seal: round trip, a wrong code and a changed byte are refused", sealing)

    def cli_page():
        # `page` seals by default and shows the code only to the window; --plain leaves the values
        # in the clear and shows nothing; with no window to show it in, nothing is left to run.
        (tmp / "s.yaml").write_text(yaml.safe_dump(steps(base), allow_unicode=True))
        (tmp / "a.json").write_text(json.dumps(small))
        (tmp / "v.json").write_text(json.dumps({"x:ruolo.tipo": "titolare"}))
        shown, real = [], run.show_code

        def page_cmd(out, *extra):
            argv, buf = sys.argv, io.StringIO()
            sys.argv = ["run.py", "page", "--steps", str(tmp / "s.yaml"), "--answers", str(tmp / "a.json"),
                        "--values", str(tmp / "v.json"), "--out", str(out), *extra]
            try:
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    return run.main(), buf.getvalue()
            finally:
                sys.argv = argv
        run.show_code = lambda code, give_up=None: shown.append(code)
        try:
            rc, text = page_cmd(tmp / "cli-sealed")
            js = (tmp / "cli-sealed" / "run.js").read_text()
            assert rc == 0 and len(shown) == 1, (rc, text)
            assert shown[0] not in text and run.pretty_code(shown[0]) not in text and shown[0] not in js
            assert small["den"] not in js and "startSealed" in js, js[:200]
            rc, text = page_cmd(tmp / "cli-plain", "--plain")
            assert rc == 0 and len(shown) == 1, "--plain showed a code"
            assert small["den"] in (tmp / "cli-plain" / "run.js").read_text()

            def no_window(code, give_up=None):
                raise run.StepError("no window")
            run.show_code = no_window
            rc, text = page_cmd(tmp / "cli-nowindow")
            assert rc == 1 and not (tmp / "cli-nowindow" / "run.js").exists(), "a sealed run.js was left with no code shown"
        finally:
            run.show_code = real
    case("run.py page seals by default, shows the code only to the window, and --plain says so", cli_page)

    def no_record():
        try:
            run.resumption({"url": "https://example.invalid/d", "at": {"phase": "section", "index": 1}})
        except run.StepError as e:
            assert "no record of what the earlier sections typed" in str(e), str(e)
        else:
            raise AssertionError("a resume past the first section went ahead with no record of the earlier ones")
        assert run.resumption({"url": "https://example.invalid/d", "at": {"phase": "wizard", "index": 0}})["kept"] == []
    case("a resume with no private record of the earlier sections is refused", no_record)

    def missing():
        values = run.Values(answers | {"ricevuta": str(tmp / "nope.p7m")}, fields={"x:ruolo.tipo": "titolare"})
        try:
            run.plan(steps(base), values)
        except run.StepError as e:
            assert "no file" in str(e), str(e)
        else:
            raise AssertionError("a missing file passed the plan")
    case("a file that isn't there stops the plan", missing)

    def reviewed():
        filled = {"procedure": "test/allegati", "result": "filled", "sections": [], "total_seconds": 3.0,
                  "url": "https://example.invalid/d", "values": [], "yours": ["Firmare"]}
        folder = tmp / "review"
        (folder / "private").mkdir(parents=True, exist_ok=True)
        decl = [{"section": "Dichiarazione di consapevolezza", "text": "Il sottoscritto dichiara il vero.",
                 "boxes": [{"label": "Per presa visione", "kind": "checkbox", "ticked": False}]}]
        (folder / "private" / "declarations.json").write_text(json.dumps(decl))
        (folder / "private" / "anteprima.pdf").write_bytes(b"%PDF-1.4\nfinto\n")
        page = run.review.portal_review(filled | {"declarations_read": 1, "preview_pdf": True}, folder)
        assert "Il sottoscritto dichiara il vero." in page and "Le dichiarazioni che spunterà" in page
        assert "1 copiate parola per parola dal portale; nessuna spuntata" in page, "no check that none is ticked"
        assert "Scarica il PDF" in page and "L&#x27;anteprima PDF del portale copiata" in page
        decl[0]["boxes"][0]["ticked"] = True
        (folder / "private" / "declarations.json").write_text(json.dumps(decl))
        page = run.review.portal_review(filled | {"declarations_read": 1}, folder)
        assert "già spuntate prima che Lei le aprisse" in page and "Dichiarazione di consapevolezza" in page
        # Nothing copied (the pane, or an older run): the page says so, and never shows a stand-in.
        pane = run.review.portal_review(filled | {"declarations_read": 2}, tmp / "nowhere")
        assert "Dichiarazioni: non copiate in questa compilazione" in pane, "no note for the pane"
        assert "non è stata copiata" in pane and "Le dichiarazioni che spunterà" not in pane
        stopped = run.review.portal_review(filled | {"result": "stopped", "error": "a reason for Claude"}, tmp / "nowhere")
        assert "Dichiarazioni" not in stopped and "anteprima" not in stopped.lower(), "a stopped run reports on what it never reached"
        assert "a reason for Claude" not in stopped and "si è fermata" in stopped.lower(), "the runner's reason on the person's page"
        # The page the person reads is Italian: none of the words an English page would have.
        english = re.compile(r"\b(the|your|you|and|of|was|draft|saved|every|value|left|declarations?)\b", re.I)
        for doc in (page, pane, stopped):
            text = re.sub(r"<[^>]+>", " ", doc.split("</style>", 1)[1])
            hits = {w.lower() for w in english.findall(text)} - {"draft"}  # test/allegati, example.invalid/d
            assert not hits, f"English on the review page: {sorted(hits)}"
    case("the review page shows the declarations' text and the portal's PDF, or says it has neither", reviewed)

    server.shutdown()
    shutil.rmtree(tmp)
    print(f"{len(ran) - len(failed)}/{len(ran)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
