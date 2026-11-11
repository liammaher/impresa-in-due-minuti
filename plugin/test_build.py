#!/usr/bin/env python3
"""build.py's switches, offline: the marked parts each build keeps, the markers it refuses,
and the hand-written plugin both ways (vault: no setup skill and no word of the archive without
it; python_download: off by default, and then no download in the launcher or the texts).

  python3 plugin/test_build.py      (needs PyYAML, as build.py does)
"""

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import build  # noqa: E402

TEXT = "a\n<!-- vault -->\nb\n<!-- /vault -->\n<!-- no-vault -->\nc\n<!-- /no-vault -->\nd\n"


def refused(text):
    try:
        build.keep_parts(text, True, "t.md")
    except SystemExit:
        return True
    return False


def main():
    assert build.keep_parts(TEXT, True, "t.md") == "a\nb\nd\n"
    assert build.keep_parts(TEXT, False, "t.md") == "a\nc\nd\n"
    for bad in ("<!-- vault -->\nx\n", "x\n<!-- /vault -->\n", "<!-- vault -->\n<!-- no-vault -->\n",
                "<!-- vault -->\nx\n<!-- /no-vault -->\n"):
        assert refused(bad), bad
    assert isinstance(build.vault_default(), bool)
    import pin_marketplace  # the listing people read before installing says what the plugin has
    for vault in (True, False):
        said = pin_marketplace.marketplace("0.1.0", "0" * 40, vault=vault)["plugins"][0]["description"]
        assert ("vault" in said) == vault, said
    # What the app lists, in Italian and under the plugin's name, entry and manifest alike.
    entry = pin_marketplace.marketplace("0.1.0", "0" * 40, vault=False)["plugins"][0]
    manifest = json.loads(build.with_scope((HERE / "impresa-in-un-minuto" / ".claude-plugin" / "plugin.json").read_text(), "plugin.json"))
    for said in (entry, manifest):
        assert said["displayName"] == "Impresa in un minuto", said
        assert build.scope()["copertura"] in said["description"] and "prepares" not in said["description"].lower(), said

    # Each shipped skill's description is Italian: the app shows it, and writes its "Prova nella chat"
    # prompt from it (2026-11-07: an English "Use when … see a demo" gave "show me a demo CILA").
    import re
    english = re.compile(r"\b(the|use|when|asks|wants|show|demo|test with|made-up|set me up|or update|it isn't)\b", re.I)
    for skill in sorted((HERE / "impresa-in-un-minuto" / "skills").iterdir()):
        if skill.name == build.TEST_SKILL:  # never shipped
            continue
        front = (skill / "SKILL.md").read_text().split("---")[1]
        said = next(line for line in front.splitlines() if line.startswith("description:"))
        plain = re.sub(r"«[^»]*»", "", said)  # what the tecnico may type, quoted, is theirs
        assert not english.search(plain), f"{skill.name}: English in its description: {english.search(plain).group(0)!r}"

    with tempfile.TemporaryDirectory() as tmp:
        for vault in (True, False):
            plugin = Path(tmp) / str(vault)
            shutil.copytree(HERE / "impresa-in-un-minuto", plugin)
            build.select_vault(plugin, vault)
            assert (plugin / "skills" / build.SETUP_SKILL).is_dir() == vault
            for f in plugin.rglob("*.md"):
                text = f.read_text()
                assert not any(build.MARKER.match(line.strip()) for line in text.splitlines()), f
                if not vault:
                    for word in ("pvault", "archivio", "Touch ID", build.SETUP_SKILL):
                        assert word not in text, f"{f.relative_to(plugin)} says {word!r} without the archive"
        # A text naming the archive outside a vault part stops a no-vault build.
        plugin = Path(tmp) / "leak"
        shutil.copytree(HERE / "impresa-in-un-minuto", plugin)
        (plugin / "skills" / "pratiche" / "EXTRA.md").write_text("run pvault status\n")
        try:
            build.select_vault(plugin, False)
        except SystemExit:
            pass
        else:
            raise AssertionError("a no-vault build kept a text that names pvault")

        # A private term stops the build, as a whole word (not inside a hash), and the message
        # gives its line number in the list, never the term.
        plugin = Path(tmp) / "private"
        (plugin / "s").mkdir(parents=True)
        (plugin / "s" / "schema.json").write_text('{"d": "e.g. 908", "sha": "a908b", "cf": "ABCDEF 12G34 H567I"}')
        build.check_private(plugin, ["90", "a9"])  # only inside other words: passes
        for terms, line in ((["x", "908"], 2), (["ABCDEF12G34H567I"], 1)):  # a long one also spaced out
            try:
                build.check_private(plugin, terms)
            except SystemExit as e:
                assert f"s/schema.json: [{line}]" in str(e) and terms[line - 1] not in str(e), e
            else:
                raise AssertionError(f"{terms} not found")

    # python_download: off unless build.yaml says otherwise; its parts nest inside the vault's.
    assert build.switch("python_download") is False, "plugin/build.yaml: python_download ships off"
    both = "a\n<!-- no-vault -->\n<!-- download -->\nb\n<!-- /download -->\n<!-- no-download -->\nc\n<!-- /no-download -->\n<!-- /no-vault -->\n"
    assert build.keep(build.keep_parts(both, False, "t.md"), False, "download", build.DOWNLOAD, "t.md") == "a\nc\n"
    assert build.keep(build.keep_parts(both, False, "t.md"), True, "download", build.DOWNLOAD, "t.md") == "a\nb\n"
    assert build.keep("x\n# <download>\ny\n# </download>\n", False, "download", build.DOWNLOAD_SH, "py") == "x\n"
    with tempfile.TemporaryDirectory() as tmp:
        for download in (True, False):
            plugin = Path(tmp) / str(download)
            shutil.copytree(HERE / "impresa-in-un-minuto", plugin)
            build.select_vault(plugin, False)
            build.select_download(plugin, download)
            py = (plugin / build.LAUNCHER).read_text()
            assert ("python-build-standalone" in py) == download and "# <" not in py
            skill = (plugin / "skills" / "pratiche" / "SKILL.md").read_text()
            assert ("scarico Python" in skill) == download and ("Never install Python yourself" in skill) != download
            for f in plugin.rglob("*.md"):
                assert not any(build.DOWNLOAD.match(line.strip()) for line in f.read_text().splitlines()), f
        # A text that says the plugin downloads Python, outside a download part, stops an off build.
        plugin = Path(tmp) / "leak-dl"
        shutil.copytree(HERE / "impresa-in-un-minuto", plugin)
        (plugin / "skills" / "pratiche" / "EXTRA.md").write_text("it fetches python-build-standalone\n")
        try:
            build.select_download(plugin, False)
        except SystemExit:
            pass
        else:
            raise AssertionError("an off build kept a text about downloading Python")
    # The texts say what the build carries, from build.yaml's sportelli and coverage.yaml's comuni:
    # the sportelli it lists (the SUE's and the SUAP's) of Napoli; another comune, the same texts say so.
    got = build.scope()
    assert got["copertura"] == " e ".join(n for d, n in build.SPORTELLO_NAMES.items() if d in build.sportelli()) \
        + " del Comune di Napoli" and got["comuni"] == "il Comune di Napoli" and got["città"] == "Napoli", got
    assert ("SCIA per aprire" in got["pratiche"]) == ("suap" in build.sportelli()) and "CILA" in got["pratiche"], got
    assert ("titolare di un'impresa" in got["chi"]) == ("suap" in build.sportelli()), got
    both = build.scope({"sue", "suap"}, {"F839": "Napoli", "H501": "Roma"})
    assert (both["copertura"], both["comuni"], both["città"]) == (
        "SUE e SUAP dei Comuni di Napoli e Roma", "i Comuni di Napoli e Roma", "Napoli e Roma"), both
    assert build.scope({"sue"})["chi"] == "un architetto, un geometra o un ingegnere" and "SCIA per aprire" not in build.scope({"sue"})["pratiche"]
    text = "Solo il {{copertura}}.\n<!-- no-suap -->\nIl SUAP no.\n<!-- /no-suap -->\n<!-- suap -->\nIl SUAP sì.\n<!-- /suap -->\n"
    assert build.with_scope(text, "t", {"sue"}) == "Solo il SUE del Comune di Napoli.\nIl SUAP no.\n"
    assert build.with_scope(text, "t", {"sue", "suap"}) == "Solo il SUE e SUAP del Comune di Napoli.\nIl SUAP sì.\n"
    # Every shipped text has its placeholders filled.
    for f in [*(HERE / "impresa-in-un-minuto").rglob("*.md"), HERE / "impresa-in-un-minuto" / ".claude-plugin" / "plugin.json"]:
        left = re.findall(r"\{\{(?:copertura|comuni|città|pratiche|chi)\}\}", build.with_scope(f.read_text(), f.name))
        assert not left, (f, left)
    # A table's name says its sportello (the SUAP's table stays out while it isn't carried).
    assert build.table_sportello(Path("sue-napoli-adempimenti.yaml")) == "sue"
    assert build.table_sportello(Path("suap-napoli.yaml")) == "suap"
    print("ok: build.py's vault, python_download and sportelli switches, and private terms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
