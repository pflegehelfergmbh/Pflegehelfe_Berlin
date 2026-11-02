#!/usr/bin/env python3
"""Validate all bilingual Malaika pages, canonical URLs and static HTML assets.

This is a staging site. All pages intentionally remain noindex.
German and Russian must each have a complete one-to-one route set.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://pflegehelfergmbh.github.io/Pflegehelfe_Berlin/"
errors = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.headings = []
        self.images = []
        self.jsonld = False
        self.json_data = ""
        self.noindex = False
        self.lang = ""
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "link":
            self.tags.append(a)
        if tag == "h1":
            self.headings.append(a)
        if tag == "img":
            self.images.append(a)
        if tag == "meta" and a.get("name") == "robots":
            self.noindex = "noindex" in a.get("content", "")
        if tag == "script" and a.get("type") == "application/ld+json":
            self.jsonld = True
    def handle_data(self, data):
        if self.jsonld:
            self.json_data += data
    def handle_endtag(self, tag):
        if tag == "script":
            self.jsonld = False

paths = sorted(ROOT.rglob("*.html"))
de = {str(x.relative_to(ROOT)) for x in paths if x.relative_to(ROOT).parts[0] != "ru"}
ru = {str(x.relative_to(ROOT))[3:] for x in paths if x.relative_to(ROOT).parts[0] == "ru"}
if not de:
    errors.append("No German pages")
if de != ru:
    errors.append("Mismatched DE/RU paths: DE-only=" + str(sorted(de - ru)) + " RU-only=" + str(sorted(ru - de)))
for path in paths:
    rel = path.relative_to(ROOT).as_posix()
    is_ru = rel.startswith("ru/")
    route = (rel[3:] if is_ru else rel).removesuffix("index.html")
    de_url = BASE + route
    ru_url = BASE + "ru/" + route
    url = ru_url if is_ru else de_url
    parser = Page()
    source = path.read_text(encoding="utf-8")
    parser.feed(source)
    if parser.lang != ("ru" if is_ru else "de"):
        errors.append(rel + ": invalid html lang")
    if not parser.noindex:
        errors.append(rel + ": noindex missing")
    if len(parser.headings) != 1:
        errors.append(rel + ": expected one H1, found " + str(len(parser.headings)))
    if '<script' in source.replace('<script type="application/ld+json">', ""):
        errors.append(rel + ": additional script detected")
    canon = [x.get("href") for x in parser.tags if x.get("rel") == "canonical"]
    if canon != [url]:
        errors.append(rel + ": canonical does not match own URL")
    alternates = {x.get("hreflang"): x.get("href") for x in parser.tags if x.get("rel") == "alternate"}
    if alternates != {"de": de_url, "ru": ru_url, "x-default": de_url}:
        errors.append(rel + ": reciprocal hreflang missing or mismatched: " + str(alternates))
    styles = [x.get("href", "") for x in parser.tags if x.get("rel") == "stylesheet"]
    if len(styles) != 1:
        errors.append(rel + ": expected one shared local stylesheet")
    for asset in [*styles, *[img.get("src", "") for img in parser.images]]:
        if not asset:
            errors.append(rel + ": empty asset URL")
            continue
        parsed = urlparse(asset)
        if parsed.scheme or parsed.netloc:
            errors.append(rel + ": unexpected remote asset " + asset)
            continue
        target = (path.parent / unquote(parsed.path)).resolve()
        if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
            errors.append(rel + ": missing asset " + asset)
    try:
        graph = json.loads(parser.json_data)
        nodes = graph.get("@graph", [])
        webpages = [n for n in nodes if n.get("@type") == "WebPage"]
        if len(webpages) != 1 or webpages[0].get("url") != url:
            errors.append(rel + ": structured WebPage URL incorrect")
        if webpages and webpages[0].get("inLanguage") != ("ru-RU" if is_ru else "de-DE"):
            errors.append(rel + ": structured page language incorrect")
        org = [n for n in nodes if n.get("@type") == "Organization"]
        if len(org) != 1 or org[0].get("name") != "Pflegedienst Malaika GmbH":
            errors.append(rel + ": business entity missing")
    except (ValueError, TypeError) as e:
        errors.append(rel + ": malformed JSON-LD: " + str(e))
if errors:
    print("Bilingual QA FAILED")
    for err in errors:
        print("-", err)
    sys.exit(1)
print(f"Bilingual QA passed: {len(de)} German + {len(ru)} Russian pages, correct canonical/hreflang/noindex, accessible assets.")
