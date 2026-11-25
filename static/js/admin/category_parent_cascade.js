(function () {
  "use strict";

  var ARROW =
    '<svg class="parent-cascade__arrow" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 3.5L10.5 8 6 12.5"></path></svg>';

  function parseTree(root) {
    var el = root.querySelector("script[type='application/json']");
    if (!el) return [];
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      return [];
    }
  }

  function findPath(nodes, pk, trail) {
    trail = trail || [];
    for (var i = 0; i < (nodes || []).length; i += 1) {
      var node = nodes[i];
      var next = trail.concat([node]);
      if (String(node.id) === String(pk)) return next;
      var deeper = findPath(node.children, pk, next);
      if (deeper) return deeper;
    }
    return null;
  }

  function makeRow(node, withArrow) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "parent-cascade__row";
    btn.setAttribute("data-id", node ? String(node.id) : "");
    var name = document.createElement("span");
    name.className = "parent-cascade__name";
    name.textContent = node ? node.name : "Без батьківської";
    btn.appendChild(name);
    if (withArrow) btn.insertAdjacentHTML("beforeend", ARROW);
    return btn;
  }

  function bind(root) {
    if (root.getAttribute("data-cascade-ready")) return;
    root.setAttribute("data-cascade-ready", "1");
    var tree = parseTree(root);
    var hidden = root.querySelector("[data-cascade-value]");
    var toggle = root.querySelector("[data-cascade-toggle]");
    var label = root.querySelector("[data-cascade-label]");
    var panel = root.querySelector("[data-cascade-panel]");
    var back = root.querySelector("[data-cascade-back]");
    var col1 = root.querySelector("[data-cascade-col='1']");
    var col2 = root.querySelector("[data-cascade-col='2']");
    var col3 = root.querySelector("[data-cascade-col='3']");
    if (!hidden || !toggle || !panel || !col1 || !col2 || !col3) return;

    var state = { l1: null, l2: null, l3: null };

    function pathNodes() {
      var out = [];
      if (state.l1) out.push(state.l1);
      if (state.l2) out.push(state.l2);
      if (state.l3) out.push(state.l3);
      return out;
    }

    function sync() {
      var nodes = pathNodes();
      var last = nodes[nodes.length - 1];
      hidden.value = last ? String(last.id) : "";
      if (label) {
        label.textContent = last
          ? nodes.map(function (n) { return n.name; }).join(" / ")
          : "—";
      }
    }

    function paintList(col, nodes, activeId, includeEmpty) {
      col.innerHTML = "";
      if (includeEmpty) {
        var empty = makeRow(null, false);
        empty.classList.toggle("is-active", !activeId && !state.l1);
        empty.addEventListener("click", function (e) {
          e.stopPropagation();
          state.l1 = null;
          state.l2 = null;
          state.l3 = null;
          paint();
          close();
        });
        col.appendChild(empty);
      }
      (nodes || []).forEach(function (node) {
        var hasKids = node.children && node.children.length;
        var row = makeRow(node, hasKids);
        row.classList.toggle("is-active", String(node.id) === String(activeId || ""));
        row.addEventListener("click", function (e) {
          e.stopPropagation();
          pick(node, col);
          if (!hasKids) close();
        });
        col.appendChild(row);
      });
    }

    function pick(node, col) {
      if (col === col1) {
        state.l1 = node;
        state.l2 = null;
        state.l3 = null;
      } else if (col === col2) {
        state.l2 = node;
        state.l3 = null;
      } else {
        state.l3 = node;
      }
      paint();
      sync();
    }

    function paint() {
      paintList(col1, tree, state.l1 && state.l1.id, true);
      var kids = state.l1 ? state.l1.children || [] : [];
      col2.hidden = !kids.length;
      if (kids.length) paintList(col2, kids, state.l2 && state.l2.id, false);
      var grand = state.l2 ? state.l2.children || [] : [];
      col3.hidden = !grand.length;
      if (grand.length) paintList(col3, grand, state.l3 && state.l3.id, false);
      panel.classList.toggle("is-l2", !col2.hidden);
      panel.classList.toggle("is-l3", !col3.hidden);
      var level = state.l3 ? 3 : state.l2 ? 2 : 1;
      if (back) back.hidden = level < 2;
    }

    function open() {
      panel.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      root.classList.add("is-open");
      paint();
    }

    function close() {
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
      root.classList.remove("is-open");
    }

    function applyValue() {
      var path = hidden.value ? findPath(tree, hidden.value) : null;
      state.l1 = path && path[0] ? path[0] : null;
      state.l2 = path && path[1] ? path[1] : null;
      state.l3 = path && path[2] ? path[2] : null;
      sync();
    }

    applyValue();
    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      if (panel.hidden) open();
      else close();
    });
    if (back) {
      back.addEventListener("click", function (e) {
        e.stopPropagation();
        if (state.l3) state.l3 = null;
        else if (state.l2) state.l2 = null;
        paint();
        sync();
      });
    }
    document.addEventListener("pointerdown", function (e) {
      if (!root.contains(e.target)) close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
  }

  function boot() {
    document.querySelectorAll("[data-parent-cascade]").forEach(bind);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
