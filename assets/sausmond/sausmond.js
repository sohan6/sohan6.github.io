(function () {
  "use strict";

  var CATALOG_URL = "/assets/sausmond/catalog.json";

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function highlight(text, terms) {
    var escaped = escapeHtml(text);
    if (!terms || !terms.length) return escaped;
    var sorted = terms.slice().sort(function (a, b) { return b.length - a.length; });
    var pattern = sorted.map(function (t) {
      return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }).join("|");
    if (!pattern) return escaped;
    var re = new RegExp("(" + pattern + ")", "gi");
    return escaped.replace(re, "<mark>$1</mark>");
  }

  function formatDate(item) {
    if (!item.date) return "Undated";
    return item.date_is_exact ? item.date : "c. " + item.date;
  }

  function card(item) {
    var el = document.createElement("article");
    el.className = "sausmond-card";

    var title = item.title || item.identifier;
    var desc = item.description || "No description available.";
    var dept = [item.department, item.document_belongs].filter(Boolean).join(" · ");
    var primaryLink = item.match_url || item.archive_url;
    var sourceLabel = item.source === "fulltext" ? "Full text match" : "Metadata match";
    var sourceClass = item.source === "fulltext" ? "sausmond-badge-fulltext" : "sausmond-badge-metadata";

    el.innerHTML =
      '<div class="sausmond-card-thumb">' +
        '<img src="' + escapeHtml(item.thumbnail_url) + '" alt="" loading="lazy" onerror="this.parentElement.style.display=\'none\'">' +
      '</div>' +
      '<div class="sausmond-card-body">' +
        '<div class="sausmond-card-meta">' +
          '<span class="sausmond-badge ' + sourceClass + '">' + sourceLabel + '</span>' +
          '<span class="sausmond-date">' + escapeHtml(formatDate(item)) + '</span>' +
          (dept ? '<span class="sausmond-dept">' + escapeHtml(dept) + '</span>' : '') +
        '</div>' +
        '<h3 class="sausmond-card-title"><a href="' + escapeHtml(primaryLink) + '" target="_blank" rel="noopener">' + escapeHtml(title) + '</a></h3>' +
        '<p class="sausmond-card-desc">' + highlight(desc, item.matched_terms) + '</p>' +
        '<div class="sausmond-meter" title="Relevance: ' + item.relevance_score + '%">' +
          '<div class="sausmond-meter-track"><div class="sausmond-meter-fill" style="width:' + item.relevance_score + '%"></div></div>' +
          '<span class="sausmond-meter-label">' + item.relevance_score + '% relevance</span>' +
        '</div>' +
        '<div class="sausmond-card-links">' +
          '<a href="' + escapeHtml(primaryLink) + '" target="_blank" rel="noopener">' + (item.match_url ? 'View match on archive.org' : 'View on archive.org') + '</a>' +
          (item.pdf_url ? ' &middot; <a href="' + escapeHtml(item.pdf_url) + '" target="_blank" rel="noopener">PDF</a>' : '') +
          (item.source_url ? ' &middot; <a href="' + escapeHtml(item.source_url) + '" target="_blank" rel="noopener">Original source</a>' : '') +
        '</div>' +
      '</div>';
    return el;
  }

  function render(catalog, sortBy) {
    var list = document.getElementById("sausmond-list");
    var items = catalog.items.slice();

    if (sortBy === "date") {
      items.sort(function (a, b) { return (b.date || "0").localeCompare(a.date || "0"); });
    } else {
      items.sort(function (a, b) { return a.rank - b.rank; });
    }

    list.innerHTML = "";
    if (!items.length) {
      list.innerHTML = '<p class="sausmond-empty">No documents found yet. Run the catalog script to refresh, or widen the spelling variants it searches for.</p>';
      return;
    }
    items.forEach(function (item) { list.appendChild(card(item)); });
  }

  function init(catalog) {
    var meta = document.getElementById("sausmond-meta");
    if (meta) {
      meta.textContent = catalog.total_found + " document" + (catalog.total_found === 1 ? "" : "s") +
        " found (" + catalog.fulltext_hits + " full text, " + catalog.metadata_only_hits + " metadata-only)" +
        " · last refreshed " + catalog.generated_at.replace("T", " ").replace("Z", " UTC");
    }
    var queryEl = document.getElementById("sausmond-query");
    if (queryEl) queryEl.textContent = catalog.metadata_query;

    render(catalog, "relevance");

    var sortSelect = document.getElementById("sausmond-sort");
    if (sortSelect) {
      sortSelect.addEventListener("change", function () {
        render(catalog, sortSelect.value);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    fetch(CATALOG_URL)
      .then(function (r) {
        if (!r.ok) throw new Error("catalog fetch failed: " + r.status);
        return r.json();
      })
      .then(init)
      .catch(function (err) {
        var list = document.getElementById("sausmond-list");
        if (list) {
          list.innerHTML = '<p class="sausmond-empty">Couldn\'t load the catalog (' + escapeHtml(err.message) + '). Try running <code>python tools/sausmond_catalog.py</code> to regenerate it.</p>';
        }
      });
  });
})();
