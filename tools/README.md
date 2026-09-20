# Sausmond catalog — technical notes

This is the technical documentation for `sausmond_catalog.py`, the script
behind the [Sausmond catalog page](/sausmond/). The page itself stays
non-technical for general readers; everything about how the data is
gathered, refreshed, and (optionally) AI-summarized lives here.

## What it does

Queries two separate Internet Archive search backends, restricted to
`creator:"Karnataka State Archives"`, matching "Sausmond" or a list of
likely spelling variants (edit `DEFAULT_TERMS` at the top of the script to
change these):

1. **Full-text search** (`service_backend=fts`) — the same backend that
   powers the "Full text" tab at `archive.org/search?sin=TXT`. It searches
   archive.org's OCR'd text of every page (the `*_hocr_searchtext.txt.gz`
   derivative each item already has — nothing is re-OCR'd locally) and
   returns a relevance score plus the actual matching sentence as a
   snippet. This is the primary, most trustworthy signal, since the word
   verifiably appears in the scanned document itself.

   **This endpoint is undocumented.** It's `https://archive.org/services/
   search/beta/page_production/`, reverse-engineered by pulling apart
   archive.org's own production JS bundle and cross-referencing the public
   `@internetarchive/search-service` npm package (which is where the
   request shape — `service_backend`, `user_query`, `filter_map`,
   `hits_per_page`, `page` — comes from). It's marked "beta" by Internet
   Archive itself and could change or break without notice. If it starts
   failing, re-run with `--no-fulltext` to fall back to metadata-only
   search.

   One quirk: the `filter_map` creator value must be **lowercase**
   (`{"creator": {"karnataka state archives": "inc"}}`) — the mixed-case
   form silently returns zero hits.

2. **Metadata search** (`archive.org/advancedsearch.php`, documented and
   stable) — searches titles, descriptions, and other catalog fields.
   This catches items whose OCR is too poor to match (e.g. handwritten
   letters) but whose human-curated description names Sausmond explicitly.

A document found by full-text search ranks above one found only via
metadata, since the former is direct textual evidence. Within each group,
order follows the backend's own relevance scoring. Documents that were
uploaded to archive.org twice under different identifiers (this happens —
Karnataka State Archives' collection has some duplicate batches) are
de-duplicated by `file_basename`, keeping the higher-scoring copy.

Every result is then enriched via the (documented) Metadata API
(`archive.org/metadata/{identifier}`) for fields like department, file
number, and a direct link back to the original source at
`archives.karnataka.gov.in`.

## Requirements

Zero dependencies for the core catalog — stdlib `urllib` only. Python
3.10+ (uses `X | None` type hints and the `match`-free but 3.10-flavored
syntax throughout).

## CLI reference

```
python tools/sausmond_catalog.py [options]

--terms TERMS              comma-separated spelling variants to search for
--creator CREATOR          archive.org creator filter (default: "Karnataka State Archives")
--rows ROWS                max metadata-search results to fetch (default: 200)
--output OUTPUT             path to write catalog.json (default: assets/sausmond/catalog.json)
--no-metadata               skip per-item metadata enrichment (faster, less detail)
--no-fulltext                skip the full-text search backend, use metadata search only
```

Re-run any time to pick up newly digitized documents — the Karnataka State
Archives collection on archive.org is actively growing (it was 1 document
on the first run of this script, 59+ within days).

## Optional: AI summaries (`--summarize`)

Each item's OCR text derivative (the `*_djvu.txt` file archive.org already
generated — e.g. `archive.org/stream/{identifier}/{file}_djvu.txt`) is
fetched, the passage around the Sausmond mention is extracted (±350
characters), and an AI model turns it into a 2-4 sentence plain-English
summary, grounded only in that excerpt.

```
--summarize                  turn AI summaries on
--summary-provider {anthropic,openai,gemini,groq}
                              force a provider instead of auto-detecting
--summary-model MODEL        override the provider's default model
--summary-batch-size N       documents summarized per API request (default: 10)
--summary-delay SECONDS      pause between batch requests (default: 0)
```

### Providers

Auto-detected from whichever API key is set in the environment, checked in
this order: Anthropic, OpenAI, Gemini, Groq.

| Provider | Env var | Install | Default model |
|---|---|---|---|
| Anthropic | `ANTHROPIC_API_KEY` (or `ant auth login`) | `pip install anthropic` | `claude-opus-5` |
| OpenAI | `OPENAI_API_KEY` | `pip install openai` | `gpt-4o-mini` |
| Gemini | `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | `pip install google-genai` | `gemini-3.6-flash` |
| Groq | `GROQ_API_KEY` | `pip install groq` | `llama-3.1-8b-instant` |

None of these keys are ever hardcoded, logged, or written to
`catalog.json` — only the resulting summary text (and which
provider/model produced it, for cache-busting) is saved.

**Model names drift.** Providers retire and rename models; a hardcoded
default here can go stale (this has already happened twice — Gemini's
`gemini-2.5-flash` and Groq's `llama-3.3-70b-versatile` both 404'd within
days of being set as defaults). If `--summarize` fails with a 404 or
"model not found," the fix is `--summary-model <current-model-id>`, found
via:
- Anthropic: [docs.anthropic.com](https://docs.anthropic.com) or the
  Console.
- OpenAI/Groq: their `/models` list endpoint with your key, e.g.
  `curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"`
  — this reflects your account's actual access, which can differ from
  what a provider's docs page shows.
- Gemini: the error message itself typically names the replacement model.

Not every model on a provider is a fit — skip audio (`whisper-*`),
text-to-speech (e.g. `orpheus-*`), and classifier/guard models (e.g.
`llama-prompt-guard-*`, `*-safeguard-*`); they don't do open-ended text
generation. Agentic wrappers (e.g. Groq's `compound`/`compound-mini`) can
also misbehave here since they may try to invoke tools mid-response
instead of returning the plain JSON this script expects.

### Batching and rate limits

Free/low tiers commonly cap **requests** per minute/day (RPM/RPD) well
before they cap tokens — observed directly on Gemini's free tier (6/5 RPM,
21/20 RPD hit while using under 1% of the token quota). So the script
batches multiple documents into one request (`--summary-batch-size`,
default 10) instead of firing one request per document, and can pace
those requests with `--summary-delay`. For ~50-60 documents on a 5 RPM /
20 RPD cap:

```
python tools/sausmond_catalog.py --summarize --summary-batch-size 8 --summary-delay 15
```

The batch request asks the model to return a JSON array
(`[{"id": "...", "summary": "..."}, ...]`); the parser tolerates markdown
code fences and surrounding prose, and any document the model doesn't
return a valid entry for is simply retried on the next `--summarize` run
rather than treated as a failure.

### Caching

Re-running `--summarize` loads the previous `catalog.json` and reuses a
document's existing summary if its underlying snippet and the requested
model are both unchanged — so refreshing only pays for documents that are
new, or whose matched passage changed. Switching `--summary-provider` /
`--summary-model` invalidates the cache for every item (by design), since
a different model's output shouldn't silently masquerade as another's.

## `catalog.json` schema

```
{
  "generated_at": "2026-09-19T14:24:06Z",
  "creator_filter": "Karnataka State Archives",
  "search_terms": [...],
  "metadata_query": "...",       // the raw advancedsearch.php query string used
  "fulltext_hits": 56,
  "metadata_only_hits": 0,
  "total_found": 56,
  "ai_summarized": true,
  "ai_provider": "groq",
  "ai_model": "openai/gpt-oss-20b",
  "items": [
    {
      "rank": 1,
      "relevance_score": 100,      // 0-100, rank-derived
      "source": "fulltext" | "metadata",
      "identifier": "...",         // archive.org item identifier
      "title": "...",
      "date": "1915" | "1915-01-01" | null,
      "date_is_exact": true,       // false if backfilled from the filename
      "description": "...",        // OCR snippet (fulltext) or curated description (metadata)
      "matched_terms": [...],
      "department": "...", "document_belongs": "...", "file_no": "...", "classification": "...",
      "language": [...], "collection": [...],
      "source_url": "...",         // original archives.karnataka.gov.in link, when available
      "archive_url": "...",        // archive.org/details/{identifier}
      "match_url": "...",          // deep link to the matching page, when available
      "pdf_url": "...", "thumbnail_url": "...",
      "ai_summary": "..." | null,
      "ai_provider": "...", "ai_model": "..."
    }
  ]
}
```

`sausmond.js` reads this file directly at `/assets/sausmond/catalog.json`
— no server, no build step. Commit and push the regenerated file to
publish new results.

## `tools/bna_import.py` — British Newspaper Archive results (manual only)

A **separate** script from `sausmond_catalog.py`, which it never modifies
and never calls. It has no network code at all.

**Why it's manual.** British Newspaper Archive (BNA) is a paywalled,
session-authenticated service sitting behind active bot protection (a
Cloudflare challenge page, confirmed by hand — even a plain HTTP request
with a normal browser user-agent gets a "Security Check" page, not the
search results). Automating requests against it — even just to fetch the
free preview snippets a search already shows — would mean replaying an
authenticated session programmatically against a wall built specifically
to stop that. This project doesn't do that. Instead:

1. You browse BNA yourself, logged into your own account, and save the
   raw response body of each search-results page you want indexed into a
   local file (outside the repo — `../test.json` relative to `tools/` by
   default). It doesn't need to be valid JSON as a whole; pasting
   multiple raw response bodies back to back with just whitespace between
   them is fine — the script parses concatenated JSON values, not one
   document.
2. You run `python tools/bna_import.py` yourself, locally. It reads that
   file and merges what it finds into `catalog.json`, without touching
   any existing (non-BNA) item.
3. The input file is never committed (`test.json` and `bna_export*.json`
   are gitignored as a safety net, on top of already living outside the
   repo by default) — only the merged `catalog.json` is.

**What's stored per article**: title, newspaper name, publication place,
publication date, and the free preview snippet BNA's own search results
already show (no login needed to see that much — it's literally in the
public search response). Never full article text, never an AI summary.
Every BNA item gets `"source": "bna"` and `"requires_subscription": true`,
which the page renders as a distinct amber "Paid source" badge plus a
"subscription required" note instead of the usual PDF/source links.

**What's deliberately *not* stored**: a thumbnail URL. The GraphQL
response includes one (`newspaperPages[].thumbnailUri`, on BNA's own
domain), but hotlinking it would mean embedding BNA's image assets on a
third-party page, which is a step further than showing text you already
have a citation for — so `thumbnail_url` is always `null` for BNA items.

**Per-article deep links.** BNA's search API doesn't return a direct
permalink, only internal ids (`articleId`, shaped like
`BL/0003193/18921203/027`) — but `build_viewer_url()` constructs the
real article URL from it, confirmed against two actual URLs pasted from
a browser rather than guessed:

```
https://www.britishnewspaperarchive.com/image-viewer?issue=BL%2F0003193%2F18921203&page=2&article=027&stringtohighlight=sausmond
```

`issue` is `articleId`'s first three segments (`BL/0003193/18921203`),
`article` is the last (`027`), and — this is the part that isn't
guessable from `articleId` alone — `page` is the *separate*
`newspaperPages[0].pageNumber` field (confirmed `2` for both example
URLs; the trailing `articleId` segment is an article index within the
issue, not a page number, and the two numbers can differ). If an
article's data doesn't fit that shape (missing `newspaperPages`, or
`articleId` with an unexpected number of segments), it falls back to the
general keyword search
(`britishnewspaperarchive.com/search-newspapers/results?keywords=sausmond`)
rather than emit a link that might be wrong.

**Idempotent.** Re-running with the same input changes nothing (0 new, 0
updated) — matched by identifier (`bna-{articleId}`), and only the
description/title changing counts as an update. Safe to run repeatedly
as you gather more search-result pages.

**Ranking.** BNA items are appended after every archive.org-sourced item
(full-text and metadata alike) and ranked among themselves by input
order — a paid, unverifiable-without-login snippet is treated as weaker
evidence than a confirmed full-text or metadata match, extending the same
source-tiering logic `sausmond_catalog.py` already applies between its
own two backends.

```
python tools/bna_import.py                        # reads ../test.json by default
python tools/bna_import.py --input path/to/file.json
python tools/bna_import.py --catalog assets/sausmond/catalog.json
python tools/bna_import.py --terms sausmond,sansmond,sausmand
```
