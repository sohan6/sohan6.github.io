#!/usr/bin/env python3
"""
Refreshable cataloger for "Sausmond" — a colony referenced in Karnataka
State Archives records (the earliest known mention: an 1915-16 letter from
a retired Madras Public Works Department engineer, proposing improvements
to its water supply).

Queries TWO separate Internet Archive search backends, restricted to
creator "Karnataka State Archives", matching "Sausmond" or its likely
spelling variants — so nothing has to be found by opening PDFs one at a
time:

  1. The full-text search backend ("fts") — the same one that powers the
     "Full text" tab on https://archive.org/search. It searches archive.org's
     OCR'd text of every page (the *_hocr_searchtext.txt.gz derivative each
     item already has — no re-OCRing on our end), and returns a relevance
     score plus the actual matching sentence as a snippet. This is the
     primary, most trustworthy signal: the word verifiably appears in the
     scanned document itself.

  2. The metadata/advancedsearch backend — searches titles, descriptions,
     and other catalog fields. This catches items whose OCR is too poor to
     match (e.g. handwritten letters) but whose human-curated description
     names Sausmond explicitly.

A document found by full-text search ranks above one found only via
metadata, since the former is direct textual evidence. Within each group,
Internet Archive's own relevance scoring decides order.

Note: the full-text endpoint (services/search/beta/page_production) is
undocumented and marked "beta" by Internet Archive itself — it is the
same endpoint archive.org's own web UI calls, reverse-engineered from the
public `@internetarchive/search-service` npm package, but it could change
without notice. If it starts failing, re-run with --no-fulltext to fall
back to metadata-only search.

Usage:
    python tools/sausmond_catalog.py
    python tools/sausmond_catalog.py --terms sausmond,sausmund,sausmont
    python tools/sausmond_catalog.py --no-fulltext
    python tools/sausmond_catalog.py --output assets/sausmond/catalog.json

Re-run any time to pick up newly digitized documents — the Karnataka
State Archives collection on archive.org is actively growing.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ADVANCED_SEARCH_URL = "https://archive.org/advancedsearch.php"
FTS_SEARCH_URL = "https://archive.org/services/search/beta/page_production/"
METADATA_URL = "https://archive.org/metadata/{identifier}"
DETAILS_URL = "https://archive.org/details/{identifier}"
THUMBNAIL_URL = "https://archive.org/services/img/{identifier}"
DOWNLOAD_URL = "https://archive.org/download/{identifier}/{filename}"

DEFAULT_CREATOR = "Karnataka State Archives"
DEFAULT_TERMS = [
    "sausmond", "sausmund", "sausmont", "sausmand",
    "sawsmond", "sawsmund", "sawsmont",
    "saussmond", "saussmund",
    "sansmond", "sansmund", "sansmont",
    "sousmond", "sousmund", "sousmont",
    "sauzmond", "souzmond",
    "zausmond", "zousmond",
]
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "sausmond" / "catalog.json"
USER_AGENT = "sausmond-catalog/1.0 (+https://github.com/sohan6/sohan6.github.io)"

METADATA_SEARCH_FIELDS = [
    "identifier", "title", "creator", "date", "description",
    "subject", "publicdate", "mediatype", "collection",
]


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --- Backend 1: metadata / advancedsearch -----------------------------------

def build_metadata_query(terms: list[str], creator: str) -> str:
    term_clause = " OR ".join(terms)
    return f'creator:"{creator}" AND ({term_clause})'


def metadata_search(terms: list[str], creator: str, rows: int) -> list[dict]:
    query = build_metadata_query(terms, creator)
    params = [("q", query), ("rows", str(rows)), ("output", "json")]
    for field in METADATA_SEARCH_FIELDS:
        params.append(("fl[]", field))
    url = ADVANCED_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    data = _get_json(url)
    return data.get("response", {}).get("docs", [])


# --- Backend 2: full-text search (the "Full text" tab's real API) -----------

def fts_search_term(term: str, creator: str, hits_per_page: int = 100) -> list[dict]:
    """One query against the archive.org full-text-inside-documents backend.
    Only ever queried with a single bare term — the endpoint does not
    reliably support boolean OR syntax, so variants are looped by the caller.
    """
    filter_map = json.dumps({"creator": {creator.lower(): "inc"}})
    all_hits: list[dict] = []
    page = 1
    while page <= 5:  # safety cap; a single spelling variant shouldn't need more
        params = {
            "service_backend": "fts",
            "user_query": term,
            "filter_map": filter_map,
            "hits_per_page": str(hits_per_page),
            "page": str(page),
        }
        url = FTS_SEARCH_URL + "?" + urllib.parse.urlencode(params)
        data = _get_json(url)
        hits = data.get("response", {}).get("body", {}).get("hits", {}).get("hits", [])
        all_hits.extend(hits)
        if len(hits) < hits_per_page:
            break
        page += 1
    return all_hits


def clean_snippet(text: str) -> str:
    return text.replace("{{{", "").replace("}}}", "").strip()


# --- Enrichment & assembly ----------------------------------------------------

def fetch_metadata(identifier: str) -> dict:
    try:
        return _get_json(METADATA_URL.format(identifier=identifier))
    except (urllib.error.URLError, json.JSONDecodeError):
        return {}


def first_pdf_filename(files: list[dict]) -> str | None:
    for f in files:
        name = f.get("name", "")
        fmt = f.get("format", "")
        if fmt == "Image Container PDF" or (name.lower().endswith(".pdf") and "text" not in name.lower()):
            return name
    for f in files:
        if f.get("name", "").lower().endswith(".pdf"):
            return f.get("name")
    return None


YEAR_RE = re.compile(r"(1[7-9]\d{2}|20\d{2})")


def guess_year_from_title(title: str) -> str | None:
    """Many bulk-uploaded Karnataka State Archives items have no structured
    date field, but their filename embeds one (e.g. 'LB-B-47-2-1915-16.pdf').
    Used only as a display fallback when metadata has no real date."""
    match = YEAR_RE.search(title or "")
    return match.group(1) if match else None


def find_matches(text: str, terms: list[str]) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    return [t for t in terms if t.lower() in lowered]


def collect_fulltext_hits(terms: list[str], creator: str) -> dict:
    """Runs one full-text query per term, dedupes by file_basename (falling
    back to identifier) so the same underlying scan uploaded twice under
    different archive.org identifiers only shows up once, and keeps the
    highest-scoring hit plus the union of matched terms for each document.
    """
    best: dict[str, dict] = {}
    for term in terms:
        try:
            hits = fts_search_term(term, creator)
        except (urllib.error.URLError, json.JSONDecodeError):
            continue
        for hit in hits:
            fields = hit.get("fields", {})
            key = fields.get("file_basename") or fields.get("identifier")
            score = hit.get("_score", 0)
            existing = best.get(key)
            if existing is None or score > existing["_score"]:
                highlights = hit.get("highlight", {}).get("text", [])
                snippet = clean_snippet(highlights[0]) if highlights else ""
                matched = existing["matched_terms"] if existing else set()
                matched = matched | {term}
                best[key] = {
                    "identifier": fields.get("identifier"),
                    "title": fields.get("title"),
                    "date": fields.get("date"),
                    "snippet": snippet,
                    "match_url": "https://archive.org" + hit["fields"].get("__href__", "") if fields.get("__href__") else None,
                    "_score": score,
                    "matched_terms": matched,
                }
            else:
                best[key]["matched_terms"] = best[key]["matched_terms"] | {term}
    return best


def build_catalog(terms: list[str], creator: str, rows: int, with_metadata: bool, use_fulltext: bool) -> dict:
    fulltext_hits = collect_fulltext_hits(terms, creator) if use_fulltext else {}
    fulltext_list = sorted(fulltext_hits.values(), key=lambda h: h["_score"], reverse=True)
    fulltext_ids = {h["identifier"] for h in fulltext_list}

    try:
        md_docs = metadata_search(terms, creator, rows)
    except (urllib.error.URLError, json.JSONDecodeError):
        md_docs = []
    md_only = [d for d in md_docs if d["identifier"] not in fulltext_ids]

    merged = [{"source": "fulltext", **h} for h in fulltext_list] + \
             [{"source": "metadata", **d} for d in md_only]
    total = len(merged)
    items = []

    for rank, entry in enumerate(merged, start=1):
        identifier = entry["identifier"]
        meta = fetch_metadata(identifier) if with_metadata else {}
        m = meta.get("metadata", {})
        files = meta.get("files", [])

        title = m.get("title") or entry.get("title") or identifier
        date = (m.get("date") or entry.get("date") or "")[:10]
        date_is_exact = bool(date)
        if not date:
            date = guess_year_from_title(title)
        collection = m.get("collection") or entry.get("collection") or []
        if isinstance(collection, str):
            collection = [collection]

        if entry["source"] == "fulltext":
            snippet = entry["snippet"]
            matched_terms = sorted(entry["matched_terms"])
        else:
            snippet = (m.get("description") or entry.get("description") or "").strip()
            matched_terms = find_matches(f"{title} {snippet}", terms)

        pdf_name = first_pdf_filename(files)
        pdf_url = DOWNLOAD_URL.format(identifier=identifier, filename=pdf_name) if pdf_name else None
        relevance_score = round(100 * (total - rank + 1) / total) if total else 0

        items.append({
            "rank": rank,
            "relevance_score": relevance_score,
            "source": entry["source"],
            "identifier": identifier,
            "title": title,
            "date": date or None,
            "date_is_exact": date_is_exact,
            "description": snippet,
            "matched_terms": matched_terms,
            "department": m.get("ksa_department"),
            "document_belongs": m.get("ksa_document_belongs"),
            "file_no": m.get("ksa_file_no_"),
            "classification": m.get("ksa_classification"),
            "language": m.get("language") or [],
            "collection": collection,
            "source_url": m.get("ksa_document_url") or m.get("source"),
            "archive_url": DETAILS_URL.format(identifier=identifier),
            "match_url": entry.get("match_url"),
            "pdf_url": pdf_url,
            "thumbnail_url": THUMBNAIL_URL.format(identifier=identifier),
        })

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "creator_filter": creator,
        "search_terms": terms,
        "metadata_query": build_metadata_query(terms, creator),
        "fulltext_hits": len(fulltext_list),
        "metadata_only_hits": len(md_only),
        "total_found": total,
        "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terms", default=",".join(DEFAULT_TERMS),
                         help="comma-separated spelling variants to search for")
    parser.add_argument("--creator", default=DEFAULT_CREATOR, help="archive.org creator filter")
    parser.add_argument("--rows", type=int, default=200, help="max metadata-search results to fetch")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="path to write catalog.json")
    parser.add_argument("--no-metadata", action="store_true",
                         help="skip per-item metadata enrichment (faster, less detail)")
    parser.add_argument("--no-fulltext", action="store_true",
                         help="skip the full-text search backend, use metadata search only")
    args = parser.parse_args()

    terms = [t.strip() for t in args.terms.split(",") if t.strip()]
    catalog = build_catalog(
        terms, args.creator, args.rows,
        with_metadata=not args.no_metadata,
        use_fulltext=not args.no_fulltext,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Full-text hits:   {catalog['fulltext_hits']}")
    print(f"Metadata-only:    {catalog['metadata_only_hits']}")
    print(f"Total found:      {catalog['total_found']}")
    print(f"Written to:       {args.output}")


if __name__ == "__main__":
    main()
