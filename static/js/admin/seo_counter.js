/* Лічильник символів біля SEO-полів (лише підказка, не блокує збереження). */
(function () {
  'use strict';
  var RULES = {
    id_title_default: { max: 60, suffix: true },
    id_title_default_ru: { max: 60, suffix: true },
    id_description_default: { min: 70, max: 160 },
    id_description_default_ru: { min: 70, max: 160 },
    id_og_image_alt: { max: 125 }
  };
  function suffixLen() {
    var s = document.getElementById('id_title_suffix');
    var v = s ? s.value.trim() : '';
    return v ? v.length + 3 : 0;
  }
  function init() {
    Object.keys(RULES).forEach(function (id) {
      var input = document.getElementById(id);
      if (!input) return;
      var rule = RULES[id];
      var out = document.createElement('div');
      out.className = 'text-xs mt-1';
      input.insertAdjacentElement('afterend', out);
      function update() {
        var n = input.value.length + (rule.suffix ? suffixLen() : 0);
        var bad = (rule.max && n > rule.max) || (rule.min && n > 0 && n < rule.min);
        out.textContent = n + ' симв.' + (rule.suffix ? ' (з суфіксом)' : '') +
          (rule.min ? ' · рекомендовано ' + rule.min + '–' + rule.max : ' · рекомендовано ≤ ' + rule.max);
        out.style.color = bad ? '#b45309' : '';
      }
      input.addEventListener('input', update);
      var sfx = document.getElementById('id_title_suffix');
      if (rule.suffix && sfx) sfx.addEventListener('input', update);
      update();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
