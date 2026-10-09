(function () {
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function initFilterGroups(root) {
    qsa('[data-filter-group]', root).forEach(function (group) {
      var btn = qs('[data-filter-toggle]', group);
      if (!btn || btn._bound) return;
      btn._bound = true;
      btn.addEventListener('click', function () {
        group.classList.toggle('is-open');
      });
    });
  }

  function clamp(n, lo, hi) {
    return Math.max(lo, Math.min(hi, n));
  }

  function initPriceSlider(root) {
    var wrap = qs('[data-price-range]', root);
    if (!wrap || wrap._bound) return;
    wrap._bound = true;
    var catalog = root.closest('[data-catalog]') || qs('[data-catalog]');
    if (!catalog) return;
    var min = +catalog.getAttribute('data-price-min') || 0;
    var max = +catalog.getAttribute('data-price-max') || 0;
    if (max <= min) max = min + 10;
    var track = qs('[data-price-track]', wrap);
    var fill = qs('[data-price-fill]', wrap);
    var loIn = qs('[data-price-lo]', wrap);
    var hiIn = qs('[data-price-hi]', wrap);
    var lo = +loIn.value || min;
    var hi = +hiIn.value || max;

    function pct(v) {
      return ((v - min) / (max - min)) * 100;
    }

    function render() {
      var lp = pct(lo);
      var hp = pct(hi);
      fill.style.left = lp + '%';
      fill.style.right = 100 - hp + '%';
      var thumbs = qsa('[data-thumb]', track);
      thumbs.forEach(function (t) {
        t.style.left = (t.getAttribute('data-thumb') === 'lo' ? lp : hp) + '%';
      });
      loIn.value = String(lo);
      hiIn.value = String(hi);
    }

    function valFromX(x) {
      var r = track.getBoundingClientRect();
      var t = clamp((x - r.left) / r.width, 0, 1);
      return Math.round((min + t * (max - min)) / 10) * 10;
    }

    function dragTo(which, v) {
      if (which === 'lo') lo = Math.min(v, hi);
      else hi = Math.max(v, lo);
      render();
    }

    var mv = null;
    var up = null;
    function stopDrag() {
      if (mv) {
        window.removeEventListener('pointermove', mv);
        window.removeEventListener('pointerup', up);
        mv = null;
      }
    }

    track.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      var v = valFromX(e.clientX);
      var thumb = e.target.getAttribute && e.target.getAttribute('data-thumb');
      var which = thumb || (Math.abs(v - lo) <= Math.abs(v - hi) ? 'lo' : 'hi');
      dragTo(which, v);
      stopDrag();
      mv = function (ev) {
        dragTo(which, valFromX(ev.clientX));
      };
      up = function () {
        stopDrag();
      };
      window.addEventListener('pointermove', mv);
      window.addEventListener('pointerup', up);
    });

    function commitInputs() {
      var a = parseInt(String(loIn.value).replace(/[^\d]/g, ''), 10);
      var b = parseInt(String(hiIn.value).replace(/[^\d]/g, ''), 10);
      lo = isNaN(a) ? min : clamp(a, min, max);
      hi = isNaN(b) ? max : clamp(b, min, max);
      if (lo > hi) {
        var t = lo;
        lo = hi;
        hi = t;
      }
      render();
    }

    loIn.addEventListener('input', function () {
      loIn.value = String(loIn.value).replace(/[^\d]/g, '');
    });
    hiIn.addEventListener('input', function () {
      hiIn.value = String(hiIn.value).replace(/[^\d]/g, '');
    });
    loIn.addEventListener('blur', commitInputs);
    hiIn.addEventListener('blur', commitInputs);
    render();
  }

  function closeFilters() {
    var filters = qs('#filters');
    var overlay = qs('#filters-overlay');
    if (filters) filters.classList.remove('is-open');
    if (overlay) overlay.classList.remove('is-open');
    document.body.style.overflowY = '';
  }

  function syncSortPrefix() {
    qsa('[data-sort-prefix]').forEach(function (el) {
      el.textContent = window.innerWidth < 720 ? '' : (window.t ? window.t('Сортування:') : 'Сортування:');
    });
  }

  function initCatalog(root) {
    root = root || document;
    var catalog = qs('[data-catalog]', root) || (root.matches && root.matches('[data-catalog]') ? root : null);
    if (!catalog && root === document) catalog = qs('[data-catalog]');
    if (!catalog) return;
    syncSortPrefix();
    initFilterGroups(catalog);
    initPriceSlider(catalog);

    var form = qs('[data-filters-form]', catalog);
    if (form && !form._closeBound) {
      form._closeBound = true;
      form.addEventListener('submit', function () {
        closeFilters();
      });
    }
  }

  initCatalog(document);
  window.addEventListener('resize', syncSortPrefix);
  document.body.addEventListener('htmx:afterSwap', function (e) {
    initCatalog(document);
    if (e.detail && e.detail.target && e.detail.target.id === 'catalog-grid') {
      closeFilters();
    }
  });
})();
