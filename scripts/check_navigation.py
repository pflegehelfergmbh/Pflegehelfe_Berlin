#!/usr/bin/env python3
"""Check that Malaika's HTML navigation stays in the correct browser tab.

Site policy:
- Internal web links: same tab (target absent or _self).
- External web links: new tab (target=_blank and rel contains noopener).
- tel:, mailto:, #fragment: no tab policy.
- All current draft HTML pages must remain noindex.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import sys

ROOT = Path(__file__).resolve().parents[1]
OWN_HOSTS = {"pflegehelfergmbh.github.io", "pflegedienst-malaika.de", "www.pflegedienst-malaika.de"}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.noindex = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            self.links.append(a)
        if tag == "meta" and a.get("name", "").lower() == "robots":
            self.noindex |= "noindex" in a.get("content", "").lower()

errors = []
pages = sorted(ROOT.rglob("*.html"))
if not pages:
    errors.append("No HTML pages found")
for path in pages:
    parser = Links()
    parser.feed(path.read_text(encoding="utf-8"))
    short = str(path.relative_to(ROOT))
    if not parser.noindex:
        errors.append(f"{short}: missing noindex while site is in development")
    for link in parser.links:
        href = link.get("href", "")
        target = link.get("target", "")
        rel = (link.get("rel") or "").split()
        parsed = urlparse(href)
        if parsed.scheme in ("mailto", "tel", "sms") or href.startswith("#"):
            continue
        is_external = parsed.scheme in ("https", "http") and parsed.hostname not in OWN_HOSTS
        if is_external:
            if target != "_blank" or "noopener" not in rel:
                errors.append(f"{short}: external link {href!r} requires target=_blank and rel=noopener")
            continue
        if target not in ("", "_self"):
            errors.append(f"{short}: internal link {href!r} must stay in current tab, got {target!r}")
        if parsed.scheme in ("", "http", "https") and not parsed.netloc:
            route = unquote(parsed.path)
            if route:
                if route.startswith("/"):
                    possible = ROOT / route.lstrip("/")
                else:
                    possible = path.parent / route
                if possible.is_dir():
                    possible = possible / "index.html"
                if not possible.exists():
                    errors.append(f"{short}: internal link {href!r} points to nonexistent local path")

if errors:
    print("Navigation QA FAILED:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"Navigation QA passed: {len(pages)} HTML pages, tab policies, relative links and noindex verified.")
