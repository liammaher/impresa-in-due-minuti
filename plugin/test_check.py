#!/usr/bin/env python3
"""The plugin's check.py against the vault's own rules: every case in
internal/vault/testdata/values.json, which internal/vault/italy_shared_test.go holds
NormalizeAndValidate to, so the copy can't drift from the vault. Then check.py's own extras,
which the vault doesn't make: sex as M or F, a field's fixed values, no secret, no unknown id.

  python3 plugin/test_check.py      (no packages)
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE / "impresa-in-un-minuto" / "skills" / "pratiche"))
sys.dont_write_bytecode = True
import check  # noqa: E402

SCHEMA = json.loads((REPO / "schema.json").read_text())


def judged(fid, value):
    out, problems = check.check({fid: value}, SCHEMA)
    return None if problems else out[fid]


def main():
    cases = json.loads((REPO / "internal" / "vault" / "testdata" / "values.json").read_text())["cases"]
    bad = [f"{c['id']} {c['value']!r}: got {judged(c['id'], c['value'])!r}, the vault's {c['want']!r}"
           for c in cases if judged(c["id"], c["value"]) != c["want"]]
    extras = [("identity.sex", "m", "M"), ("identity.sex", "X", None), ("ruolo.tipo", "titolare", "titolare"),
              ("leo:ruolo.tipo", "cliente", "cliente"), ("ruolo.tipo", "capo", None),
              ("spid.password", "x", None), ("identity.colore", "blu", None), ("Identity.first_name", "Mario", None)]
    bad += [f"{fid} {v!r}: got {judged(fid, v)!r}, want {want!r}" for fid, v, want in extras if judged(fid, v) != want]
    for b in bad:
        print("FAIL ", b)
    print(f"{len(cases)} shared cases, {len(extras)} of check.py's own: {len(bad)} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
