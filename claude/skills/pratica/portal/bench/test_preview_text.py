#!/usr/bin/env python3
"""Offline tests of portal/preview_text.js: PDFs built here, served as /fnsuap/preview.do, read by the
script as the pane runs it (headless Chromium, the file's text unchanged). No network, no portal.

  ~/.cache/pratica-portal/venv/bin/python -I claude/skills/pratica/portal/bench/test_preview_text.py

The first case is laid out as the portal's iText 2.1.7 preview is (Tm before every string, a
long cell wrapped by a second Tm, WinAnsi bytes raw and octal); the others are what another
writer may use, and what the script must refuse rather than misread.
"""

import sys
import threading
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = (HERE.parent / "preview_text.js").read_text()
FONT = b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding>>"


def stream(data, extra=b"", flate=True, length=None):
    body = zlib.compress(data) if flate else data
    filt = b"/Filter/FlateDecode" if flate else b""
    ln = length if length is not None else str(len(body)).encode()
    return b"<<" + filt + extra + b"/Length " + ln + b">>\nstream\n" + body + b"\nendstream"


def pdf(objs, trailer=b""):
    """objs: {number: body}. Object 1 is the catalog; the page tree is the caller's."""
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    for n in sorted(objs):
        out += b"%d 0 obj\n" % n + objs[n] + b"\nendobj\n"
    out += b"xref\n0 1\n0000000000 65535 f \ntrailer\n<</Size %d/Root 1 0 R%s>>\nstartxref\n0\n%%%%EOF\n" % (
        max(objs) + 1, trailer)
    return bytes(out)


def doc(pages, extra=None, font=FONT, trailer=b""):
    """A two-level page tree whose object numbers run against the reading order."""
    objs = {1: b"<</Type/Catalog/Pages 2 0 R>>", 5: font}
    nums = list(range(100, 100 - 2 * len(pages), -2))  # pages get 100, 98, ...: reading order != numbering
    objs[2] = b"<</Type/Pages/Kids[3 0 R]/Count %d>>" % len(pages)
    objs[3] = b"<</Type/Pages/Parent 2 0 R/Kids[" + b" ".join(b"%d 0 R" % n for n in nums) + b"]/Count %d>>" % len(pages)
    for n, content in zip(nums, pages):
        parts = content if isinstance(content, list) else [stream(content)]
        refs = []
        for k, part in enumerate(parts):
            objs[n + 1 + k * 1000] = part
            refs.append(b"%d 0 R" % (n + 1 + k * 1000))
        objs[n] = (b"<</Type/Page/Parent 3 0 R/MediaBox[0 0 595 842]/Resources<</Font<</F1 5 0 R>>>>/Contents["
                   + b" ".join(refs) + b"]>>")
    objs.update(extra or {})
    return pdf(objs, trailer)


def bt(x, y, s):
    return b"BT 1 0 0 1 %g %g Tm /F1 9 Tf (%s)Tj ET\n" % (x, y, s)


ITEXT_P1 = (b"q 1 1 1 rg 36 315 523 17 re f Q\n" + bt(39, 320, b"Nome") + bt(169.75, 320, b"Cognome")
            + bt(39, 303, b"Ugo") + bt(169.75, 303.4, b"Fittizio")
            + b"BT 1 0 0 1 300.5 303 Tm /F1 9 Tf (ugo.fittizio@example.co)Tj 1 0 0 1 300.5 294 Tm (m)Tj ET\n"
            + bt(39, 280, b"Che cos\\222\\350 \\(art. 6\\)") + b"BT 1 0 0 1 39 270 Tm (Localit)Tj (\xe0 estera)Tj ET\n"
            + bt(39, 260, b"\x80 333,00") + bt(39, 250, b"Il simbolo \xe8 qui"))
ITEXT_P2 = bt(39, 800, b"[ X ] NCEU") + bt(150, 800, b"[  ] NCT")

VARIANTS = (
    b"% commento (non testo) Tj\n"
    b"BT 1 0 0 1 39 700 Tm [([ X ]) -250 (riguarda) 50 (no)] TJ ET\n"
    b"BT 1 0 0 1 39 650 Tm 12 TL (prima)Tj (seconda)' 0 0 (terza)\" T* (quarta)Tj ET\n"
    b"BT 39 600 TD (a)Tj 0 -10 TD (b)Tj T* (c)Tj ET\n"
    b"q 1 0 0 1 100 500 cm BT 0 0 Td (dentro)Tj ET Q BT 1 0 0 1 39 500 Tm (fuori)Tj ET\n"
    b"q 0.5 0 0 0.5 0 0 cm BT 1 0 0 1 100 800 Tm (mezzo)Tj ET Q BT 1 0 0 1 39 400 Tm (riga)Tj ET\n"
    b"BT 1 0 0 1 39 300 Tm <4369616F>Tj ET\n"
    b"BT 1 0 0 1 39 290 Tm (a (b) c)Tj ET\n"
    b"BT 1 0 0 1 39 280 Tm (spez\\\nzato)Tj ET\n"
    b"/P <</MCID 0>> BDC BT 1 0 0 1 39 270 Tm (marcato)Tj ET EMC\n"
    b"q BI /W 4 /H 1 /CS /G /BPC 8 ID \x00\xffEI\x01 EI Q\n"
    b"BT 1 0 0 1 39 260 Tm (dopo l'immagine)Tj ET\n"
)
VARIANTS_TEXT = ("--- pagina 1\n[ X ] riguardano\nprima\nseconda\nterza\nquarta\na\nb\nc\nfuori  dentro\n"
                 "riga  mezzo\nCiao\na (b) c\nspezzato\nmarcato\ndopo l'immagine\nseconda parte\nin chiaro")


def cases():
    yield ("itext", doc([ITEXT_P1, ITEXT_P2]),
           "--- pagina 1\nNome  Cognome\nUgo  Fittizio  ugo.fittizio@example.co\nm\nChe cos’è (art. 6)\n"
           "Località estera\n€ 333,00\nIl simbolo è qui\n--- pagina 2\n[ X ] NCEU  [  ] NCT")
    # Three content streams: Flate, Flate under an indirect /Length, and none; plus an uncompressed
    # metadata stream and a font file whose bytes spell an object, which must not be read as one.
    decoy = b"9 0 obj <</Type/Catalog/Pages 77 0 R>> endobj endstream"
    second = zlib.compress(b"BT 1 0 0 1 39 250 Tm (seconda parte)Tj ET\n")
    extra = {
        40: b"<</Type/Metadata/Subtype/XML/Length 20>>\nstream\n<x:xmpmeta></x:xmp>\nendstream",
        41: b"<</Length1 %d/Length %d>>\nstream\n" % (len(decoy), len(decoy)) + decoy + b"\nendstream",
        42: str(len(second)).encode(),
    }
    yield ("variants", doc([[stream(VARIANTS),
                             b"<</Filter/FlateDecode/Length 42 0 R>>\nstream\n" + second + b"\nendstream",
                             stream(b"BT 1 0 0 1 39 240 Tm (in chiaro)Tj ET\n", flate=False)]], extra), VARIANTS_TEXT)
    # A /Length that is wrong: found again by endstream.
    yield ("wrong length", doc([[stream(bt(39, 100, b"ok"), length=b"3")]]), "--- pagina 1\nok")
    # A form XObject that no page draws (an annotation's appearance) is no reason to refuse.
    yield ("unused form", doc([bt(39, 100, b"ok")], {60: stream(b"", b"/Type/XObject/Subtype/Form/BBox[0 0 1 1]")}),
           "--- pagina 1\nok")
    yield ("empty page", doc([[]]), "--- pagina 1\n")

    refuse = [
        ("not a pdf", b"<html>Accedi con SPID</html>", "no PDF"),
        ("object streams", doc([bt(1, 1, b"x")], {60: stream(b"1 0", b"/Type/ObjStm/N 1/First 4")}), "compressed streams"),
        ("encrypted", doc([bt(1, 1, b"x")], trailer=b"/Encrypt 70 0 R"), "encrypted"),
        ("cid font", doc([bt(1, 1, b"x")], font=b"<</Type/Font/Subtype/Type0/BaseFont/X/Encoding/Identity-H>>"), "font"),
        ("differences", doc([bt(1, 1, b"x")], font=b"<</Type/Font/Subtype/Type1/BaseFont/X/Encoding 8 0 R>>",
                            extra={8: b"<</Type/Encoding/Differences[65/B]>>"}), "font"),
        ("to unicode", doc([bt(1, 1, b"x")], font=FONT[:-2] + b"/ToUnicode 8 0 R>>", extra={8: stream(b"")}), "font"),
        ("form drawn", doc([b"q /Fm0 Do Q\n" + bt(1, 1, b"x")], {60: stream(b"", b"/Type/XObject/Subtype/Form")}), "form XObject"),
        ("corrupt", doc([[b"<</Filter/FlateDecode/Length 9>>\nstream\nnot zlib!\nendstream"]]), "decompress"),
        ("other filter", doc([[b"<</Filter/ASCII85Decode/Length 2>>\nstream\n~>\nendstream"]]), "filter"),
        ("no catalog", pdf({2: b"<</Type/Pages/Kids[]/Count 0>>"}), "catalog"),
    ]
    for name, body, words in refuse:
        yield (name, body, {"error": words})


class Handler(BaseHTTPRequestHandler):
    body = b""

    def log_message(self, *a):
        pass

    def do_GET(self):
        pdf_ = self.path.startswith("/fnsuap/preview.do")
        data = Handler.body if pdf_ else b"<html><body>portale</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf" if pdf_ and data.startswith(b"%PDF") else "text/html")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    from playwright.sync_api import sync_playwright

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    failed = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/fnsuap/cmd/home")
        for name, body, want in cases():
            Handler.body = body
            got = page.evaluate(SCRIPT)
            if isinstance(want, dict):
                ok = "error" in got and want["error"] in got["error"] and "text" not in got
            else:
                ok = got.get("text") == want and got.get("bytes") == len(body)
            print(("ok   " if ok else "FAIL ") + name)
            if not ok:
                failed += 1
                print(f"  want: {want!r}\n  got:  {got!r}")
        browser.close()
    server.shutdown()
    print(f"{failed} failed" if failed else "all passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
