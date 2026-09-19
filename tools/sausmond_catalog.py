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

Optionally (--summarize), each item's OCR text derivative (the *_djvu.txt
file archive.org already generates — see e.g.
https://archive.org/stream/{identifier}/{file}_djvu.txt) is fetched, the
passage around the Sausmond mention is extracted, and an AI model turns it
into a plain-English 2-4 line summary. Works with any of three providers,
auto-detected from whichever API key is set in the environment (checked in
this order: Anthropic, OpenAI, Gemini):
  - Anthropic: `pip install anthropic`, set ANTHROPIC_API_KEY (or `ant auth
    login`). Default model: claude-opus-5.
  - OpenAI:    `pip install openai`, set OPENAI_API_KEY. Default model:
    gpt-4o-mini.
  - Gemini:    `pip install google-genai`, set GEMINI_API_KEY (or
    GOOGLE_API_KEY). Default model: gemini-2.5-flash.
Pass --summary-provider to force one explicitly, and --summary-model to
override the default model. Previously generated summaries are reused on
re-run (keyed on the underlying snippet + model) so refreshing doesn't
re-pay for unchanged documents.

Usage:
    python tools/sausmond_catalog.py
    python tools/sausmond_catalog.py --terms sausmond,sausmund,sausmont
    python tools/sausmond_catalog.py --no-fulltext
    python tools/sausmond_catalog.py --output assets/sausmond/catalog.json
    python tools/sausmond_catalog.py --summarize
    python tools/sausmond_catalog.py --summarize --summary-provider gemini

Re-run any time to pick up newly digitized documents — the Karnataka
State Archives collection on archive.org is actively growing.
"""

from __future__ import annotations

import argparse
import json
import os
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


# --- Optional: AI summaries (--summarize) ------------------------------------

def find_text_derivative(files: list[dict]) -> str | None:
    """Locate the plain-text OCR derivative archive.org already generated
    for this item (the '_djvu.txt' file), same as the one linked from the
    'Full text' view on an item's archive.org page."""
    for f in files:
        if f.get("format") == "DjVuTXT":
            return f.get("name")
    for f in files:
        if f.get("name", "").lower().endswith("_djvu.txt"):
            return f.get("name")
    return None


def fetch_full_text(identifier: str, filename: str) -> str | None:
    try:
        url = DOWNLOAD_URL.format(identifier=identifier, filename=filename)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError:
        return None


def extract_context(full_text: str, terms: list[str], window: int = 700) -> str | None:
    """Returns a window of raw OCR text around the first mention of any
    search term, for feeding to the summarizer — cheaper and more focused
    than summarizing an entire scanned book."""
    lowered = full_text.lower()
    best_pos = None
    for term in terms:
        pos = lowered.find(term.lower())
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos = pos
    if best_pos is None:
        return None
    start = max(0, best_pos - window // 2)
    end = min(len(full_text), best_pos + window // 2)
    return full_text[start:end].strip()


SUMMARY_SYSTEM_PROMPT = (
    "You summarize short excerpts of OCR'd text from historical Karnataka "
    "State Archives documents for a catalog of records mentioning a colony "
    "called Sausmond. Write 2-4 plain-English sentences describing what "
    "this specific passage says about Sausmond. Base the summary only on "
    "the text given — never invent names, dates, or events not present in "
    "it. OCR text is often garbled (misspellings, stray characters); read "
    "through minor noise, but if the passage is too corrupted to make "
    "sense of, say that plainly instead of guessing. No preamble, no "
    "markdown — plain sentences only."
)


DEFAULT_SUMMARY_MODEL = {
    "anthropic": "claude-opus-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
}
# Provider -> (module to `import`, pip package name). Gemini's is the odd one
# out: the import path (google.genai) differs from the pip package name
# (google-genai), which differs from our own --summary-provider value.
PROVIDER_MODULE = {
    "anthropic": "anthropic",
    "openai": "openai",
    "gemini": "google.genai",
}
PROVIDER_PIP_PACKAGE = {
    "anthropic": "anthropic",
    "openai": "openai",
    "gemini": "google-genai",
}


def detect_provider() -> str | None:
    """Auto-picks a provider from whichever API key is set in the
    environment, checked in this order: Anthropic, then OpenAI, then
    Gemini. Pass --summary-provider to force one explicitly instead."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    return None


def build_ai_client(provider: str):
    if provider == "anthropic":
        import anthropic
        try:
            return anthropic.Anthropic()  # resolves ANTHROPIC_API_KEY / `ant auth login` profile
        except anthropic.AnthropicError as e:
            raise RuntimeError(
                f"could not set up the Anthropic client: {e}\n"
                f"Set the ANTHROPIC_API_KEY environment variable, or run `ant auth login`."
            ) from e
    elif provider == "openai":
        import openai
        try:
            return openai.OpenAI()  # resolves OPENAI_API_KEY from the environment
        except openai.OpenAIError as e:
            raise RuntimeError(
                f"could not set up the OpenAI client: {e}\n"
                f"Set the OPENAI_API_KEY environment variable."
            ) from e
    elif provider == "gemini":
        from google import genai
        try:
            return genai.Client()  # resolves GEMINI_API_KEY, falling back to GOOGLE_API_KEY
        except Exception as e:
            raise RuntimeError(
                f"could not set up the Gemini client: {e}\n"
                f"Set the GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable."
            ) from e
    else:
        raise ValueError(f"unknown summary provider: {provider!r}")


def summarize_with_ai(provider: str, client, model: str, title: str, context: str) -> str | None:
    user_content = f'Document title: "{title}"\n\nOCR excerpt:\n"""\n{context}\n"""'

    if provider == "anthropic":
        import anthropic  # noqa: F401  (imported here so --summarize stays optional)
        try:
            response = client.messages.create(
                model=model,
                max_tokens=400,
                system=SUMMARY_SYSTEM_PROMPT,
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": user_content}],
            )
        except anthropic.APIError as e:
            print(f"  [ai] summarization failed for {title!r}: {e}")
            return None
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        return text or None

    elif provider == "openai":
        import openai  # noqa: F401  (imported here so --summarize stays optional)
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=400,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
        except openai.APIError as e:
            print(f"  [ai] summarization failed for {title!r}: {e}")
            return None
        text = (response.choices[0].message.content or "").strip()
        return text or None

    elif provider == "gemini":
        from google.genai import types as genai_types
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_content,
                config=genai_types.GenerateContentConfig(
                    system_instruction=SUMMARY_SYSTEM_PROMPT,
                    max_output_tokens=400,
                ),
            )
        except Exception as e:
            # Caught broadly: the google-genai SDK's exception hierarchy
            # isn't pinned against live docs here, so this favors skipping
            # one item over crashing the whole batch on an unexpected type.
            print(f"  [ai] summarization failed for {title!r}: {e}")
            return None
        text = (response.text or "").strip()
        return text or None

    else:
        raise ValueError(f"unknown summary provider: {provider!r}")


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


def build_catalog(
    terms: list[str], creator: str, rows: int, with_metadata: bool, use_fulltext: bool,
    summarize: bool = False, provider: str | None = None, summary_model: str | None = None,
    prev_items: dict | None = None,
) -> dict:
    ai_client = None
    ai_new, ai_reused = 0, 0
    if summarize:
        ai_client = build_ai_client(provider)
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

        ai_summary = None
        if summarize:
            prev = (prev_items or {}).get(identifier)
            if (prev and prev.get("ai_summary") and prev.get("description") == snippet
                    and prev.get("ai_model") == summary_model):
                ai_summary = prev["ai_summary"]
                ai_reused += 1
            else:
                text_filename = find_text_derivative(files)
                context = None
                if text_filename:
                    full_text = fetch_full_text(identifier, text_filename)
                    if full_text:
                        context = extract_context(full_text, terms)
                if context:
                    ai_summary = summarize_with_ai(provider, ai_client, summary_model, title, context)
                    if ai_summary:
                        ai_new += 1
                else:
                    print(f"  [ai] no readable OCR text near a match for {title!r}; skipping summary")

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
            "ai_summary": ai_summary,
            "ai_provider": provider if ai_summary else None,
            "ai_model": summary_model if ai_summary else None,
        })

    if summarize:
        print(f"  [ai] {ai_new} new summaries generated, {ai_reused} reused from the previous catalog")

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "creator_filter": creator,
        "search_terms": terms,
        "metadata_query": build_metadata_query(terms, creator),
        "fulltext_hits": len(fulltext_list),
        "metadata_only_hits": len(md_only),
        "total_found": total,
        "ai_summarized": summarize,
        "ai_provider": provider if summarize else None,
        "ai_model": summary_model if summarize else None,
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
    parser.add_argument("--summarize", action="store_true",
                         help="generate a 2-4 line AI summary per document from its OCR text. "
                              "Auto-detects the provider from whichever API key is set "
                              "(ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY / "
                              "GOOGLE_API_KEY); re-runs reuse unchanged summaries")
    parser.add_argument("--summary-provider", choices=["anthropic", "openai", "gemini"], default=None,
                         help="force a specific provider for --summarize instead of "
                              "auto-detecting from which API key is set")
    parser.add_argument("--summary-model", default=None,
                         help="model to use for --summarize (default depends on provider: "
                              "claude-opus-5 for anthropic, gpt-4o-mini for openai, "
                              "gemini-2.5-flash for gemini)")
    args = parser.parse_args()

    provider = None
    summary_model = None
    if args.summarize:
        provider = args.summary_provider or detect_provider()
        if provider is None:
            parser.error(
                "--summarize needs an API key set: export ANTHROPIC_API_KEY, OPENAI_API_KEY, "
                "or GEMINI_API_KEY (or pass --summary-provider to force one and get a clearer error)"
            )
        try:
            __import__(PROVIDER_MODULE[provider])
        except ImportError:
            parser.error(f"--summarize with provider '{provider}' requires: "
                         f"pip install {PROVIDER_PIP_PACKAGE[provider]}")
        summary_model = args.summary_model or DEFAULT_SUMMARY_MODEL[provider]

    prev_items = None
    if args.summarize and args.output.exists():
        try:
            prev_catalog = json.loads(args.output.read_text(encoding="utf-8"))
            prev_items = {item["identifier"]: item for item in prev_catalog.get("items", [])}
        except (json.JSONDecodeError, OSError):
            prev_items = None

    terms = [t.strip() for t in args.terms.split(",") if t.strip()]
    try:
        catalog = build_catalog(
            terms, args.creator, args.rows,
            with_metadata=not args.no_metadata,
            use_fulltext=not args.no_fulltext,
            summarize=args.summarize,
            provider=provider,
            summary_model=summary_model,
            prev_items=prev_items,
        )
    except RuntimeError as e:
        parser.error(str(e))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Full-text hits:   {catalog['fulltext_hits']}")
    print(f"Metadata-only:    {catalog['metadata_only_hits']}")
    print(f"Total found:      {catalog['total_found']}")
    print(f"Written to:       {args.output}")


if __name__ == "__main__":
    main()
