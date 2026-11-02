#!/usr/bin/env python3
"""Validate trilingual Malaika routes, language switching, structured data and assets.

Staging rules: every DE, RU and EN page remains noindex; local links stay in-tab.
Every published route has three equivalent pages with reciprocal hreflang entries.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://pflegehelfergmbh.github.io/Pflegehelfe_Berlin/"
LANGS = {"de": {"prefix": "", "html": "de", "schema": "de-DE"},
         "ru": {"prefix": "ru/", "html": "ru", "schema": "ru-RU"},
         "en": {"prefix": "en/", "html": "en-GB", "schema": "en-GB"}}
errors = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.headings = 0
        self.images = []
        self.jsonld = False
        self.json_data = ""
        self.script_count = 0
        self.noindex = False
        self.lang = ""
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "link":
            self.links.append(a)
        if tag == "h1":
            self.headings += 1
        if tag == "img":
            self.images.append(a)
        if tag == "meta" and a.get("name", "").lower() == "robots":
            self.noindex = "noindex" in a.get("content", "").lower()
        if tag == "script":
            self.script_count += 1
            self.jsonld = a.get("type") == "application/ld+json"
            if not self.jsonld:
                errors.append("Unexpected executable script present")
    def handle_data(self, value):
        if self.jsonld:
            self.json_data += value
    def handle_endtag(self, tag):
        if tag == "script":
            self.jsonld = False

class Switch(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.anchors.append(dict(attrs))

pages = sorted(ROOT.rglob("*.html"))
groups = {}
for code, details in LANGS.items():
    prefix = details["prefix"]
    group = set()
    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        if code == "de":
            if rel.startswith(("ru/", "en/")):
                continue
            group.add(rel)
        elif rel.startswith(prefix):
            group.add(rel[len(prefix):])
    groups[code] = group
if not groups["de"]:
    errors.append("No German pages")
for code in ("ru", "en"):
    missing = sorted(groups["de"] - groups[code])
    extra = sorted(groups[code] - groups["de"])
    if missing or extra:
        errors.append(f"Missing or extra {code} pages: missing={missing}, extra={extra}")

for code, details in LANGS.items():
    for rel in sorted(groups[code]):
        page_rel = details["prefix"] + rel
        path = ROOT / page_rel
        route = rel.removesuffix("index.html")
        urls = {key: BASE + item["prefix"] + route for key, item in LANGS.items()}
        url = urls[code]
        source = path.read_text(encoding="utf-8")
        parser = Page()
        parser.feed(source)

        def fault(message):
            errors.append(f"{page_rel}: {message}")

        if parser.lang != details["html"]:
            fault(f"wrong document lang {parser.lang!r}")
        if not parser.noindex:
            fault("noindex missing during website development")
        if parser.headings != 1:
            fault(f"expected one H1, got {parser.headings}")
        if parser.script_count != 1:
            fault(f"expected only one JSON-LD script, got {parser.script_count}")
        canonical = [x.get("href") for x in parser.links if x.get("rel") == "canonical"]
        if canonical != [url]:
            fault(f"canonical incorrect: {canonical}")
        alternates = {x.get("hreflang"): x.get("href") for x in parser.links if x.get("rel") == "alternate"}
        required = {"de": urls["de"], "ru": urls["ru"], "en": urls["en"], "x-default": urls["de"]}
        if alternates != required:
            fault(f"hreflang mismatch: {alternates}")

        match = re.search(r'<nav class="language-switch"[^>]*>[\s\S]*?</nav>', source)
        if not match:
            fault("language switch missing")
        else:
            switch = Switch()
            switch.feed(match.group(0))
            anchors = {a.get("lang"): a for a in switch.anchors}
            if set(anchors) != set(LANGS):
                fault(f"language switch incomplete: {list(anchors)}")
            for label, target in LANGS.items():
                a = anchors.get(label)
                if not a:
                    continue
                href = a.get("href", "")
                candidate = (path.parent / unquote(urlparse(href).path)).resolve()
                expected = (ROOT / target["prefix"] / route).resolve()
                if candidate != expected:
                    fault(f"{label} switch points to wrong route: {href}")
                if a.get("target", "_self") not in ("", "_self"):
                    fault(f"{label} switch opens a new tab")
                if (a.get("aria-current") == "page") != (label == code):
                    fault(f"incorrect active language {label}")

        styles = [a.get("href", "") for a in parser.links if a.get("rel") == "stylesheet"]
        if len(styles) != 1:
            fault("expected exactly one shared stylesheet")
        for asset in [*styles, *[img.get("src", "") for img in parser.images]]:
            if not asset:
                fault("empty local asset path")
                continue
            parsed = urlparse(asset)
            if parsed.scheme or parsed.netloc:
                fault(f"unexpected remote asset {asset}")
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                fault(f"missing asset {asset}")

        try:
            document = json.loads(parser.json_data)
            nodes = document.get("@graph", [])
            web = [x for x in nodes if x.get("@type") == "WebPage"]
            if len(web) != 1 or web[0].get("url") != url:
                fault("WebPage URL in JSON-LD incorrect")
            if web and web[0].get("inLanguage") != details["schema"]:
                fault("WebPage language in JSON-LD incorrect")
            org = [x for x in nodes if x.get("@type") == "Organization"]
            if len(org) != 1 or org[0].get("name") != "Pflegedienst Malaika GmbH":
                fault("Organisation entity is missing or inconsistent")
        except (ValueError, TypeError) as exc:
            fault(f"invalid structured data: {exc}")

if errors:
    print("Trilingual QA FAILED")
    for issue in errors:
        print(" -", issue)
    sys.exit(1)
print(f"Trilingual QA passed: {len(groups['de'])} routes × 3 languages = {len(pages)} HTML pages, canonical/hreflang, switch, noindex, JSON-LD and assets.")
