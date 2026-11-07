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


class InstallPage(unittest.TestCase):
    def test_marketplace_name(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        repo = market["plugins"][0]["source"]["repo"]
        self.assertEqual(page.ids["marketplace"], repo)
        self.assertEqual(repo, "liammaher/portale-sue")

    def test_prova_phrase_is_the_skills(self):
        # The skill's description names the phrase that starts the Prova; the page must give the same.
        skill = (ROOT / "plugin" / "portale-sue" / "skills" / "portale-sue-pratica" / "SKILL.md").read_text()
        phrase = page.ids["prova"]
        self.assertIn(phrase.lower(), skill.lower())
        self.assertIn(f"«{phrase}»", (ROOT / "README.md").read_text())

    def test_every_copy_button_has_its_text(self):
        for tag, attrs in page.tags:
            if tag == "button" and "data-copy" in attrs:
                self.assertTrue(page.ids.get(attrs["data-copy"]), attrs["data-copy"])

    def test_loads_nothing_from_elsewhere(self):
        # Links are fine; nothing the browser fetches on its own (scripts, styles, images, fonts, frames).
        for tag, attrs in page.tags:
            for key in ("src", "srcset", "data", "poster"):
                self.assertNotIn(key, attrs, f"<{tag} {key}=...>")
            if tag == "link":
                self.assertTrue(attrs.get("href", "").startswith("data:"), attrs)
            if tag in ("iframe", "object", "embed", "img", "video", "audio"):
                self.fail(f"<{tag}> on the page")
        self.assertNotRegex(PAGE, r"@import|url\(\s*['\"]?https?:")

    def test_links_are_https(self):
        for tag, attrs in page.tags:
            if tag == "a":
                self.assertRegex(attrs.get("href", ""), r"^https://", attrs)

    def test_labels_of_the_italian_app(self):
        # support.claude.com/it/articles/13837440: Personalizza → Plugin → Aggiungi → Aggiungi marketplace.
        labels = re.findall(r'<span class="ui">([^<]+)</span>', PAGE)
        for label in ("Personalizza", "Plugin", "+ Aggiungi", "Aggiungi marketplace", "Installa"):
            self.assertIn(label, labels)

    def test_italian_and_not_official(self):
        self.assertRegex(PAGE, r'<html lang="it">')
        self.assertIn("Non è uno strumento ufficiale", PAGE)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
