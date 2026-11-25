(() => {
  const formEl = document.querySelector(".site-content-editor form");
  if (!formEl) return;

  const emptyHtml = (emptyTpl) => {
    if (emptyTpl instanceof HTMLTemplateElement) {
      const holder = document.createElement("div");
      holder.appendChild(emptyTpl.content.cloneNode(true));
      return holder.innerHTML;
    }
    return emptyTpl.innerHTML;
  };

  const bindRoot = (root) => {
    const prefix = root.getAttribute("data-cms-nav");
    if (!prefix) return;
    const emptyTpl = root.querySelector("[data-cms-nav-empty]");
    const totalInput =
      root.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`) ||
      formEl.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
    if (!emptyTpl || !totalInput) return;

    root.querySelectorAll("[data-cms-nav-add]").forEach((addBtn) => {
      addBtn.addEventListener("click", () => {
        const group = addBtn.getAttribute("data-cms-nav-group") || "";
        const list =
          (group && root.querySelector(`[data-cms-nav-list="${group}"]`)) ||
          root.querySelector("[data-cms-nav-list]");
        if (!list) return;
        const next = Number(totalInput.value || "0");
        const html = emptyHtml(emptyTpl).replace(/__prefix__/g, String(next));
        const wrap = document.createElement("div");
        wrap.innerHTML = html.trim();
        const row = wrap.firstElementChild;
        if (!row) return;
        if (group) {
          const groupInput = row.querySelector(
            'input[name$="-group"], input[name$="-tab"]'
          );
          if (groupInput) groupInput.value = group;
        }
        const order = row.querySelector('input[name$="-sort_order"]');
        if (order) {
          order.value = String(list.querySelectorAll("[data-cms-nav-row]").length);
        }
        const active = row.querySelector('input[name$="-is_active"]');
        if (active) active.checked = true;
        list.appendChild(row);
        totalInput.value = String(next + 1);
        row.dispatchEvent(new CustomEvent("formset:added", { bubbles: true }));
      });
    });
  };

  document.querySelectorAll("[data-cms-nav]").forEach(bindRoot);
})();
