(function () {
  "use strict";

  function rowOf(field) {
    return field.closest(".form-row, .field-color_code, [class*='field-color_code']");
  }

  function parseIds(raw) {
    if (!raw) return {};
    var out = {};
    String(raw)
      .split(",")
      .forEach(function (part) {
        var id = part.trim();
        if (id) out[id] = true;
      });
    return out;
  }

  function bind() {
    var field = document.getElementById("id_color_code");
    var category = document.getElementById("id_category");
    if (!field || !category) return;
    var allowed = parseIds(field.getAttribute("data-cylinder-ids"));
    var row = rowOf(field);
    if (!row) return;

    function paint() {
      var current = String(category.value || "").trim();
      var show = allowed[current] === true;
      row.classList.toggle("is-core-hidden", !show);
    }

    category.addEventListener("change", paint);
    paint();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
