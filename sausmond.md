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
  --paid-track:     #fbe8c6;
  --paid-text:      #8a5a00;
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
    --paid-track:     #4a3510;
    --paid-text:      #e3b567;
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
.sausmond-badge-bna { background: var(--paid-track); color: var(--paid-text); }
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

.sausmond-root h2 { margin-top: 1.6em; }
.sausmond-intro ul { color: var(--text-secondary); }
.sausmond-note { font-style: italic; color: var(--text-muted); }
.sausmond-figure {
  margin: 1.2em 0;
  padding: 0.75em;
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.sausmond-figure img { display: block; width: 100%; border-radius: 4px; }
.sausmond-figure figcaption {
  margin-top: 0.6em;
  font-size: 0.85em;
  color: var(--text-muted);
}
</style>

<p class="sausmond-intro">
Sausmond was one of several large land grants made by the Maharajah of
Mysore to Anglo-Indian settlers, part of a wider effort to build
agricultural townships for the community &mdash; itself part of a much
older ambition the Maharajahs of Mysore had long held, to make Mysore a
genuinely cosmopolitan state, open to communities from across India and
beyond. Whitefield, today in a rather different form, is the best-known
survivor of those settlements; Sausmond and others like it have mostly
faded from memory, and very little research exists on what became of
them. This page is an attempt to change that: gathering what can be
traced through gazette notices, land records, and other archival
documents, and being careful to separate what is documented from what is
only remembered or assumed.
</p>

<h2>The land grant</h2>
<p class="sausmond-intro">
On 27 April 1882, the Dewan's office recorded His Highness the Maharajah's
sanction of a land grant to the Mysore Eurasian and Anglo-Indian
Association &mdash; three blocks totalling 3,025 acres and 39 guntas,
assessed at Rs. 3,574-8-0, offered on a sliding scale: free of assessment
for the first two years, a quarter assessment for the third and fourth,
half for the fifth and sixth, and full assessment from the seventh year
on. Two of the three blocks lay in Varthur Hobli, near Kadugodi railway
station, spanning the revenue villages of Nellurhalli, Nagondahalli,
Hagadur, Doddakannelli, Chikkannelli, Mallur, Gunjur, Kachamanahalli,
Halunayakanhalli, Kodati, and Chikbellandur; the third block,
Srigandhakaval, lay separately on the Magadi road and isn't connected to
Sausmond. Portions of Hagadur and Nellurhalli became Whitefield; Kodathi
village housed another of the resulting colonies, known as Duckworth
&mdash; St Anthony's Church at Kodathi is one of the oldest parish
churches in Bangalore. Sausmond itself isn't named in this order; it
appears to be one of the colonies later established within the Varthur
Hobli grant, alongside Whitefield and Duckworth, as later correspondence
in the catalog below attests.
</p>

<figure class="sausmond-figure">
<img src="/assets/sausmond/images/Microfilm_Rollno-199_V004_0189.jpg" alt="Page 41: Proceedings of the Dewan to His Highness the Maha Raja of Mysore, Revenue, dated 27 April 1882 -- the order sanctioning the land grant to the Mysore Eurasian and Anglo-Indian Association">
<figcaption>The order itself: <em>Proceedings of the Dewan to His Highness the Maha Raja of Mysore (Revenue), dated 27th April 1882.</em></figcaption>
</figure>

<figure class="sausmond-figure">
<img src="/assets/sausmond/images/Microfilm_Rollno-199_V004_0190.jpg" alt="Statement of Lands applied for by the Mysore Eurasian and Anglo-Indian Association, Bangalore -- table of villages, blocks, and acreage">
<figcaption>The accompanying statement of lands, by village and block. (<a href="https://archive.org/details/karnataka-state-archives-2026-545487/page/n189/mode/2up" target="_blank" rel="noopener">Source: Karnataka State Archives, via archive.org</a>)</figcaption>
</figure>

<h2>Title deeds traced</h2>
<p class="sausmond-intro">
Property title deeds referencing the grant have so far been traced in
three villages:
</p>
<ul class="sausmond-intro">
<li>Chikkakanneli</li>
<li>Doddakanneli</li>
<li>Chikkabellandur</li>
</ul>

<h2>Etymology</h2>
<p class="sausmond-intro">
The name itself is well attested in the contemporary press. The
<em>Madras Weekly Mail</em> explained on 20 June 1901 that "Whitefield
was named after the late D. S. White, and Sausmond after Dr. J. Sausman,
from the deep interest they took in Whitefield and Sausmond
respectively." Two other papers, over a decade earlier, independently
corroborate this: both the <em>Civil &amp; Military Gazette</em>
(Lahore, 2 January 1888) and the <em>Homeward Mail from India, China and
the East</em> (London, 23 January 1888) describe "Mr. Sausman" as "the
founder of the colony." <span class="sausmond-badge sausmond-badge-bna" style="display:inline">Paid source</span>
<span class="sausmond-note">(<a href="https://www.britishnewspaperarchive.com/search-newspapers/results?keywords=sausmond" target="_blank" rel="noopener">British Newspaper Archive</a>, subscription required &mdash; previews of all three are in the catalog below)</span>.
</p>
<p class="sausmond-intro">
Several recent-year sale deeds refer to the place as "Sasmandu" &mdash;
the Kannada rendering of Sausmond &mdash; which confirms the place name
in the documentary record, even though it is no longer used locally.
</p>

<figure class="sausmond-figure">
<img src="/assets/sausmond/images/1955-survey-map-sausmond.jpg" alt="1955 U.S. Army Map Service survey map showing Sausmond labeled between Rifle Range and Gunjur, just south of Vartur (Varthur)">
<figcaption>Sausmond, labeled by name, on a 1955 U.S. Army Map Service survey of the Bangalore area &mdash; sitting just south of Vartur (Varthur) and Whitefield, and just west of Gunjur. (<a href="https://commons.wikimedia.org/wiki/File:Map_India_and_Pakistan_1-250,000_Tile_ND_44-13_Bangalore.jpg" target="_blank" rel="noopener">Full map, public domain, via Wikimedia Commons</a>)</figcaption>
</figure>

<h2>The documents</h2>
<p class="sausmond-intro">
This page also collects every document held by the
<strong>Karnataka State Archives</strong> that mentions Sausmond. Documents
where the word appears directly in the scanned page
(<span class="sausmond-badge sausmond-badge-fulltext" style="display:inline">Full text match</span>,
shown with the actual matching sentence) are the most solid evidence and
are listed first; documents found only through their catalog description
(<span class="sausmond-badge sausmond-badge-metadata" style="display:inline">Metadata match</span>)
follow after. A few results also come from newspaper archives
(<span class="sausmond-badge sausmond-badge-bna" style="display:inline">Paid source</span>)
&mdash; these link to a subscription-only site, so the preview snippet
shown here is all that's freely visible without an account there.
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

<div id="sausmond-list"><p class="sausmond-empty">Loading&hellip;</p></div>

<p class="sausmond-intro" style="margin-top:2em; font-size:0.85em;">
Karnataka State Archives is still digitizing its records, so this list
grows over time. Curious how it's put together? See the
<a href="https://github.com/sohan6/sohan6.github.io/blob/master/tools/README.md" target="_blank" rel="noopener">technical notes</a>.
</p>

</div>

<script src="/assets/sausmond/sausmond.js" defer></script>
