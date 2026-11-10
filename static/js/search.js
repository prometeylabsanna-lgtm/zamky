(function () {
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function apiUrl() {
    var pref = (location.pathname.match(/^\/(ua|ru)(?=\/|$)/) || [])[0] || '/ua';
    return pref + '/api/search/';
  }

  function debounce(fn, ms) {
    var t;
    return function () {
      var args = arguments;
      var ctx = this;
      clearTimeout(t);
      t = setTimeout(function () {
        fn.apply(ctx, args);
      }, ms);
    };
  }

  function typeLabel(type) {
    if (type === 'category') return 'Категорія';
    if (type === 'brand') return 'Бренд';
    return 'Товар';
  }

  function bindForm(form) {
    var input = qs('[data-search-input]', form);
    var box = qs('[data-search-suggest]', form);
    if (!input || !box || form._searchBound) return;
    form._searchBound = true;

    var active = -1;
    var items = [];
    var abortCtrl = null;

    function hide() {
      box.hidden = true;
      box.innerHTML = '';
      active = -1;
      items = [];
      input.setAttribute('aria-expanded', 'false');
    }

    function render(payload) {
      items = (payload && payload.items) || [];
      if (!items.length) {
        hide();
        return;
      }
      var html = '<ul class="hdr-search__list" role="listbox">';
      items.forEach(function (item, i) {
        html +=
          '<li role="option" class="hdr-search__item" data-idx="' +
          i +
          '">' +
          '<a class="hdr-search__link" href="' +
          item.url +
          '">' +
          '<span class="hdr-search__label">' +
          item.label +
          '</span>' +
          '<span class="hdr-search__meta">' +
          (item.meta || typeLabel(item.type)) +
          '</span>' +
          '</a></li>';
      });
      if (payload.all_url) {
        html +=
          '<li class="hdr-search__item hdr-search__item--all">' +
          '<a class="hdr-search__link" href="' +
          payload.all_url +
          '">Показати всі результати</a></li>';
      }
      html += '</ul>';
      box.innerHTML = html;
      box.hidden = false;
      input.setAttribute('aria-expanded', 'true');
      active = -1;
    }

    function setActive(next) {
      var rows = qsa('.hdr-search__item', box);
      if (!rows.length) return;
      if (active >= 0 && rows[active]) rows[active].classList.remove('is-active');
      active = next;
      if (active < 0) active = rows.length - 1;
      if (active >= rows.length) active = 0;
      rows[active].classList.add('is-active');
      var link = qs('a', rows[active]);
      if (link) link.focus({ preventScroll: true });
      input.focus();
    }

    var fetchSuggest = debounce(function () {
      var q = (input.value || '').trim();
      if (q.length < 2) {
        hide();
        return;
      }
      if (abortCtrl) abortCtrl.abort();
      abortCtrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
      var url = apiUrl() + '?q=' + encodeURIComponent(q);
      fetch(url, {
        headers: { Accept: 'application/json' },
        credentials: 'same-origin',
        signal: abortCtrl ? abortCtrl.signal : undefined,
      })
        .then(function (r) {
          return r.json();
        })
        .then(render)
        .catch(function () {
          /* ignore abort/network */
        });
    }, 220);

    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');
    input.addEventListener('input', fetchSuggest);
    input.addEventListener('focus', function () {
      if ((input.value || '').trim().length >= 2) fetchSuggest();
    });
    input.addEventListener('keydown', function (e) {
      if (box.hidden) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActive(active + 1);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActive(active - 1);
      } else if (e.key === 'Escape') {
        hide();
      } else if (e.key === 'Enter' && active >= 0) {
        var row = qsa('.hdr-search__item', box)[active];
        var link = row && qs('a', row);
        if (link) {
          e.preventDefault();
          location.href = link.getAttribute('href');
        }
      }
    });

    document.addEventListener('click', function (e) {
      if (!form.contains(e.target)) hide();
    });
  }

  function init() {
    qsa('[data-search-form]').forEach(bindForm);
  }

  init();
  document.body.addEventListener('htmx:afterSwap', init);
})();
