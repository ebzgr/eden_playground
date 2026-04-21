/**
 * Populates brainstorming topics from data/brainstorming-topics.json and enables column sorting.
 * Default sort: importance (high → low), then open before closed, then title A–Z.
 */
(function () {
  const DATA_URL = 'data/brainstorming-topics.json';

  const IMPORTANCE_RANK = { critical: 4, high: 3, medium: 2, low: 1 };
  const STATUS_RANK = { open: 1, closed: 0 };

  function rankImportance(s) {
    return IMPORTANCE_RANK[String(s || '').toLowerCase()] ?? 0;
  }

  function rankStatus(s) {
    return STATUS_RANK[String(s || '').toLowerCase()] ?? 0;
  }

  function defaultSort(a, b) {
    const ri = rankImportance(b.importance) - rankImportance(a.importance);
    if (ri !== 0) return ri;
    const rs = rankStatus(b.status) - rankStatus(a.status);
    if (rs !== 0) return rs;
    return String(a.title).localeCompare(String(b.title), undefined, { sensitivity: 'base' });
  }

  function sortRows(rows, key, dir) {
    const mult = dir === 'asc' ? 1 : -1;
    return [...rows].sort((a, b) => {
      let cmp = 0;
      if (key === 'topic') {
        cmp = a.title.localeCompare(b.title, undefined, { sensitivity: 'base' });
      } else if (key === 'importance') {
        cmp = rankImportance(a.importance) - rankImportance(b.importance);
      } else if (key === 'status') {
        cmp = rankStatus(a.status) - rankStatus(b.status);
      }
      if (cmp !== 0) return cmp * mult;
      return defaultSort(a, b);
    });
  }

  function badgeClass(imp) {
    const i = String(imp || '').toLowerCase();
    return 'bb-badge bb-importance-' + (['low', 'medium', 'high', 'critical'].includes(i) ? i : 'medium');
  }

  function statusClass(st) {
    return st === 'closed' ? 'bb-badge bb-status-closed' : 'bb-badge bb-status-open';
  }

  function statusLabel(st) {
    return st === 'closed' ? 'Closed' : 'Open';
  }

  function importanceLabel(imp) {
    const i = String(imp || '').toLowerCase();
    return i.charAt(0).toUpperCase() + i.slice(1);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderCards(root, rows) {
    root.innerHTML = '';

    if (!rows.length) {
      root.innerHTML = '<div style="grid-column: 1 / -1; color: rgba(27,31,42,0.7);">No topics yet.</div>';
      return;
    }

    for (const row of rows) {
      const card = document.createElement('article');
      card.className = 'bb-card';
      card.innerHTML = `
        <div class="bb-card-top">
          <h3 class="bb-card-title"><a href="${escapeHtml(row.href)}">${escapeHtml(row.title)}</a></h3>
          <div class="bb-card-badges">
            <span class="${badgeClass(row.importance)}">${escapeHtml(importanceLabel(row.importance))}</span>
            <span class="${statusClass(row.status)}">${escapeHtml(statusLabel(row.status))}</span>
          </div>
        </div>
      `;
      root.appendChild(card);
    }
  }

  function setAriaSort(buttons, activeKey, dir) {
    buttons.forEach((btn) => {
      const k = btn.getAttribute('data-sort');
      if (k === activeKey) {
        btn.setAttribute('aria-sort', dir === 'asc' ? 'ascending' : 'descending');
      } else {
        btn.removeAttribute('aria-sort');
      }
    });
  }

  async function init() {
    const cardsRoot = document.getElementById('bb-topics-cards');
    if (!cardsRoot) return;

    cardsRoot.innerHTML = '<div style="grid-column: 1 / -1;">Loading topics…</div>';

    let payload;
    try {
      const res = await fetch(DATA_URL, { cache: 'no-store' });
      if (!res.ok) throw new Error(res.statusText);
      payload = await res.json();
    } catch (e) {
      cardsRoot.innerHTML =
        '<div style="grid-column: 1 / -1;">Could not load topics. If you opened this via <code>file://</code>, use a local server instead. Also verify <code>docs/data/brainstorming-topics.json</code> exists.</div>';
      console.error(e);
      return;
    }

    let rows = (payload.topics || []).slice();
    rows.sort(defaultSort);

    let sortKey = 'importance';
    let sortDir = 'desc';

    const buttons = document.querySelectorAll('.bb-sort');

    function apply() {
      const sorted = sortRows(rows, sortKey, sortDir);
      renderCards(cardsRoot, sorted);
      setAriaSort(buttons, sortKey, sortDir);
    }

    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.getAttribute('data-sort');
        if (key === sortKey) {
          sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          sortKey = key;
          sortDir = key === 'topic' ? 'asc' : 'desc';
        }
        apply();
      });
    });

    apply();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
