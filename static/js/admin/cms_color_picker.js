(function () {
  "use strict";

  function normalize(val, fallback) {
    var v = String(val || "").trim();
    if (!v) return "";
    if (v.charAt(0) !== "#") v = "#" + v;
    if (/^#[0-9a-fA-F]{3}$/.test(v)) {
      v = "#" + v[1] + v[1] + v[2] + v[2] + v[3] + v[3];
    }
    if (!/^#[0-9a-fA-F]{6}$/.test(v)) {
      return normalize(fallback, "#ffffff") || "#ffffff";
    }
    return v.toLowerCase();
  }

  function paint(root, val) {
    if (!root) return;
    var native = root.querySelector("[data-cms-color-native]");
    var hex = root.querySelector("[data-cms-color-hex]");
    var circle = root.querySelector("[data-cms-color-circle]");
    var fallback = root.getAttribute("data-default-color") || "#ffffff";
    if (!native) return;
    var n = normalize(val, fallback);
    native.value = n;
    if (hex) hex.value = n;
    if (circle) circle.style.background = n;
    try {
      native.dispatchEvent(new Event("input", { bubbles: true }));
      native.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (err) {}
  }

  function bindRoot(root) {
    if (!root || root.dataset.cmsColorBound === "1") return;
    root.dataset.cmsColorBound = "1";
    var native = root.querySelector("[data-cms-color-native]");
    var hex = root.querySelector("[data-cms-color-hex]");
    var fallback = root.getAttribute("data-default-color") || "#ffffff";
    if (!native) return;

    native.addEventListener("input", function () {
      paint(root, native.value);
    });
    if (hex) {
      hex.addEventListener("input", function () {
        var n = String(hex.value || "").trim();
        if (/^#[0-9a-fA-F]{6}$/i.test(n) || /^#[0-9a-fA-F]{3}$/i.test(n)) {
          paint(root, n);
        }
      });
      hex.addEventListener("change", function () {
        paint(root, hex.value || fallback);
      });
    }
    paint(root, native.value || fallback);
  }

  function init(scope) {
    (scope || document).querySelectorAll("[data-cms-colorpick]").forEach(bindRoot);
  }

  function resetAll(scope) {
    var root = scope || document;
    root.querySelectorAll("[data-cms-colorpick]").forEach(function (pick) {
      bindRoot(pick);
      paint(pick, pick.getAttribute("data-default-color") || "#ffffff");
    });
  }

  document.addEventListener("click", function (event) {
    var allBtn = event.target.closest("[data-cms-style-reset-all]");
    if (allBtn) {
      event.preventDefault();
      event.stopPropagation();
      var panel = allBtn.closest("[data-admin-panel='style']") || document;
      resetAll(panel);
      return;
    }
    var btn = event.target.closest("[data-cms-color-default]");
    if (!btn) return;
    event.preventDefault();
    event.stopPropagation();
    var pick = btn.closest("[data-cms-colorpick]");
    if (!pick) return;
    bindRoot(pick);
    paint(pick, pick.getAttribute("data-default-color") || "#ffffff");
  });

  function boot() {
    init(document);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  window.zamkyCmsColorPicker = { init: init, resetAll: resetAll };
})();
