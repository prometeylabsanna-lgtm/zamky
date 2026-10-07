(function () {
  'use strict';

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  var drawer = qs('#cart-drawer');
  function openDrawer() {
    if (!drawer) return;
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }
  document.addEventListener('click', function (e) {
    var openBtn = e.target.closest('[data-open-cart]');
    if (openBtn) {
      e.preventDefault();
      openDrawer();
      if (window.htmx) {
        var pref = (location.pathname.match(/^\/(uk|ru)(?=\/|$)/) || [])[0] || '/uk';
        htmx.ajax('GET', pref + '/cart/drawer/', {
          target: '#cart-drawer-body',
          swap: 'innerHTML',
        });
      }
      return;
    }
    if (e.target.closest('[data-close-cart]')) closeDrawer();
  });

  document.body.addEventListener('htmx:afterSwap', function (e) {
    if (e.detail && e.detail.target && e.detail.target.id === 'cart-drawer-body') {
      openDrawer();
    }
    var toast = qs('#cart-toast');
    if (toast && toast.textContent.trim()) {
      toast.classList.add('is-visible');
      clearTimeout(toast._t);
      toast._t = setTimeout(function () {
        toast.classList.remove('is-visible');
        toast.textContent = '';
      }, 2200);
    }
    qsa('.product-card__cart.is-added').forEach(function (btn) {
      btn.classList.add('is-pop');
      setTimeout(function () {
        btn.classList.remove('is-pop');
      }, 180);
      setTimeout(function () {
        btn.classList.remove('is-added');
      }, 1400);
    });
  });

  qsa('[data-slider]').forEach(function (section) {
    var track = qs('[data-slider-track]', section);
    if (!track) return;
    var prev = qs('[data-slider-prev]', section);
    var next = qs('[data-slider-next]', section);
    var step = function () {
      return Math.min(track.clientWidth * 0.85, 322);
    };
    if (prev) {
      prev.addEventListener('click', function () {
        track.scrollBy({ left: -step(), behavior: 'smooth' });
      });
    }
    if (next) {
      next.addEventListener('click', function () {
        track.scrollBy({ left: step(), behavior: 'smooth' });
      });
    }
  });

  var gallery = qs('[data-gallery]');
  if (gallery && !qs('[data-pdp]')) {
    var track = qs('[data-gallery-track]', gallery);
    var slides = qsa('.gallery__slide', gallery);
    var thumbs = qsa('[data-thumb]', document);
    var index = 0;
    function go(i) {
      if (!slides.length) return;
      index = (i + slides.length) % slides.length;
      track.style.transform = 'translateX(' + -index * 100 + '%)';
      thumbs.forEach(function (t, ti) {
        t.classList.toggle('is-active', ti === index);
      });
      var counter = qs('[data-gallery-counter]');
      if (counter) counter.textContent = index + 1 + ' / ' + slides.length;
    }
    var prev = qs('[data-gallery-prev]');
    var next = qs('[data-gallery-next]');
    if (prev) prev.addEventListener('click', function () { go(index - 1); });
    if (next) next.addEventListener('click', function () { go(index + 1); });
    thumbs.forEach(function (t, ti) {
      t.addEventListener('click', function () { go(ti); });
    });
    var startX = 0;
    gallery.addEventListener('touchstart', function (e) {
      startX = e.changedTouches[0].clientX;
    }, { passive: true });
    gallery.addEventListener('touchend', function (e) {
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 40) go(index + (dx < 0 ? 1 : -1));
    }, { passive: true });
    go(0);
  }

  var filters = qs('#filters');
  var overlay = qs('#filters-overlay');
  qsa('[data-open-filters]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (!filters) return;
      filters.classList.add('is-open');
      if (overlay) overlay.classList.add('is-open');
      document.body.style.overflow = 'hidden';
    });
  });
  qsa('[data-close-filters]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (!filters) return;
      filters.classList.remove('is-open');
      if (overlay) overlay.classList.remove('is-open');
      document.body.style.overflow = '';
    });
  });

  qsa('[data-choice-group]').forEach(function (group) {
    qsa('[data-choice]', group).forEach(function (btn) {
      btn.addEventListener('click', function () {
        qsa('[data-choice]', group).forEach(function (b) {
          b.classList.remove('is-active');
        });
        btn.classList.add('is-active');
        var input = qs('input[type="radio"], input[type="hidden"]', btn) ||
          qs('input[name="' + btn.getAttribute('data-name') + '"]', group);
        var value = btn.getAttribute('data-value');
        var name = btn.getAttribute('data-name');
        if (name) {
          var hidden = qs('input[name="' + name + '"]', group.closest('form') || document);
          if (hidden) hidden.value = value;
        }
        if (input && input.type === 'radio') {
          input.checked = true;
        }
      });
    });
  });

  window.Zamky = { openDrawer: openDrawer, closeDrawer: closeDrawer };
})();
