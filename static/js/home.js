(function () {
  'use strict';

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function t(s) {
    return window.t ? window.t(s) : s;
  }

  function getCsrf() {
    var inp = qs('input[name=csrfmiddlewaretoken]');
    return inp ? inp.value : '';
  }

  function readJson(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  /* Hero carousel */
  (function initHero() {
    var root = qs('[data-hero]');
    if (!root) return;
    var slides = qsa('[data-hero-slide]', root);
    var dots = qsa('[data-hero-dot]', root);
    if (!slides.length) return;
    var index = 0;
    var timer;

    function go(i) {
      index = (i + slides.length) % slides.length;
      slides.forEach(function (s, si) {
        s.classList.toggle('is-active', si === index);
      });
      dots.forEach(function (d, di) {
        d.classList.toggle('is-active', di === index);
      });
    }

    function next() {
      go(index + 1);
    }

    function start() {
      clearInterval(timer);
      timer = setInterval(next, 6000);
    }

    function stop() {
      clearInterval(timer);
    }

    var prev = qs('[data-hero-prev]', root);
    var nextBtn = qs('[data-hero-next]', root);
    if (prev) {
      prev.addEventListener('click', function () {
        go(index - 1);
        start();
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', function () {
        next();
        start();
      });
    }
    dots.forEach(function (d, di) {
      d.addEventListener('click', function () {
        go(di);
        start();
      });
    });
    root.addEventListener('mouseenter', stop);
    root.addEventListener('mouseleave', start);
    go(0);
    start();
  })();

  /* Popular tabs + slider */
  (function initPopular() {
    var section = qs('[data-home-popular]');
    if (!section) return;
    var tabs = qsa('[data-pop-tab]', section);
    var panels = qsa('[data-pop-panel]', section);

    function activePanel() {
      return panels.find(function (p) {
        return !p.hidden;
      });
    }

    function activeTrack() {
      var p = activePanel();
      return p ? qs('[data-pop-track]', p) : null;
    }

    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var key = tab.getAttribute('data-pop-tab');
        tabs.forEach(function (tb) {
          var on = tb === tab;
          tb.classList.toggle('is-active', on);
          tb.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        panels.forEach(function (p) {
          var show = p.getAttribute('data-pop-panel') === key;
          p.hidden = !show;
          p.classList.toggle('is-active', show);
        });
      });
    });

    var prev = qs('[data-pop-prev]', section);
    var next = qs('[data-pop-next]', section);
    var step = function () {
      var track = activeTrack();
      if (!track) return 200;
      var item = qs('.home-popular__item', track);
      var w = item ? item.offsetWidth : 200;
      return w + 12;
    };
    if (prev) {
      prev.addEventListener('click', function () {
        var track = activeTrack();
        if (track) track.scrollBy({ left: -step(), behavior: 'smooth' });
      });
    }
    if (next) {
      next.addEventListener('click', function () {
        var track = activeTrack();
        if (track) track.scrollBy({ left: step(), behavior: 'smooth' });
      });
    }
  })();

  /* Picker */
  (function initPicker() {
    var root = qs('[data-picker]');
    if (!root) return;
    var apiUrl = root.getAttribute('data-picker-api');
    var options = readJson('picker-options') || {};
    var state = { door: '0', mech: '', brand: '', color: '', price: '' };
    var resultsEl = qs('#picker-results', root);
    var backdrop = null;

    qsa('[data-door-id]', root).forEach(function (btn) {
      btn.addEventListener('click', function () {
        state.door = btn.getAttribute('data-door-id');
        qsa('[data-door-id]', root).forEach(function (b) {
          var on = b === btn;
          b.classList.toggle('is-active', on);
          b.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
      });
    });

    function closeFilters() {
      qsa('.home-filter.is-open', root).forEach(function (f) {
        f.classList.remove('is-open');
        var toggle = qs('.home-filter__toggle', f);
        var menu = qs('.home-filter__menu', f);
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
        if (menu) menu.hidden = true;
      });
      if (backdrop) {
        backdrop.remove();
        backdrop = null;
      }
    }

    function openFilter(filterEl) {
      closeFilters();
      filterEl.classList.add('is-open');
      var toggle = qs('.home-filter__toggle', filterEl);
      var menu = qs('.home-filter__menu', filterEl);
      if (toggle) toggle.setAttribute('aria-expanded', 'true');
      if (menu) menu.hidden = false;
      backdrop = document.createElement('div');
      backdrop.className = 'home-picker__backdrop';
      backdrop.addEventListener('click', closeFilters);
      document.body.appendChild(backdrop);
    }

    function setFilter(key, slug, label) {
      state[key] = slug || '';
      var filterEl = qs('[data-filter="' + key + '"]', root);
      if (!filterEl) return;
      filterEl.classList.toggle('is-set', !!slug);
      var valEl = qs('[data-filter-val]', filterEl);
      if (valEl) valEl.textContent = slug ? label : t('Не обрано');
      closeFilters();
    }

    function buildMenu(filterEl, key) {
      var menu = qs('.home-filter__menu', filterEl);
      if (!menu || menu.dataset.ready) return;
      menu.dataset.ready = '1';
      var list = options[key] || [];
      var anyBtn = document.createElement('button');
      anyBtn.type = 'button';
      anyBtn.className = 'home-filter__opt' + (!state[key] ? ' is-active' : '');
      anyBtn.textContent = t('Будь-який');
      anyBtn.addEventListener('click', function () {
        setFilter(key, '', '');
      });
      menu.appendChild(anyBtn);
      list.forEach(function (opt) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className =
          'home-filter__opt' + (state[key] === opt.slug ? ' is-active' : '');
        btn.textContent = opt.label;
        btn.addEventListener('click', function () {
          setFilter(key, opt.slug, opt.label);
        });
        menu.appendChild(btn);
      });
    }

    qsa('.home-filter', root).forEach(function (filterEl) {
      buildMenu(filterEl, filterEl.getAttribute('data-filter'));
      var toggle = qs('.home-filter__toggle', filterEl);
      if (toggle) {
        toggle.addEventListener('click', function () {
          if (filterEl.classList.contains('is-open')) closeFilters();
          else openFilter(filterEl);
        });
      }
    });

    function pluralModels(n) {
      var a = n % 10;
      var b = n % 100;
      if (a === 1 && b !== 11) return t('модель');
      if (a >= 2 && a <= 4 && (b < 12 || b > 14)) return t('моделі');
      return t('моделей');
    }

    function renderResults(data) {
      if (!resultsEl) return;
      resultsEl.hidden = false;
      var count = data.count || 0;
      var items = data.items || [];
      var subParts = [t('Для дверей') + ': ' + doorLabel()];
      if (state.mech) subParts.push(findLabel('mech', state.mech));
      if (state.brand) subParts.push(state.brand);
      if (state.price) subParts.push(state.price);
      if (state.color) subParts.push(findLabel('color', state.color));

      var html = '<div class="home-picker__results-head">';
      html += '<div><div class="home-picker__results-title">';
      html +=
        count > 0
          ? t('Підібрали') + ' ' + count + ' ' + pluralModels(count)
          : t('Нічого не знайдено');
      html += '</div><div class="home-picker__results-sub">' + subParts.join(' · ') + '</div></div>';
      html += '<div class="home-picker__results-actions">';
      html +=
        '<button type="button" class="home-btn-soft" data-picker-reset>' +
        t('Скинути') +
        '</button>';
      html +=
        '<a class="home-btn-outline" href="' +
        catalogHref() +
        '">' +
        t('Перейти в каталог') +
        '</a></div></div>';

      if (!count) {
        html += '<div class="home-picker__empty"><p class="home-picker__empty-title">' + t('За цими параметрами замків немає') + '</p>';
        html += '<p class="home-picker__empty-text">' + t('Змініть параметри або завантажте фото нижче, і ми підберемо аналог') + '</p>';
        html += '<button type="button" class="home-btn-solid" data-picker-reset>' + t('Скинути параметри') + '</button></div>';
      } else {
        html += '<div class="home-picker__cards">';
        items.slice(0, 4).forEach(function (item, i) {
          html += renderCard(item, i === 0);
        });
        html += '</div>';
      }
      resultsEl.innerHTML = html;

      qsa('[data-picker-reset]', resultsEl).forEach(function (btn) {
        btn.addEventListener('click', resetPicker);
      });
      qsa('[data-pk-add]', resultsEl).forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          if (window.htmx) {
            htmx.ajax('POST', btn.getAttribute('data-cart-url'), { swap: 'none' });
            btn.classList.add('is-added');
          }
        });
      });
    }

    function renderCard(item, best) {
      var tags = [];
      if (item.brand) tags.push(item.brand);
      if (item.in_stock) tags.push(item.stock_label || t('В наявності'));
      var tagHtml = tags
        .map(function (tg) {
          return '<span class="home-pk-card__tag">' + tg + '</span>';
        })
        .join('');
      var cartUrl = item.add_url || '/cart/add/' + item.id + '/';
      var pref = (location.pathname.match(/^\/(ua|ru)(?=\/|$)/) || [])[0] || '';
      if (pref && cartUrl.indexOf(pref) !== 0) cartUrl = pref + cartUrl;

      return (
        '<article class="home-pk-card' +
        (best ? ' is-best' : '') +
        '">' +
        (best ? '<span class="home-pk-card__badge">' + t('Найкращий збіг') + '</span>' : '') +
        '<a class="home-pk-card__img" href="' +
        item.url +
        '"><img src="' +
        item.image +
        '" alt=""></a>' +
        '<div class="home-pk-card__tags">' +
        tagHtml +
        '</div>' +
        '<a class="home-pk-card__name" href="' +
        item.url +
        '">' +
        item.name +
        '</a>' +
        '<div class="home-pk-card__foot"><div><div class="home-pk-card__old">' +
        (item.old_price || '') +
        '</div><div class="home-pk-card__price">' +
        item.price +
        '</div></div>' +
        (item.in_stock
          ? '<button type="button" class="home-pk-card__cart" data-pk-add data-cart-url="' +
            cartUrl +
            '" aria-label="' +
            t('До кошика') +
            '"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M8.5 4.5 6 8M15.5 4.5 18 8" stroke="#fff" stroke-width="1.8" stroke-linecap="round"></path><path d="M2.5 8.6h19" stroke="#fff" stroke-width="1.8" stroke-linecap="round"></path><path d="M4 10h16l-1.6 7.2A3.5 3.5 0 0 1 15 20H9a3.5 3.5 0 0 1-3.4-2.8z" fill="#fff"></path></svg></button>'
          : '') +
        '</div></article>'
      );
    }

    function findLabel(key, slug) {
      var list = options[key] || [];
      var hit = list.find(function (o) {
        return o.slug === slug;
      });
      return hit ? hit.label : slug;
    }

    function doorLabel() {
      var btn = qs('[data-door-id="' + state.door + '"]', root);
      if (!btn) return '';
      var label = qs('.home-door-btn__label', btn);
      return label ? label.textContent.replace(/\s+/g, ' ').trim().toLowerCase() : '';
    }

    function catalogHref() {
      var path = '/catalog/';
      var pref = (location.pathname.match(/^\/(ua|ru)(?=\/|$)/) || [])[0] || '';
      return pref + path;
    }

    function resetPicker() {
      state.mech = state.brand = state.color = state.price = '';
      qsa('.home-filter', root).forEach(function (f) {
        f.classList.remove('is-set');
        var valEl = qs('[data-filter-val]', f);
        if (valEl) valEl.textContent = t('Не обрано');
      });
      if (resultsEl) {
        resultsEl.hidden = true;
        resultsEl.innerHTML = '';
      }
    }

    var showBtn = qs('[data-picker-show]', root);
    if (showBtn) {
      showBtn.addEventListener('click', function () {
        closeFilters();
        var params = new URLSearchParams();
        params.set('door', state.door);
        if (state.mech) params.set('mech', state.mech);
        if (state.brand) params.set('brand', state.brand);
        if (state.color) params.set('color', state.color);
        if (state.price) params.set('price', state.price);
        fetch(apiUrl + '?' + params.toString(), {
          headers: { Accept: 'application/json' },
          credentials: 'same-origin',
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            if (data && data.ok) renderResults(data);
          })
          .catch(function () {});
      });
    }
  })();
})();
