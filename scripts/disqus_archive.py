#!/usr/bin/env python3
"""Turn a Disqus XML export into data/comments/<post-slug>.json for the static comment archive.

Usage: python3 scripts/disqus_archive.py ../faiface-github-io-*.xml.gz

Only public fields are kept (display name, date, sanitized message, reply structure).
Emails, IP addresses, deleted posts and spam never leave the export file.
"""
import gzip
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

NS = {"d": "http://disqus.com", "dsq": "http://disqus.com/disqus-internals"}
DSQ_ID = "{http://disqus.com/disqus-internals}id"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "comments"

# Tags Disqus emits in comment bodies that are safe to keep; everything else is dropped (text kept).
ALLOWED = {"p", "br", "a", "b", "strong", "i", "em", "u", "s", "code", "pre", "blockquote", "ul", "ol", "li"}
DROPPED = {"script", "style"}  # tags whose text content is dropped too


def unwrap_disqus_link(href):
    """disq.us/url?url=<target>:<tracking hash>&cuid=... -> <target>"""
    u = urlparse(href)
    if u.hostname != "disq.us":
        return href
    target = parse_qs(u.query).get("url", [href])[0]
    return re.sub(r":[A-Za-z0-9_-]{20,}$", "", target)


class Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.dropping = 0

    def handle_starttag(self, tag, attrs):
        if tag in DROPPED:
            self.dropping += 1
        if tag not in ALLOWED or self.dropping:
            return
        if tag == "a":
            # Disqus wraps links in a redirector; unwrap it so the archive links directly.
            href = unwrap_disqus_link(dict(attrs).get("href") or "")
            if not re.match(r"https?://", href):
                return self.out.append("<a>")
            return self.out.append(f'<a href="{html.escape(href)}" rel="nofollow ugc noopener">')
        self.out.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if tag in DROPPED:
            self.dropping = max(0, self.dropping - 1)
        elif tag in ALLOWED and tag != "br" and not self.dropping:
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.dropping:
            self.out.append(html.escape(data, quote=False))


def sanitize(message):
    s = Sanitizer()
    s.feed(message or "")
    s.close()
    out = "".join(s.out).strip()
    # Disqus pads code snippets with line breaks, which render as blank lines.
    out = re.sub(r"<code>(?:<br>)+", "<code>", out)
    return re.sub(r"(?:<br>)+</code>", "</code>", out)


def text(el, path):
    found = el.find(path, NS)
    return (found.text or "").strip() if found is not None else ""


def post_slug(link):
    # Disqus also made threads for translate.goog proxies, localhost previews etc.; only the real site counts.
    u = urlparse(link)
    if u.hostname != "faiface.github.io":
        return None
    m = re.fullmatch(r"/post/([^/]+)/?", u.path)
    return m.group(1) if m else None


def main(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rb") as f:
        root = ET.parse(f).getroot()

    slug_of_thread = {}
    for thread in root.findall("d:thread", NS):
        slug = post_slug(text(thread, "d:link"))
        if slug:
            slug_of_thread[thread.get(DSQ_ID)] = slug

    comments = {}
    skipped = 0
    for post in root.findall("d:post", NS):
        if text(post, "d:isDeleted") == "true" or text(post, "d:isSpam") == "true":
            skipped += 1
            continue
        slug = slug_of_thread.get(post.find("d:thread", NS).get(DSQ_ID))
        if not slug:
            skipped += 1
            continue
        parent = post.find("d:parent", NS)
        comments.setdefault(slug, []).append({
            "id": post.get(DSQ_ID),
            "parent": parent.get(DSQ_ID) if parent is not None else None,
            "author": text(post, "d:author/d:name") or "Anonymous",
            "date": text(post, "d:createdAt"),
            "message": sanitize(text(post, "d:message")),
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug, items in sorted(comments.items()):
        ids = {c["id"] for c in items}
        for c in items:
            if c["parent"] not in ids:  # reply to a deleted/spam comment: show it top-level
                c["parent"] = None
        items.sort(key=lambda c: c["date"])
        (OUT_DIR / f"{slug}.json").write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
        print(f"{slug}: {len(items)} comments")
    print(f"skipped {skipped} deleted/spam/unmatched posts")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
