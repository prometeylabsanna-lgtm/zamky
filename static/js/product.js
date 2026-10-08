(function () {
  'use strict';

  var root = document.querySelector('[data-pdp]');
  if (!root) return;

  var variantsEl = document.getElementById('pdp-variants');
  var variants = [];
  try {
    variants = variantsEl ? JSON.parse(variantsEl.textContent || '[]') : [];
  } catch (e) {
    variants = [];
  }

  var state = {
    color: root.getAttribute('data-color') || '',
    size: parseInt(root.getAttribute('data-size') || '0', 10) || 0,
    qty: 1,
    slide: 0,
    guide: false,
    acc: null,
    added: false,
    copied: false,
  };

  var STATUS = {
    in: { bg: 'var(--color-success-bg)', color: 'var(--color-success)' },
    low: { bg: 'var(--color-warning-bg)', color: 'var(--color-warning)' },
    out: { bg: 'var(--color-out-bg)', color: 'var(--color-out)' },
  };

  function qs(sel, el) {
    return (el || root).querySelector(sel);
  }
  function qsa(sel, el) {
    return Array.from((el || root).querySelectorAll(sel));
  }

  function fmt(n) {
    return Math.round(n).toLocaleString('uk-UA').replace(/\u00a0/g, ' ') + ' ₴';
  }

  function current() {
    return (
      variants.find(function (v) {
        return v.color === state.color && v.size === state.size;
      }) ||
      variants.find(function (v) {
        return String(v.id) === String(root.getAttribute('data-product-id'));
      }) ||
      variants[0]
    );
  }

  function stockFor(color, size) {
    var v = variants.find(function (x) {
      return x.color === color && x.size === size;
    });
    return v ? v.stock : 0;
  }

  function setBadge(el, status, text) {
    if (!el) return;
    el.classList.remove('badge--in', 'badge--low', 'badge--out');
    el.classList.add('badge--' + status);
    var t = el.querySelector('[data-stock-badge-text]');
    if (t) t.textContent = text;
  }

  function renderGallery(v) {
    var track = qs('[data-gallery-track]');
    var thumbs = qs('[data-thumbs]');
    if (!track || !thumbs || !v) return;
    var imgs = v.images || [];
    track.innerHTML = imgs
      .map(function (img, i) {
        return (
          '<div class="pdp-gallery__slide' +
          (i === 0 ? ' is-active' : '') +
          '"><img src="' +
          img.src +
          '" alt="' +
          (img.alt || '').replace(/"/g, '&quot;') +
          '"></div>'
        );
      })
      .join('');
    thumbs.innerHTML = imgs
      .map(function (img, i) {
        return (
          '<button type="button" class="pdp-thumbs__btn' +
          (i === state.slide ? ' is-active' : '') +
          '" data-thumb aria-label="' +
          (window.t ? window.t('Фото') : 'Фото') +
          ' ' +
          (i + 1) +
          '"><img src="' +
          img.src +
          '" alt=""></button>'
        );
      })
      .join('');
    qsa('[data-thumb]', thumbs).forEach(function (btn, i) {
      btn.addEventListener('click', function () {
        goSlide(i);
      });
    });
    goSlide(Math.min(state.slide, Math.max(0, imgs.length - 1)));
  }

  function goSlide(i) {
    var track = qs('[data-gallery-track]');
    var slides = qsa('.pdp-gallery__slide', track);
    if (!slides.length) return;
    state.slide = (i + slides.length) % slides.length;
    // Без transform: інакше stacking context ламає mix-blend-mode → білий прямокутник.
    track.style.transform = '';
    slides.forEach(function (slide, si) {
      slide.classList.toggle('is-active', si === state.slide);
    });
    qsa('[data-thumb]').forEach(function (t, ti) {
      t.classList.toggle('is-active', ti === state.slide);
    });
    var counter = qs('[data-gallery-counter]');
    if (counter) counter.textContent = state.slide + 1 + ' / ' + slides.length;
  }

  function bindGalleryGestures() {
    var gallery = qs('[data-gallery]');
    if (!gallery || gallery._bound) return;
    gallery._bound = true;
    var startX = 0;
    gallery.addEventListener(
      'touchstart',
      function (e) {
        startX = e.changedTouches[0].clientX;
      },
      { passive: true }
    );
    gallery.addEventListener(
      'touchend',
      function (e) {
        var dx = e.changedTouches[0].clientX - startX;
        if (Math.abs(dx) > 40) goSlide(state.slide + (dx < 0 ? 1 : -1));
      },
      { passive: true }
    );
    var prev = qs('[data-gallery-prev]');
    var next = qs('[data-gallery-next]');
    if (prev) prev.addEventListener('click', function () { goSlide(state.slide - 1); });
    if (next) next.addEventListener('click', function () { goSlide(state.slide + 1); });
    document.addEventListener('keydown', function (e) {
      if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
      if (e.key === 'ArrowLeft') goSlide(state.slide - 1);
      if (e.key === 'ArrowRight') goSlide(state.slide + 1);
    });
  }

  function applyVariant(v, pushUrl) {
    if (!v) return;
    state.color = v.color;
    state.size = v.size;
    state.qty = 1;
    state.slide = 0;
    root.setAttribute('data-color', v.color);
    root.setAttribute('data-size', String(v.size));
    root.setAttribute('data-product-id', String(v.id));

    var title = qs('[data-product-title]');
    if (title) title.textContent = v.name;
    var crumb = qs('[data-crumb-title]');
    if (crumb) crumb.textContent = v.name;
    document.title = v.name;

    qsa('[data-stock-badge]').forEach(function (el) {
      setBadge(el, v.status, v.badge);
    });

    var skuLabel = qs('[data-sku-label]');
    var skuBtn = qs('[data-copy-sku]');
    if (skuLabel) skuLabel.textContent = (window.t ? window.t('Код товару:') : 'Код товару:') + ' ' + v.sku;
    if (skuBtn) skuBtn.setAttribute('data-sku', v.sku);

    var colorName = qs('[data-color-name]');
    if (colorName) colorName.textContent = v.color_label;
    var sizeName = qs('[data-size-name]');
    if (sizeName) sizeName.textContent = v.size_label;

    qsa('[data-color]').forEach(function (btn) {
      btn.classList.toggle('is-active', btn.getAttribute('data-color') === v.color);
    });

    qsa('[data-size]').forEach(function (btn) {
      var len = parseInt(btn.getAttribute('data-size'), 10);
      var left = stockFor(v.color, len);
      var out = left === 0;
      btn.classList.toggle('is-active', len === v.size);
      btn.classList.toggle('is-out', out);
      var sub = btn.querySelector('[data-size-sub]');
      if (sub) {
        sub.textContent = out
          ? (window.t ? window.t('немає') : 'немає')
          : len + ' ' + (window.t ? window.t('мм') : 'мм');
      }
    });

    var oldEl = qs('[data-old-price]');
    var discEl = qs('[data-discount]');
    var priceEl = qs('[data-price]');
    if (oldEl) oldEl.textContent = v.old_price ? fmt(v.old_price) : '';
    if (discEl) discEl.textContent = v.discount ? '−' + v.discount + '%' : '';
    if (priceEl) priceEl.textContent = fmt(v.price);

    var note = qs('[data-stock-note]');
    if (note) {
      note.textContent = v.stock_note;
      note.className = 'pdp-stock-note__text is-' + v.status;
    }

    var qtyEl = qs('[data-qty]');
    var qtyInput = qs('[data-qty-input]');
    if (qtyEl) qtyEl.textContent = '1';
    if (qtyInput) qtyInput.value = '1';

    var cartBtn = qs('[data-add-cart]');
    var cartLabel = qs('[data-cart-label]');
    if (cartBtn) {
      cartBtn.setAttribute('hx-post', v.add_url);
      cartBtn.classList.toggle('is-out', v.status === 'out');
      cartBtn.classList.remove('is-added');
      cartBtn.disabled = v.status === 'out';
      if (window.htmx) htmx.process(cartBtn);
    }
    if (cartLabel) {
      cartLabel.textContent =
        v.status === 'out'
          ? (window.t ? window.t('Немає в наявності') : 'Немає в наявності')
          : (window.t ? window.t('До кошика') : 'До кошика');
    }

    var wish = qs('[data-wishlist-btn]');
    if (wish) {
      wish.id = 'wishlist-btn-' + v.id;
      wish.setAttribute('hx-post', v.wishlist_url);
      if (window.htmx) htmx.process(wish);
    }

    var specSku = qs('[data-spec-sku]');
    if (specSku) specSku.textContent = v.sku;
    var specCover = qs('[data-spec-cover]');
    if (specCover) specCover.textContent = v.cover;
    var specLen = qs('[data-spec-len]');
    if (specLen) specLen.textContent = v.size + ' ' + (window.t ? window.t('мм') : 'мм');
    var specAb = qs('[data-spec-ab]');
    if (specAb) {
      specAb.textContent =
        v.size_a + '×' + v.size_b + ' ' + (window.t ? window.t('мм') : 'мм');
    }

    renderGallery(v);

    if (pushUrl && v.url && window.location.pathname !== v.url) {
      history.replaceState({ product: v.id }, '', v.url);
    }
  }

  function openQuick() {
    var v = current();
    var box = qs('[data-quick-root]');
    if (!box || !v) return;
    box.innerHTML =
      '<form class="pdp-quick__form" data-quick-form hx-post="' +
      v.quick_url +
      '" hx-target="[data-quick-root]" hx-swap="innerHTML">' +
      '<label class="pdp-quick__phone"><span>+380</span>' +
      '<input type="tel" name="phone" required placeholder="00 000 00 00" autocomplete="tel" inputmode="tel" autofocus></label>' +
      '<input type="hidden" name="quantity" value="' +
      state.qty +
      '" data-quick-qty>' +
      '<button type="submit" class="pdp-quick__submit">' +
      (window.t ? window.t('Замовити') : 'Замовити') +
      '</button></form>' +
      '<p class="pdp-quick__note">' +
      (window.t
        ? window.t('Менеджер передзвонить протягом 15 хвилин і уточнить деталі замовлення.')
        : 'Менеджер передзвонить протягом 15 хвилин і уточнить деталі замовлення.') +
      '</p>';
    if (window.htmx) htmx.process(box);
  }

  qsa('[data-color]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      state.color = btn.getAttribute('data-color');
      applyVariant(current(), true);
    });
  });

  qsa('[data-size]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      state.size = parseInt(btn.getAttribute('data-size'), 10);
      applyVariant(current(), true);
    });
  });

  var guideBtn = qs('[data-toggle-guide]');
  var guide = qs('[data-guide]');
  if (guideBtn && guide) {
    guideBtn.addEventListener('click', function () {
      state.guide = !state.guide;
      guide.hidden = !state.guide;
    });
  }

  qsa('[data-acc-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var item = btn.closest('[data-acc-item]');
      if (!item) return;
      var id = item.getAttribute('data-acc-id');
      var open = item.classList.contains('is-open');
      qsa('[data-acc-item]').forEach(function (el) {
        el.classList.remove('is-open');
        var panel = qs('[data-acc-panel]', el);
        if (panel) panel.hidden = true;
      });
      if (!open) {
        item.classList.add('is-open');
        var panel = qs('[data-acc-panel]', item);
        if (panel) panel.hidden = false;
        state.acc = id;
      } else {
        state.acc = null;
      }
    });
  });

  var dec = qs('[data-qty-dec]');
  var inc = qs('[data-qty-inc]');
  function syncQty() {
    var v = current();
    var max = v ? Math.max(1, v.stock || 1) : 1;
    if (v && v.status === 'out') state.qty = 1;
    else state.qty = Math.min(Math.max(1, state.qty), max);
    var qtyEl = qs('[data-qty]');
    var qtyInput = qs('[data-qty-input]');
    var quickQty = qs('[data-quick-qty]');
    if (qtyEl) qtyEl.textContent = String(state.qty);
    if (qtyInput) qtyInput.value = String(state.qty);
    if (quickQty) quickQty.value = String(state.qty);
  }
  if (dec) {
    dec.addEventListener('click', function () {
      state.qty -= 1;
      syncQty();
    });
  }
  if (inc) {
    inc.addEventListener('click', function () {
      state.qty += 1;
      syncQty();
    });
  }

  var skuBtn = qs('[data-copy-sku]');
  if (skuBtn) {
    skuBtn.addEventListener('click', function () {
      var sku = skuBtn.getAttribute('data-sku') || '';
      try {
        navigator.clipboard.writeText(sku);
      } catch (e) {}
      var label = qs('[data-sku-label]');
      if (label) {
        label.textContent = window.t ? window.t('Скопійовано') : 'Скопійовано';
        clearTimeout(skuBtn._t);
        skuBtn._t = setTimeout(function () {
          label.textContent =
            (window.t ? window.t('Код товару:') : 'Код товару:') + ' ' + sku;
        }, 1200);
      }
    });
  }

  var openQuickBtn = qs('[data-open-quick]');
  if (openQuickBtn) {
    openQuickBtn.addEventListener('click', openQuick);
  }

  document.body.addEventListener('htmx:afterSwap', function (e) {
    var cartBtn = qs('[data-add-cart]');
    if (cartBtn && e.detail && e.detail.successful) {
      var path = (e.detail.pathInfo && e.detail.pathInfo.requestPath) || '';
      if (path.indexOf('/cart/add/') !== -1 && !cartBtn.disabled) {
        cartBtn.classList.add('is-added');
        var label = qs('[data-cart-label]');
        if (label) {
          label.textContent = window.t ? window.t('Додано до кошика') : 'Додано до кошика';
        }
        clearTimeout(cartBtn._t);
        cartBtn._t = setTimeout(function () {
          cartBtn.classList.remove('is-added');
          if (label && !cartBtn.disabled) {
            label.textContent = window.t ? window.t('До кошика') : 'До кошика';
          }
        }, 1600);
        if (window.Zamky && window.Zamky.openDrawer) {
          window.Zamky.openDrawer();
          if (window.htmx) {
            var pref = (location.pathname.match(/^\/(ua|ru)(?=\/|$)/) || [])[0] || '/ua';
            htmx.ajax('GET', pref + '/cart/drawer/', {
              target: '#cart-drawer-body',
              swap: 'innerHTML',
            });
          }
        }
      }
    }
  });

  bindGalleryGestures();
  applyVariant(current(), false);
})();
