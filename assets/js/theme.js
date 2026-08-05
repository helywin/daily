(() => {
  const storageKey = 'daily-theme';
  const root = document.documentElement;
  const toggle = document.querySelector('.theme-toggle');
  const themeColor = document.querySelector('meta[name="theme-color"]');
  const systemTheme = matchMedia('(prefers-color-scheme: dark)');

  const getSavedTheme = () => {
    try {
      const savedTheme = localStorage.getItem(storageKey);
      return savedTheme === 'light' || savedTheme === 'dark' ? savedTheme : null;
    } catch (_) {
      return null;
    }
  };

  const updateToggle = (theme) => {
    if (!toggle) return;
    const nextThemeLabel = theme === 'dark' ? '亮色' : '暗色';
    const label = `切换到${nextThemeLabel}模式`;
    toggle.setAttribute('aria-label', label);
    toggle.setAttribute('title', label);
  };

  const applyTheme = (theme, persist = false) => {
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
    if (themeColor) themeColor.content = theme === 'dark' ? '#0b1120' : '#f4f6f8';
    updateToggle(theme);

    if (persist) {
      try { localStorage.setItem(storageKey, theme); } catch (_) {}
    }
  };

  applyTheme(root.dataset.theme === 'dark' ? 'dark' : 'light');

  toggle?.addEventListener('click', () => {
    applyTheme(root.dataset.theme === 'dark' ? 'light' : 'dark', true);
  });

  systemTheme.addEventListener?.('change', (event) => {
    if (!getSavedTheme()) applyTheme(event.matches ? 'dark' : 'light');
  });
})();
