// Theme toggle — works with static or dynamically injected #theme-toggle (sidebar.js).
(function () {
  const STORAGE_KEY = 'wwmm-theme';

  function applySavedTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') {
      document.documentElement.setAttribute('data-theme', saved);
    }
  }

  applySavedTheme();

  function syncButton(btn) {
    const current = document.documentElement.getAttribute('data-theme');
    const isLight = current === 'light';
    btn.textContent = isLight ? '🌙' : '☀️';
    btn.setAttribute('aria-label', isLight ? 'Switch to dark mode' : 'Switch to light mode');
    btn.setAttribute('aria-pressed', isLight ? 'true' : 'false');
  }

  function bindThemeToggle() {
    const btn = document.getElementById('theme-toggle');
    if (!btn || btn.dataset.wikiBound) return;
    btn.dataset.wikiBound = '1';

    btn.addEventListener('click', function () {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem(STORAGE_KEY, next);
      syncButton(btn);
    });

    syncButton(btn);
  }

  window.wikiBindThemeToggle = bindThemeToggle;

  document.addEventListener('DOMContentLoaded', bindThemeToggle);
})();
