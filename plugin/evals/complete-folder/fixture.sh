#!/usr/bin/env bash
# A complete real job, as a tecnico hands it over: the studio in studio.json (their details, given
# once), and the client's job in Fittizio/ with the P6 dossier in the documents' real formats
# (intake/bench/dossier.py: visura, lease, deed, relazione, notifica, receipts...) and the
# tecnico's note.txt with what no document holds. Every file is a signed PDF/A (a self-signed
# certificate made here, as bench/test_one_yes.py does). Not called a test: the reply is the one
# message with every answer, for one «sì».
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$here/../_job/studio.json" studio.json
mkdir -p Fittizio
cp -R "$here/../_dossier" Fittizio/docs
cp "$here/note.txt" Fittizio/note.txt
cf="$(python3 -c 'import json; d=json.load(open("studio.json")); print(next(v for k,v in d.items() if k.endswith(":identity.codice_fiscale")))')"
tmp="$(mktemp -d)"
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$tmp/k.pem" -out "$tmp/c.pem" -days 2 \
  -subj "/C=IT/O=Fittizio/CN=Firma Finta/serialNumber=TINIT-$cf" 2>/dev/null
for f in Fittizio/docs/*.pdf; do
  python3 - "$f" "$tmp" <<'PY'
import subprocess, sys
from pathlib import Path
f, tmp = Path(sys.argv[1]), Path(sys.argv[2])
raw = f.read_bytes()
xmp = (b'\n%<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF><rdf:Description xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/" '
       b'pdfaid:part="2" pdfaid:conformance="B"/></rdf:RDF></x:xmpmeta>\n')
content = raw if b"pdfaid" in raw else raw + xmp
(tmp / "doc.pdf").write_bytes(content)
subprocess.run(["openssl", "cms", "-sign", "-signer", tmp / "c.pem", "-inkey", tmp / "k.pem", "-in", tmp / "doc.pdf",
                "-outform", "DER", "-out", tmp / "sig.der", "-binary"], check=True, capture_output=True)
sig = (tmp / "sig.der").read_bytes().hex().upper()
f.write_bytes(content + b"1 0 obj\n<< /Type /Sig /Filter /Adobe.PPKLite /SubFilter /ETSI.CAdES.detached "
              b"/ByteRange [0 100 200 300] /Contents <" + (sig + "0" * 2048).encode() + b"> >>\nendobj\n%%EOF\n")
PY
done
rm -rf "$tmp"
