(function () {
  "use strict";

  var KEY = "zamky_theme";
  var root = document.documentElement;

  function current() {
    var t = root.getAttribute("data-theme");
    return t === "dark" ? "dark" : "light";
  }

  function apply(theme) {
    var next = theme === "dark" ? "dark" : "light";
    root.setAttribute("data-theme", next);
    try {
      window.localStorage.setItem(KEY, next);
    } catch (e) {}
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      var dark = next === "dark";
      btn.setAttribute("aria-pressed", dark ? "true" : "false");
      btn.setAttribute(
        "aria-label",
        dark
          ? (window.t && window.t("Світла тема")) || "Світла тема"
          : (window.t && window.t("Темна тема")) || "Темна тема"
      );
    });
  }

  function toggle() {
    apply(current() === "dark" ? "light" : "dark");
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    e.preventDefault();
    toggle();
  });

  apply(current());
})();
