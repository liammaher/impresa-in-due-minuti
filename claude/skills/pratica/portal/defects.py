#!/usr/bin/env python3
"""docs/portal-defects.md, drawn from defects.yaml, the one record of the portals' known defects.

    defects.py            say whether docs/portal-defects.md is defects.yaml's
    defects.py --write    draw it again

Each entry's `page` is its section of the page (a heading and its points, in order); the rest
is what gen.py copies into a steps file for pre-flight to return (gen.py leaves `page` out).
test_gen fails on a page that differs. Edit defects.yaml, never the page.
"""
import argparse
import sys
import textwrap
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RECORD = HERE / "defects.yaml"
OUT = HERE.parents[3] / "docs" / "portal-defects.md"
HEAD = """# Portal defects

<!-- Drawn from claude/skills/pratica/portal/defects.yaml by defects.py --write; edit defects.yaml, not this page. -->

Things Napoli's SUE on impresainungiorno does that a pratica can't work around: each blocks a case
the law allows, so the recipe refuses it with the reason. Each is a record in
`claude/skills/pratica/portal/defects.yaml`, which the refusal names (`defect:`): pre-flight then
returns it under `defects`, and the person is told what the portal does and chooses what to do.
Fixing them is the portal's operator's (InfoCamere, which runs impresainungiorno) or the Comune's
(the SUE configures its forms). Each entry says what to report and how it was checked, without
personal data. The reports to send, in Italian and one per recipient, with the channels:
[`docs/defect-reports/`](defect-reports/README.md).
"""


def render(record=None):
    record = record if record is not None else yaml.safe_load(RECORD.read_text())
    out = [HEAD]
    for id_, d in record.items():
        page = d.get("page")
        if not page:
            raise ValueError(f"defects.yaml: {id_} has no page (its section of docs/portal-defects.md)")
        out.append(f"## {page['heading']}\n")
        for label, text in page["points"].items():
            out.append(textwrap.fill(f"- **{label}**: {text}", 100, subsequent_indent="  ",
                                     break_long_words=False, break_on_hyphens=False))
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    text = render()
    if a.write:
        OUT.write_text(text)
    elif OUT.read_text() != text:
        sys.exit(f"{OUT} isn't defects.yaml's: defects.py --write")
    print(f"{OUT.name} is defects.yaml's")


if __name__ == "__main__":
    main()
