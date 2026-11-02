#!/usr/bin/env python3
"""Validate all DE/RU/EN Malaika pages, translated routes, metadata and assets.

This is a staging website. Keep noindex until the final legal and content review.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://pflegehelfergmbh.github.io/Pflegehelfe_Berlin/"
LANGUAGES = {"de": "de-DE", "ru": "ru-RU", "en": "en-GB"}
errors = []


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.headings = 0
        self.images = []
        self.jsonld = False
        self.json_data = ""
        self.scripts = 0
        self.noindex = False
        self.lang = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "link":
            self.links.append(a)
        elif tag == "h1":
            self.headings += 1
        elif tag == "img":
            self.images.append(a)
        elif tag == "meta" and a.get("name", "").lower() == "robots":
            self.noindex = "noindex" in a.get("content", "").lower()
        elif tag == "script":
            self.scripts += 1
            if a.get("type") == "application/ld+json":
                self.jsonld = True

    def handle_data(self, data):
        if self.jsonld:
            self.json_data += data

    def handle_endtag(self, tag):
        if tag == "script":
            self.jsonld = False


paths = sorted(ROOT.rglob("*.html"))
route_sets = {code: set() for code in LANGUAGES}
for path in paths:
    rel = path.relative_to(ROOT).as_posix()
    code = rel.split("/", 1)[0] if rel.startswith(("ru/", "en/")) else "de"
    route = rel[len(code)+1:] if code != "de" else rel
    route_sets[code].add(route)

if not route_sets["de"]:
    errors.append("No German pages")
for code in ("ru", "en"):
    if route_sets[code] != route_sets["de"]:
        errors.append(
            f"Mismatched DE/{code.upper()} pages: "
            f"DE-only={sorted(route_sets['de'] - route_sets[code])}, "
            f"{code.upper()}-only={sorted(route_sets[code] - route_sets['de'])}"
        )

for path in paths:
    rel = path.relative_to(ROOT).as_posix()
    code = rel.split("/", 1)[0] if rel.startswith(("ru/", "en/")) else "de"
    route = rel[len(code)+1:] if code != "de" else rel
    suffix = route.removesuffix("index.html")
    urls = {k: BASE + (k + "/" if k != "de" else "") + suffix for k in LANGUAGES}
    own_url = urls[code]

    parser = Page()
    parser.feed(path.read_text(encoding="utf-8"))
    if parser.lang not in (code, LANGUAGES[code]):
        errors.append(f"{rel}: incorrect HTML lang {parser.lang!r}")
    if not parser.noindex:
        errors.append(f"{rel}: noindex missing")
    if parser.headings != 1:
        errors.append(f"{rel}: expected one H1, got {parser.headings}")
    if parser.scripts != 1:
        errors.append(f"{rel}: expected only a single JSON-LD script")

    canon = [a.get("href") for a in parser.links if a.get("rel") == "canonical"]
    if canon != [own_url]:
        errors.append(f"{rel}: incorrect canonical: {canon}")

    alternates = {a.get("hreflang"): a.get("href")
                  for a in parser.links if a.get("rel") == "alternate"}
    expected = {**urls, "x-default": urls["de"]}
    if alternates != expected:
        errors.append(f"{rel}: incorrect hreflang: {alternates} expected {expected}")

    styles = [a.get("href", "") for a in parser.links if a.get("rel") == "stylesheet"]
    if len(styles) != 1:
        errors.append(f"{rel}: expected one local stylesheet")
    for asset in [*styles, *(a.get("src", "") for a in parser.images)]:
        if not asset:
            errors.append(f"{rel}: empty asset URL")
            continue
        parsed = urlparse(asset)
        if parsed.scheme or parsed.netloc:
            errors.append(f"{rel}: unexpected remote asset {asset}")
            continue
        target = (path.parent / unquote(parsed.path)).resolve()
        if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
            errors.append(f"{rel}: missing asset {asset}")

    try:
        graph = json.loads(parser.json_data)
        nodes = graph.get("@graph", [])
        webpages = [n for n in nodes if n.get("@type") == "WebPage"]
        if len(webpages) != 1 or webpages[0].get("url") != own_url:
            errors.append(f"{rel}: incorrect WebPage structured-data URL")
        if webpages and webpages[0].get("inLanguage") != LANGUAGES[code]:
            errors.append(f"{rel}: incorrect WebPage language")
        org = [n for n in nodes if n.get("@type") == "Organization"]
        if len(org) != 1 or org[0].get("name") != "Pflegedienst Malaika GmbH":
            errors.append(f"{rel}: required business entity missing")
    except (ValueError, TypeError) as exc:
        errors.append(f"{rel}: malformed JSON-LD: {exc}")

if errors:
    print("Trilingual QA FAILED:")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print(
    "Trilingual QA passed: "
    + ", ".join(f"{len(route_sets[k])} {k.upper()}" for k in LANGUAGES)
    + " pages; canonical, hreflang, noindex, shared assets and JSON-LD validated."
)
