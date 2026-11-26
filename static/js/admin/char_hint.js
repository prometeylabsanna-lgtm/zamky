/* Лічильник символів біля полів з data-char-max. Не блокує збереження. */
(function () {
  'use strict';

  function suffixLen() {
    var s = document.getElementById('id_title_suffix');
    var v = s ? s.value.trim() : '';
    return v ? v.length + 3 : 0;
  }

  function bind(input) {
    if (input.getAttribute('data-char-bound')) return;
    var max = parseInt(input.getAttribute('data-char-max') || '0', 10);
    var min = parseInt(input.getAttribute('data-char-min') || '0', 10);
    if (!max && !min) return;
    input.setAttribute('data-char-bound', '1');
    var withSuffix = input.getAttribute('data-char-suffix') === '1';
    var out = document.createElement('p');
    out.className = 'admin-char-hint text-xs mt-1 text-font-subtle-light dark:text-font-subtle-dark';
    input.insertAdjacentElement('afterend', out);

    function update() {
      var n = (input.value || '').length + (withSuffix ? suffixLen() : 0);
      var over = max && n > max;
      var under = min && n > 0 && n < min;
      var rec = min ? 'рекомендовано ' + min + '–' + max : 'рекомендовано до ' + max;
      out.textContent = n + ' симв. · ' + rec + (withSuffix ? ' (з назвою бренду)' : '');
      out.style.color = over || under ? '#b45309' : '';
    }

    input.addEventListener('input', update);
    if (withSuffix) {
      var sfx = document.getElementById('id_title_suffix');
      if (sfx) sfx.addEventListener('input', update);
    }
    update();
  }

  function init() {
    document.querySelectorAll('[data-char-max], [data-char-min]').forEach(bind);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
