#!/usr/bin/env python3
"""build.py's vault switch, offline: the marked parts each build keeps, the markers it refuses,
and the hand-written plugin both ways (no setup skill and no word of the archive without it).

  python3 plugin/test_build.py      (needs PyYAML, as build.py does)
"""

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
        said = pin_marketplace.marketplace("0.1.0", "0" * 64, vault=vault)["plugins"][0]["description"]
        assert ("vault" in said) == vault, said

    with tempfile.TemporaryDirectory() as tmp:
        for vault in (True, False):
            plugin = Path(tmp) / str(vault)
            shutil.copytree(HERE / "portali", plugin)
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
        shutil.copytree(HERE / "portali", plugin)
        (plugin / "skills" / "portali-pratica" / "EXTRA.md").write_text("run pvault status\n")
        try:
            build.select_vault(plugin, False)
        except SystemExit:
            pass
        else:
            raise AssertionError("a no-vault build kept a text that names pvault")
    print("ok: build.py's vault switch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
