#!/usr/bin/env python3
"""
Merges British Newspaper Archive (BNA) search results into catalog.json.

This script has NO network code and never will. It reads a local JSON
file you've already saved by hand (see --input) — one or more raw BNA
GraphQL `searchNewspaperArticles` responses — and merges the article
previews it finds into catalog.json's `items` array, alongside (never
replacing) the archive.org-derived entries that tools/sausmond_catalog.py
already put there. tools/sausmond_catalog.py is untouched by this script
and by running it.

Why this is a separate, manual step rather than automation: BNA is a
paywalled, session-authenticated service sitting behind active bot
protection (a Cloudflare challenge page, confirmed by hand). Automating
requests against it — even just to fetch free preview snippets — means
replaying your authenticated session programmatically against a wall
built specifically to stop that, which isn't something this project
does. You fetch the input file yourself, by hand, from your own logged-in
browser; this script only ever reads the file already sitting on disk.

What gets stored per article: title, newspaper name, publication date,
and the same free preview snippet BNA's own search results page already
shows (no login needed to see that much) — never full article text,
never an AI summary. Every BNA-sourced item is marked
`"source": "bna"` / `"requires_subscription": true`, which the site
renders as a distinct "Paid source" badge with a subscription notice.
No thumbnail is ever hotlinked from BNA's servers, even though the
response includes a thumbnail URL — see the note in article_to_item().

Input format: the file does NOT need to be valid JSON on its own.
Multiple raw `{"data": {"articleSearch": {...}}}` responses may simply be
concatenated back to back with nothing but whitespace between them —
e.g. pasting one search-results page's response body after another as
you page through results. This script parses them as a stream of
concatenated JSON values (json.JSONDecoder.raw_decode in a loop), not as
one JSON document.

Each item links straight to its matching page in BNA's viewer
(`/image-viewer?issue=...&page=...&article=...&stringtohighlight=...`),
built from `articleId` and `newspaperPages[0].pageNumber` per
build_viewer_url() — confirmed against two real article URLs, not
guessed. Falls back to a generic keyword-search link only when an
article's data doesn't fit that shape.

Usage:
    python tools/bna_import.py                       # reads the default --input path
    python tools/bna_import.py --input path/to/file.json
    python tools/bna_import.py --catalog assets/sausmond/catalog.json
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# Deliberately outside the site/ repo by default, so the raw BNA export
# never sits somewhere a stray `git add -A` could catch it.
DEFAULT_INPUT = Path(__file__).resolve().parent.parent.parent / "test.json"
DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "assets" / "sausmond" / "catalog.json"
BNA_SEARCH_URL = "https://www.britishnewspaperarchive.com/search-newspapers/results"

DEFAULT_TERMS = [
    "sausmond", "sausmund", "sausmont", "sausmand",
    "sawsmond", "sawsmund", "sawsmont",
    "saussmond", "saussmund",
    "sansmond", "sansmund", "sansmont",
    "sousmond", "sousmund", "sousmont",
    "sauzmond", "souzmond",
    "zausmond", "zousmond",
]

HIGHLIGHT_SPAN_RE = re.compile(r"</?span[^>]*>", re.IGNORECASE)


def load_concatenated_json(text: str) -> list[dict]:
    """Parses one or more JSON values placed back to back with only
    whitespace between them (no commas, no enclosing array) — exactly
    what you get pasting multiple raw fetch() response bodies into one
    file, one search-results page at a time."""
    decoder = json.JSONDecoder()
    objects = []
    idx, n = 0, len(text)
    while idx < n:
        while idx < n and text[idx] in " \t\r\n":
            idx += 1
        if idx >= n:
            break
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError as e:
            line = text.count("\n", 0, idx) + 1
            raise ValueError(f"could not parse JSON starting at character {idx} (line ~{line}): {e}") from e
        objects.append(obj)
        idx = end
    return objects


def extract_articles(responses: list[dict]) -> list[dict]:
    articles = []
    for resp in responses:
        search = (resp.get("data") or {}).get("articleSearch") or {}
        articles.extend(search.get("articles") or [])
    return articles


def clean_bna_snippet(text: str) -> str:
    """BNA's own snippet already wraps the matched term in
    <span class='highlight'>...</span>. Strip that markup so our own
    highlight() re-wraps it in <mark> from matched_terms instead of
    leaving raw HTML sitting in the description field."""
    return HIGHLIGHT_SPAN_RE.sub("", text or "").strip()


def find_matches(text: str, terms: list[str]) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    return [t for t in terms if t.lower() in lowered]


def build_viewer_url(article: dict, matched_terms: list[str]) -> str | None:
    """Constructs a deep link straight to the matching page, e.g.
    https://www.britishnewspaperarchive.com/image-viewer?issue=BL%2F0003193%2F18921203&page=2&article=027&stringtohighlight=sausmond

    Confirmed against two real article URLs (not guessed): articleId
    ("BL/0003193/18921203/027") splits into `issue` (its first three
    segments) and `article` (the last); `page` is newspaperPages[0]'s
    plain (unpadded) pageNumber, which is a *different* number from the
    article segment -- they are not interchangeable. Returns None (never
    a wrong link) if the shape doesn't match what was confirmed."""
    article_id = article.get("articleId") or ""
    parts = article_id.split("/")
    if len(parts) != 4:
        return None
    pages = article.get("newspaperPages") or []
    page_number = pages[0].get("pageNumber") if pages else None
    if page_number is None:
        return None
    params = {
        "issue": "/".join(parts[:3]),
        "page": str(page_number),
        "article": parts[3],
        "stringtohighlight": matched_terms[0] if matched_terms else "sausmond",
    }
    return "https://www.britishnewspaperarchive.com/image-viewer?" + urllib.parse.urlencode(params)


def article_to_item(article: dict, terms: list[str]) -> dict:
    article_id = article.get("articleId") or article.get("id")
    title = article.get("title") or "Untitled article"
    snippet = clean_bna_snippet(article.get("textSnippet"))
    issue = article.get("newspaperIssue") or {}
    date = issue.get("publicationDate")
    matched_terms = find_matches(f"{title} {snippet}", terms)

    return {
        "rank": None,             # filled in by merge_items()
        "relevance_score": None,  # filled in by merge_items()
        "source": "bna",
        "identifier": f"bna-{article_id}",
        "title": title,
        "date": date,
        "date_is_exact": bool(date),
        "description": snippet,
        "matched_terms": matched_terms,
        "newspaper_name": issue.get("title"),
        "publication_place": issue.get("publicationPlace"),
        "requires_subscription": True,
        "department": None, "document_belongs": None, "file_no": None, "classification": None,
        "language": [], "collection": [],
        "source_url": None,
        # Generic fallback link (always valid); match_url below carries
        # the precise deep link when the data supports constructing one.
        "archive_url": f"{BNA_SEARCH_URL}?keywords=sausmond",
        "match_url": build_viewer_url(article, matched_terms),
        "pdf_url": None,
        # Deliberately never populated: even though the response includes
        # a thumbnailUri, hotlinking BNA's images onto a third-party page
        # isn't something this project does -- see the module docstring.
        "thumbnail_url": None,
        "ai_summary": None, "ai_provider": None, "ai_model": None,
    }


def merge_items(catalog: dict, new_bna_items: dict[str, dict]) -> tuple[dict, int, int]:
    """Upserts BNA items into catalog['items'] by identifier. Every
    non-BNA item is left completely untouched, in its existing position."""
    existing = catalog.setdefault("items", [])
    by_id = {item["identifier"]: item for item in existing}

    added = updated = 0
    for identifier, new_item in new_bna_items.items():
        old = by_id.get(identifier)
        if old is not None:
            changed = any(old.get(k) != new_item[k] for k in ("description", "title", "match_url"))
            old.update({k: v for k, v in new_item.items() if k not in ("rank", "relevance_score")})
            updated += 1 if changed else 0
        else:
            existing.append(new_item)
            by_id[identifier] = new_item
            added += 1

    # Recompute rank/relevance_score for the whole catalog: keep every
    # archive.org item's existing relative order, then append BNA items
    # after all of them -- a paid, unverifiable-without-login snippet is
    # weaker evidence than a confirmed full-text or metadata match, same
    # tiering logic tools/sausmond_catalog.py already applies between its
    # own two sources.
    non_bna = [it for it in existing if it["source"] != "bna"]
    bna = [it for it in existing if it["source"] == "bna"]
    ordered = non_bna + bna

    total = len(ordered)
    for rank, item in enumerate(ordered, start=1):
        item["rank"] = rank
        item["relevance_score"] = round(100 * (total - rank + 1) / total) if total else 0

    catalog["items"] = ordered
    catalog["total_found"] = total
    catalog["bna_hits"] = len(bna)
    catalog["bna_imported_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return catalog, added, updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                         help=f"path to the pasted BNA response(s) file (default: {DEFAULT_INPUT})")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG,
                         help=f"path to catalog.json to update in place (default: {DEFAULT_CATALOG})")
    parser.add_argument("--terms", default=",".join(DEFAULT_TERMS),
                         help="comma-separated terms to mark as matched within snippets")
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"input file not found: {args.input}")
    if not args.catalog.exists():
        parser.error(f"catalog file not found: {args.catalog} (run tools/sausmond_catalog.py first)")

    responses = load_concatenated_json(args.input.read_text(encoding="utf-8"))
    articles = extract_articles(responses)
    terms = [t.strip() for t in args.terms.split(",") if t.strip()]

    new_items = {}
    for article in articles:
        item = article_to_item(article, terms)
        new_items[item["identifier"]] = item  # de-dupes repeats within this same file too

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    catalog, added, updated = merge_items(catalog, new_items)

    args.catalog.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Parsed responses:   {len(responses)}")
    print(f"Articles found:     {len(articles)}")
    print(f"New BNA items:      {added}")
    print(f"Updated BNA items:  {updated}")
    print(f"Catalog total:      {catalog['total_found']} ({catalog['bna_hits']} from BNA)")
    print(f"Written to:         {args.catalog}")


if __name__ == "__main__":
    main()
