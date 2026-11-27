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
    var ctas = qsa('[data-hero-cta]', root);
    if (!slides.length) return;
    var index = 0;
    var timer;

    function loadSlideImg(slide) {
      if (!slide) return;
      var img = slide.querySelector('img');
      if (!img) return;
      var srcset = img.getAttribute('data-srcset');
      var src = img.getAttribute('data-src');
      if (srcset && !img.getAttribute('srcset')) {
        img.setAttribute('srcset', srcset);
      }
      if (src && !img.getAttribute('src')) {
        img.setAttribute('src', src);
      }
    }

    function go(i) {
      index = (i + slides.length) % slides.length;
      loadSlideImg(slides[index]);
      loadSlideImg(slides[(index + 1) % slides.length]);
      slides.forEach(function (s, si) {
        s.classList.toggle('is-active', si === index);
      });
      dots.forEach(function (d, di) {
        d.classList.toggle('is-active', di === index);
      });
      ctas.forEach(function (c, ci) {
        c.hidden = ci !== index;
      });
    }

    function next() {
      go(index + 1);
    }

    function start() {
      clearInterval(timer);
      timer = setInterval(next, 3000);
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
    window.addEventListener('load', function () {
      loadSlideImg(slides[1]);
    }, { once: true });
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

    function i18n(name, fallback) {
      var value = root.getAttribute('data-i18n-' + name);
      return value ? value : fallback;
    }

    function node(tag, className, text) {
      var el = document.createElement(tag);
      if (className) el.className = className;
      if (text != null) el.textContent = text;
      return el;
    }
    var apiUrl = root.getAttribute('data-picker-api');
    var options = readJson('picker-options') || {};
    var firstDoor = qs('[data-door-id]', root);
    var filterKeys = qsa('[data-filter]', root)
      .map(function (el) {
        return el.getAttribute('data-filter');
      })
      .filter(Boolean);
    var state = {
      door: firstDoor ? firstDoor.getAttribute('data-door-id') : '0',
    };
    filterKeys.forEach(function (key) {
      state[key] = '';
    });
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
      anyBtn.textContent = i18n('any', 'Будь-який');
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
      if (a === 1 && b !== 11) return i18n('model1', 'модель');
      if (a >= 2 && a <= 4 && (b < 12 || b > 14)) return i18n('model2', 'моделі');
      return i18n('model5', 'моделей');
    }

    function renderResults(data) {
      if (!resultsEl) return;
      resultsEl.hidden = false;
      resultsEl.replaceChildren();
      var count = data.count || 0;
      var items = data.items || [];
      var fallback = !!data.fallback;
      var subParts = [i18n('fordoor', 'Для дверей') + ': ' + doorLabel()];
      filterKeys.forEach(function (key) {
        if (state[key]) subParts.push(findLabel(key, state[key]));
      });
      if (fallback) {
        subParts.unshift(i18n('fallback', 'Точних збігів немає — популярні моделі'));
      }
      var titleText = fallback
        ? i18n('recommend', 'Рекомендуємо популярні')
        : count > 0
          ? i18n('picked', 'Підібрали') + ' ' + count + ' ' + pluralModels(count)
          : i18n('none', 'Нічого не знайдено');

      var head = node('div', 'home-picker__results-head');
      var titles = node('div');
      titles.appendChild(node('div', 'home-picker__results-title', titleText));
      titles.appendChild(node('div', 'home-picker__results-sub', subParts.join(' · ')));
      var actions = node('div', 'home-picker__results-actions');
      var resetBtn = node('button', 'home-btn-soft', i18n('reset', 'Скинути'));
      resetBtn.type = 'button';
      resetBtn.setAttribute('data-picker-reset', '');
      var catalogLink = node('a', 'home-btn-outline', i18n('catalog', 'Перейти в каталог'));
      catalogLink.href = catalogHref();
      actions.appendChild(resetBtn);
      actions.appendChild(catalogLink);
      head.appendChild(titles);
      head.appendChild(actions);
      resultsEl.appendChild(head);

      if (!count) {
        var empty = node('div', 'home-picker__empty');
        empty.appendChild(node('p', 'home-picker__empty-title', i18n('empty-title', 'За цими параметрами замків немає')));
        empty.appendChild(node('p', 'home-picker__empty-text', i18n('empty-text', 'Змініть параметри або завантажте фото нижче, і ми підберемо аналог')));
        var resetAll = node('button', 'home-btn-solid', i18n('reset-all', 'Скинути параметри'));
        resetAll.type = 'button';
        resetAll.setAttribute('data-picker-reset', '');
        empty.appendChild(resetAll);
        resultsEl.appendChild(empty);
      } else {
        var cards = node('div', 'home-picker__cards');
        items.slice(0, 4).forEach(function (item, i) {
          cards.appendChild(renderCard(item, !fallback && i === 0));
        });
        resultsEl.appendChild(cards);
      }

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
      if (item.in_stock) tags.push(item.stock_label || i18n('stock', 'В наявності'));
      var cartUrl = item.add_url || '/cart/add/' + item.id + '/';
      var pref = (location.pathname.match(/^\/(ua|ru)(?=\/|$)/) || [])[0] || '';
      if (pref && cartUrl.indexOf(pref) !== 0) cartUrl = pref + cartUrl;

      var card = node('article', 'home-pk-card' + (best ? ' is-best' : ''));
      if (best) card.appendChild(node('span', 'home-pk-card__badge', i18n('best', 'Найкращий збіг')));
      var imgLink = node('a', 'home-pk-card__img');
      imgLink.href = item.url || '#';
      var img = document.createElement('img');
      img.src = item.image || '';
      img.alt = '';
      imgLink.appendChild(img);
      card.appendChild(imgLink);
      var tagBox = node('div', 'home-pk-card__tags');
      tags.forEach(function (tg) {
        tagBox.appendChild(node('span', 'home-pk-card__tag', tg));
      });
      card.appendChild(tagBox);
      var nameLink = node('a', 'home-pk-card__name', item.name || '');
      nameLink.href = item.url || '#';
      card.appendChild(nameLink);
      var foot = node('div', 'home-pk-card__foot');
      var prices = node('div');
      prices.appendChild(node('div', 'home-pk-card__old', item.old_price || ''));
      prices.appendChild(node('div', 'home-pk-card__price', item.price || ''));
      foot.appendChild(prices);
      if (item.in_stock) {
        var cart = document.createElement('button');
        cart.type = 'button';
        cart.className = 'home-pk-card__cart';
        cart.setAttribute('data-pk-add', '');
        cart.setAttribute('data-cart-url', cartUrl);
        cart.setAttribute('aria-label', t('До кошика'));
        cart.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M8.5 4.5 6 8M15.5 4.5 18 8" stroke="#fff" stroke-width="1.8" stroke-linecap="round"></path><path d="M2.5 8.6h19" stroke="#fff" stroke-width="1.8" stroke-linecap="round"></path><path d="M4 10h16l-1.6 7.2A3.5 3.5 0 0 1 15 20H9a3.5 3.5 0 0 1-3.4-2.8z" fill="#fff"></path></svg>';
        foot.appendChild(cart);
      }
      card.appendChild(foot);
      return card;
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
      if (!label) return '';
      var parts = label.innerHTML.split(/<br\s*\/?>/i).map(function (chunk) {
        var el = document.createElement('span');
        el.innerHTML = chunk;
        return (el.textContent || '').replace(/\s+/g, ' ').trim();
      }).filter(Boolean);
      return parts.join(' ').toLowerCase();
    }

    function catalogHref() {
      var path = '/catalog/';
      var pref = (location.pathname.match(/^\/(ua|ru)(?=\/|$)/) || [])[0] || '';
      return pref + path;
    }

    function resetPicker() {
      filterKeys.forEach(function (key) {
        state[key] = '';
      });
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
        filterKeys.forEach(function (key) {
          if (state[key]) params.set(key, state[key]);
        });
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
