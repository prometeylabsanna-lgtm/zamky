/**
 * Заголовки груп фільтрів на вкладці характеристик товару.
 */
(function () {
  "use strict";

  function init() {
    var last = "";
    document.querySelectorAll("[data-filter-group]").forEach(function (select) {
      var group = select.getAttribute("data-filter-group") || "";
      var row =
        select.closest(".form-row") ||
        select.closest("[class*='field-spec_attr_']") ||
        select.parentElement;
      if (!row) return;
      if (group && group !== last) {
        var title = document.createElement("p");
        title.className = "product-filter-heading";
        title.textContent = group;
        row.parentNode.insertBefore(title, row);
        last = group;
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
