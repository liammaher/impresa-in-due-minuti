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
        self.assertEqual(repo, "liammaher/impresa-in-un-minuto")

    def test_prova_phrase_is_the_skills(self):
        # The skill's description names the phrase that starts the Prova; the page must give the same.
        skill = (ROOT / "plugin" / "impresa-in-un-minuto" / "skills" / "pratiche" / "SKILL.md").read_text()
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

    def test_every_text_has_its_english(self):
        # The IT/EN switch shows one of two texts, each block written twice (lang="it", lang="en"), the app's
        # button names with them. Pairs sit next to each other, with the same tag and the same buttons.
        blocks = []   # (lang, tag, [app labels inside])
        stack = []    # open elements: (tag, index in blocks or None)
        class Walk(HTMLParser):
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag in ("meta", "link", "img", "br", "input"):
                    return
                if tag != "html" and attrs.get("lang") in ("it", "en"):
                    blocks.append((attrs["lang"], tag, []))
                    stack.append((tag, len(blocks) - 1))
                else:
                    stack.append((tag, None))
                if tag == "span" and attrs.get("class") == "ui":
                    self.chip = True
                    inside = [i for _, i in stack if i is not None]
                    self.target = inside[-1] if inside else None
            def handle_endtag(self, tag):
                while stack and stack.pop()[0] != tag:
                    pass
                self.chip = False
            chip, target = False, None
            def handle_data(self, data):
                if self.chip and self.target is not None:
                    blocks[self.target][2].append(data.strip())
        Walk().feed(PAGE)
        self.assertTrue(blocks)
        langs = [b[0] for b in blocks]
        self.assertEqual(langs.count("it"), langs.count("en"))
        for it, en in zip(blocks[::2], blocks[1::2]):
            self.assertEqual((it[0], en[0]), ("it", "en"), "an it block is followed by its en block")
            self.assertEqual(it[1], en[1], it)
            self.assertEqual(len(it[2]), len(en[2]), (it, en))
        english = {label for b in blocks if b[0] == "en" for label in b[2]}
        for label in ("+ Add", "Add marketplace", "Add from a repository", "Sync", "New plugins", "+",
                      "Manage marketplaces", "Check for updates", "Remove"):
            self.assertIn(label, english)

    def test_italian_and_not_official(self):
        self.assertRegex(PAGE, r'<html lang="it">')
        self.assertIn("Non è uno strumento ufficiale", PAGE)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
