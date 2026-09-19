---
layout: page
title: Sausmond
---

<div class="sausmond-root">
<style>
.sausmond-root {
  color-scheme: light;
  --surface-1:      #fcfcfb;
  --text-primary:   #0b0b0b;
  --text-secondary: #52514e;
  --text-muted:     #898781;
  --border:         rgba(11,11,11,0.10);
  --accent:         #2a78d6;
  --accent-track:   #cde2fb;
}
@media (prefers-color-scheme: dark) {
  .sausmond-root {
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --border:         rgba(255,255,255,0.10);
    --accent:         #3987e5;
    --accent-track:   #184f95;
  }
}

/* Widen this page's content column beyond Lanyon's narrow blog width so the
   tile grid isn't forced down to 2 per row. Scoped to this page only, since
   Jekyll renders each page as its own static file. */
.container.content { max-width: min(94vw, 1200px); }

.sausmond-intro { color: var(--text-secondary); }
.sausmond-intro code { background: var(--border); padding: 0 4px; border-radius: 3px; }

.sausmond-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75em;
  margin: 1.5em 0 1em;
  padding: 0.75em 1em;
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: 6px;
}
#sausmond-meta { color: var(--text-secondary); font-size: 0.9em; }
.sausmond-toolbar label { color: var(--text-secondary); font-size: 0.9em; margin-right: 0.4em; }
#sausmond-sort { font: inherit; padding: 0.2em 0.4em; }

.sausmond-query {
  font-size: 0.8em;
  color: var(--text-muted);
  margin: -0.5em 0 1.5em;
  word-break: break-word;
}
.sausmond-query code { color: var(--text-secondary); }

#sausmond-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1em;
}

.sausmond-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--surface-1);
}
.sausmond-card-thumb { background: var(--border); }
.sausmond-card-thumb img { display: block; width: 100%; height: 160px; object-fit: cover; }
.sausmond-card-body { padding: 1em; display: flex; flex-direction: column; gap: 0.5em; }
.sausmond-card-meta { display: flex; align-items: center; gap: 0.6em; flex-wrap: wrap; font-size: 0.8em; color: var(--text-muted); }
.sausmond-badge {
  font-size: 0.75em;
  font-weight: 600;
  padding: 0.15em 0.55em;
  border-radius: 999px;
  white-space: nowrap;
}
.sausmond-badge-fulltext { background: var(--accent-track); color: var(--accent); }
.sausmond-badge-metadata { background: var(--border); color: var(--text-secondary); }
.sausmond-card-title { margin: 0; font-size: 1.05em; line-height: 1.3; }
.sausmond-card-title a { color: var(--text-primary); text-decoration: none; }
.sausmond-card-title a:hover { text-decoration: underline; }
.sausmond-card-desc { margin: 0; font-size: 0.92em; color: var(--text-secondary); line-height: 1.45; }
.sausmond-card-desc mark { background: var(--accent-track); color: var(--text-primary); border-radius: 2px; padding: 0 2px; }

.sausmond-ai-summary {
  margin: 0;
  font-size: 0.92em;
  line-height: 1.45;
  color: var(--text-primary);
  background: var(--accent-track);
  border-radius: 6px;
  padding: 0.6em 0.75em;
}
.sausmond-ai-summary-label {
  display: block;
  font-size: 0.72em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--accent);
  margin-bottom: 0.25em;
}

.sausmond-meter { display: flex; align-items: center; gap: 0.6em; }
.sausmond-meter-track { flex: 1; height: 6px; border-radius: 3px; background: var(--accent-track); overflow: hidden; }
.sausmond-meter-fill { height: 100%; background: var(--accent); border-radius: 3px; }
.sausmond-meter-label { font-size: 0.78em; color: var(--text-muted); white-space: nowrap; }

.sausmond-card-links { font-size: 0.85em; }
.sausmond-card-links a { color: var(--accent); }

.sausmond-empty { color: var(--text-secondary); padding: 2em 0; }
</style>

<p class="sausmond-intro">
Sausmond was a small colony near Bangalore, close to Whitefield and
Duckworth &mdash; both Anglo-Indian settlements &mdash; and it turns up
again and again in early-20th-century administrative paperwork: proposals
to sink a well, a request to open a road from Sarjapur Road, correspondence
about water supply, land set aside "for building purposes" by the
Anglo-Indian Association. It left no other footprint that's easy to find
today. This page is an automatically refreshed catalog of every
<strong>Karnataka State Archives</strong> item on
<a href="https://archive.org" target="_blank" rel="noopener">archive.org</a>
that mentions Sausmond or a likely spelling variant, built from two
different Internet Archive search engines so nothing has to be found by
opening PDFs one at a time: full-text search of each document's actual
scanned OCR text (<span class="sausmond-badge sausmond-badge-fulltext" style="display:inline">Full text match</span>,
with the real matching sentence shown as a snippet), and metadata search
of titles and descriptions (<span class="sausmond-badge sausmond-badge-metadata" style="display:inline">Metadata match</span>),
for the rare document whose scan is too degraded to OCR cleanly. Full-text
matches &mdash; direct textual evidence &mdash; rank above metadata-only
ones; within each group, order follows Internet Archive's own relevance
scoring.
</p>

<div class="sausmond-toolbar">
  <span id="sausmond-meta">Loading catalog&hellip;</span>
  <span>
    <label for="sausmond-sort">Sort by</label>
    <select id="sausmond-sort">
      <option value="relevance">Relevance</option>
      <option value="date">Date</option>
    </select>
  </span>
</div>

<p class="sausmond-query">Query: <code id="sausmond-query"></code></p>

<div id="sausmond-list"><p class="sausmond-empty">Loading&hellip;</p></div>

<p class="sausmond-intro" style="margin-top:2em;">
<strong>Refreshing this catalog.</strong> The list above is generated by
<code>tools/sausmond_catalog.py</code>, a dependency-free Python script that
queries, per spelling variant, the same full-text search backend that powers
the "Full text" tab at
<a href="https://archive.org/search?sin=TXT" target="_blank" rel="noopener">archive.org/search</a>
(restricted to <code>creator:"Karnataka State Archives"</code>), falls back
to the
<a href="https://archive.org/advancedsearch.php" target="_blank" rel="noopener">Advanced Search API</a>
for anything only a curated description mentions, and enriches every hit via
the
<a href="https://archive.org/metadata/" target="_blank" rel="noopener">Metadata API</a>.
Since Karnataka State Archives is still digitizing its holdings, re-run it
any time to pick up newly added documents:
</p>

<pre><code>python tools/sausmond_catalog.py
# or, to try a wider net of spelling variants:
python tools/sausmond_catalog.py --terms sausmond,sausmund,sausmont,sawsmond
# or, to add a short AI-written summary per document: set ANTHROPIC_API_KEY
# (pip install anthropic), OPENAI_API_KEY (pip install openai), or
# GEMINI_API_KEY (pip install google-genai) and the provider is
# auto-detected. Re-runs reuse unchanged summaries, so this only pays for
# documents that are new or whose match changed.
python tools/sausmond_catalog.py --summarize
python tools/sausmond_catalog.py --summarize --summary-provider gemini  # force a provider</code></pre>

<p class="sausmond-intro">
That overwrites <code>assets/sausmond/catalog.json</code>, which this page
reads directly &mdash; commit and push the updated file to publish new
results.
</p>

</div>

<script src="/assets/sausmond/sausmond.js" defer></script>
