#!/usr/bin/env python3
"""A made-up PDF in the rehearsals' layout: one page, "FAC-SIMILE - PROVA NON INVIARE", a title
and a made-up address, as every file under rehearsals/*/files/ reads.

    python3 claude/skills/pratica/portal/bench/fake_pdf.py OUT.pdf "Title" ["Address"] [--size MB]

--size pads it with a stream of random bytes to that many MB, the weight of a real drawing, for a
run that tries files over the pane's 16 KB (the person picks them: portal/README.md, "Large files").
Such files stay out of the repo (a folder outside it, as ~/Downloads/pv-pick-prova on 2026-11-04).
"""
import argparse
import os
from pathlib import Path


def esc(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make(out, title, address="Via Domenico Fontana 40", size_mb=0):
    lines = ["FAC-SIMILE - PROVA NON INVIARE", "Documento inventato per una prova del portale.", "", title,
             f"{address} [inventata]"]
    text = ("BT /F1 14 Tf 50 780 Td 18 TL " + " ".join(f"({esc(line)}) '" for line in lines) + " ET").encode("cp1252")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Length %d >>\nstream\n" % len(text) + text + b"\nendstream"]
    if size_mb:
        pad = os.urandom(int(size_mb * 1024 * 1024))  # as a scanned drawing weighs; not drawn
        objs.append(b"<< /Length %d >>\nstream\n" % len(pad) + pad + b"\nendstream")
    out_b, offs = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offs.append(len(out_b))
        out_b += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out_b)
    out_b += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out_b += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    Path(out).write_bytes(bytes(out_b))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("title")
    ap.add_argument("address", nargs="?", default="Via Domenico Fontana 40")
    ap.add_argument("--size", type=float, default=0, help="pad to this many MB")
    a = ap.parse_args()
    make(a.out, a.title, a.address, a.size)
