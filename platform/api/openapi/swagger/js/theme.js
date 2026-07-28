(() => {
  const STORAGE_KEY = "codestrata-platform-api-theme";

  function systemTheme() {
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark";
  }

  function resolved(preference) {
    if (preference === "light" || preference === "dark") return preference;
    return systemTheme();
  }

  function apply(preference) {
    const theme = resolved(preference);
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.style.colorScheme = theme;
    for (const button of document.querySelectorAll("[data-theme-set]")) {
      button.setAttribute(
        "aria-pressed",
        button.getAttribute("data-theme-set") === preference ? "true" : "false"
      );
    }
  }

  function currentPreference() {
    return localStorage.getItem(STORAGE_KEY) || "system";
  }

  apply(currentPreference());

  for (const button of document.querySelectorAll("[data-theme-set]")) {
    button.addEventListener("click", () => {
      const next = button.getAttribute("data-theme-set") || "system";
      localStorage.setItem(STORAGE_KEY, next);
      apply(next);
    });
  }

  window
    .matchMedia("(prefers-color-scheme: light)")
    .addEventListener("change", () => {
      if (currentPreference() === "system") apply("system");
    });
})();
