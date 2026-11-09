#!/usr/bin/env python3
"""The install page (site/index.html): what it tells the tecnico to paste and type is what the
marketplace and the skill take, and the page loads nothing from anywhere else.

  python3 site/test_site.py      (standard library only)
"""

import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAGE = (HERE / "index.html").read_text(encoding="utf-8")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.tags, self._open = {}, [], None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if "id" in attrs:
            self._open = attrs["id"]
            self.ids[self._open] = ""

    def handle_endtag(self, tag):
        self._open = None

    def handle_data(self, data):
        if self._open:
            self.ids[self._open] += data


page = Page()
page.feed(PAGE)


def png_size(path):
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


class InstallPage(unittest.TestCase):
    def test_marketplace_name(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        repo = market["plugins"][0]["source"]["repo"]
        self.assertEqual(page.ids["marketplace"], repo)
        self.assertEqual(repo, "liammaher/portali")

    def test_prova_phrase_is_the_skills(self):
        # The skill's description names the phrase that starts the Prova; the page must give the same.
        skill = (ROOT / "plugin" / "portali" / "skills" / "pratiche" / "SKILL.md").read_text()
        phrase = page.ids["prova"]
        self.assertIn(phrase.lower(), skill.lower())
        self.assertIn(f"«{phrase}»", (ROOT / "README.md").read_text())

    def test_every_copy_button_has_its_text(self):
        for tag, attrs in page.tags:
            if tag == "button" and "data-copy" in attrs:
                self.assertTrue(page.ids.get(attrs["data-copy"]), attrs["data-copy"])

    def test_loads_nothing_from_elsewhere(self):
        # Links are fine; nothing the browser fetches on its own (scripts, styles, fonts, frames) but
        # the page's own screenshots, served next to it from site/img/.
        for tag, attrs in page.tags:
            for key in ("src", "srcset", "data", "poster"):
                if tag == "img" and key == "src":
                    self.assertRegex(attrs["src"], r"^img/[a-z0-9-]+\.png$", attrs)
                else:
                    self.assertNotIn(key, attrs, f"<{tag} {key}=...>")
            if tag == "link":
                self.assertTrue(attrs.get("href", "").startswith("data:"), attrs)
            if tag in ("iframe", "object", "embed", "video", "audio"):
                self.fail(f"<{tag}> on the page")
        self.assertNotRegex(PAGE, r"@import|url\(\s*['\"]?https?:")

    def test_screenshots(self):
        # Each screenshot exists at twice the size the page gives it (no jump while it loads), says in Italian
        # what it shows, and site/img/ holds nothing the page doesn't show: everything there is published.
        shown = set()
        for tag, attrs in page.tags:
            if tag != "img":
                continue
            path = HERE / attrs["src"]
            self.assertTrue(path.is_file(), path)
            # Twice the size it is shown at: a 1x screenshot is blurry on a Retina screen.
            self.assertEqual(png_size(path), (2 * int(attrs["width"]), 2 * int(attrs["height"])), path)
            self.assertGreater(len(attrs.get("alt", "")), 20, attrs)
            shown.add(path.name)
        self.assertTrue(shown)
        self.assertEqual(shown, {p.name for p in (HERE / "img").iterdir()})

    def test_links_are_https(self):
        for tag, attrs in page.tags:
            if tag == "a":
                self.assertRegex(attrs.get("href", ""), r"^https://", attrs)

    def test_labels_of_the_italian_app(self):
        # As read in claude.ai set to italiano (Italia), and its it-IT strings, on 2026-11-07 («+»: 11-08). The help
        # article says «Personalizza»; the app says «Personalizzazione».
        labels = re.findall(r'<span class="ui"[^>]*>([^<]+)</span>', PAGE)
        for label in ("+ Aggiungi", "Aggiungi marketplace", "Aggiungi da un repository", "Sincronizza",
                      "Nuovi plugin", "+", "Gestisci marketplace", "Verifica aggiornamenti", "Rimuovi"):
            self.assertIn(label, labels)

    def test_every_label_has_its_english(self):
        # The IT/EN switch swaps each label for the English app's; a label without one would stay Italian.
        for tag, attrs in page.tags:
            if tag == "span" and attrs.get("class") == "ui":
                self.assertIn("data-en", attrs, attrs)

    def test_italian_and_not_official(self):
        self.assertRegex(PAGE, r'<html lang="it">')
        self.assertIn("Non è uno strumento ufficiale", PAGE)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
