/**
 * Loads wiki sidebar from data/site-nav.json (two-step nav: Wiki + Related).
 * Requires #wiki-sidebar-root in the document.
 */
(function () {
  const NAV_URL = 'data/site-nav.json';

  function currentPage() {
    const path = window.location.pathname || '';
    const seg = path.split('/').filter(Boolean);
    return seg.length ? seg[seg.length - 1] : 'index.html';
  }

  function relativePrefix() {
    const path = window.location.pathname || '';
    const seg = path.split('/').filter(Boolean);

    // If the site is hosted with /docs/ in the URL (e.g. /docs/brainstorming.html),
    // treat "docs" as the site root for link resolution. If not present, assume the
    // directory containing index.html is the web root (e.g. /brainstorming.html).
    const docsIdx = seg.lastIndexOf('docs');

    // Depth from "site root folder" (docs folder if present) to the current file.
    // Example: /docs/brainstorming/page.html → seg length=3, docsIdx=0 → depth=1 → "../"
    const depth = docsIdx >= 0 ? Math.max(0, seg.length - docsIdx - 2) : Math.max(0, seg.length - 1);
    return '../'.repeat(depth);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function isExternalHref(href) {
    const h = String(href || '').trim();
    return (
      h.startsWith('http://') ||
      h.startsWith('https://') ||
      h.startsWith('mailto:') ||
      h.startsWith('tel:') ||
      h.startsWith('#') ||
      h.startsWith('/')
    );
  }

  function resolveHref(prefix, href) {
    if (!href) return '';
    if (!prefix || isExternalHref(href)) return href;
    return prefix + href;
  }

  function renderLink(prefix, href, label, active) {
    const cls = active ? 'nav-link active' : 'nav-link';
    const resolved = resolveHref(prefix, href);
    return `<a href="${escapeHtml(resolved)}" class="${cls}">${escapeHtml(label)}</a>`;
  }

  async function load() {
    const root = document.getElementById('wiki-sidebar-root');
    if (!root) return;

    let data;
    try {
      const prefix = relativePrefix();
      const res = await fetch(prefix + NAV_URL, { cache: 'no-store' });
      if (!res.ok) throw new Error(res.statusText);
      data = await res.json();
    } catch (e) {
      root.innerHTML =
        '<div class="sidebar sidebar--error" role="navigation"><p class="sidebar-error">Could not load navigation. Open this site via a local server (not file://) so data files can load.</p></div>';
      console.error(e);
      return;
    }

    const page = currentPage();
    const prefix = relativePrefix();
    const primary = data.primary || [];
    const relatedMap = data.relatedByPage || {};
    const related = relatedMap[page] || relatedMap['index.html'] || [];

    const brand = escapeHtml(data.brand || 'Wiki');

    let primaryHtml = '';
    for (const item of primary) {
      const active = item.href === page;
      primaryHtml += renderLink(prefix, item.href, item.label, active);
    }

    let relatedHtml = '';
    for (const item of related) {
      const active = item.href === page;
      relatedHtml += renderLink(prefix, item.href, item.label, active);
    }

    root.innerHTML = `
<nav class="sidebar" aria-label="Site navigation">
  <div class="sidebar-header">
    <div class="sidebar-title">${brand}</div>
    <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Toggle theme" title="Dark / light mode"></button>
  </div>
  <div class="sidebar-body">
    <div class="nav-section nav-section--wiki">
      <div class="nav-section-label">Wiki</div>
      <div class="nav-section-links">${primaryHtml}</div>
    </div>
    <div class="nav-section nav-section--related">
      <div class="nav-section-label">Related</div>
      <div class="nav-section-links">${relatedHtml}</div>
    </div>
  </div>
</nav>`;

    if (typeof window.wikiBindThemeToggle === 'function') {
      window.wikiBindThemeToggle();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();
