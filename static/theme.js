(function () {
  const STORAGE_KEY = "ipclem-theme";

  function systemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function savedTheme() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      if (value === "light" || value === "dark") return value;
    } catch (_) {
      /* ignore */
    }
    return null;
  }

  function currentTheme() {
    return savedTheme() || systemTheme();
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    const btn = document.getElementById("themeToggle");
    if (!btn) return;
    const isLight = theme === "light";
    btn.setAttribute("aria-checked", isLight ? "true" : "false");
    btn.setAttribute(
      "aria-label",
      isLight ? "Light mode on. Switch to dark mode." : "Dark mode on. Switch to light mode."
    );
    btn.title = isLight ? "Light mode" : "Dark mode";
  }

  function setTheme(theme, persist) {
    applyTheme(theme);
    if (!persist) return;
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (_) {
      /* ignore */
    }
  }

  applyTheme(currentTheme());

  window.addEventListener("DOMContentLoaded", () => {
    applyTheme(currentTheme());

    const btn = document.getElementById("themeToggle");
    if (btn) {
      btn.addEventListener("click", () => {
        const next = currentTheme() === "dark" ? "light" : "dark";
        setTheme(next, true);
      });
    }

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onSystemChange = () => {
      if (savedTheme() === null) applyTheme(systemTheme());
    };
    if (media.addEventListener) media.addEventListener("change", onSystemChange);
    else if (media.addListener) media.addListener(onSystemChange);
  });
})();
