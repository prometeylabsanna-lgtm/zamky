(function () {
  'use strict';

  function scrollToForm() {
    var el = document.getElementById('form');
    if (!el) return;
    var top = el.getBoundingClientRect().top + window.scrollY - 100;
    window.scrollTo({ top: top, behavior: 'smooth' });
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-to-form], [data-scroll-form]');
    if (!btn || btn.hasAttribute('data-auto-scroll-form')) return;
    e.preventDefault();
    scrollToForm();
  });

  var root = document.querySelector('[data-auto-scroll-form]');
  if (root) setTimeout(scrollToForm, 30);
  if (location.hash === '#form' || location.hash === '#contacts') {
    setTimeout(scrollToForm, 30);
  }

  document.body.addEventListener('htmx:beforeRequest', function (e) {
    var form = e.target.closest && e.target.closest('.info-form');
    if (!form) return;
    var btn = form.querySelector('[data-send-label]');
    if (btn) {
      btn.dataset.prev = btn.textContent;
      btn.textContent = 'Надсилаємо…';
    }
  });

  document.body.addEventListener('htmx:afterRequest', function (e) {
    var form = e.target.closest && e.target.closest('.info-form');
    if (!form) return;
    var btn = form.querySelector('[data-send-label]');
    if (btn && btn.dataset.prev) btn.textContent = btn.dataset.prev;
  });
})();
