(function () {
  'use strict';

  var COOKIE = 'zamky_consent';
  var banner = document.getElementById('cookie-banner');
  if (!banner) return;

  function readCookie(name) {
    var parts = ('; ' + document.cookie).split('; ' + name + '=');
    if (parts.length < 2) return '';
    return decodeURIComponent(parts.pop().split(';').shift() || '');
  }

  function setCookie(value) {
    var maxAge = 60 * 60 * 24 * 365;
    var secure = location.protocol === 'https:' ? '; Secure' : '';
    document.cookie =
      COOKIE + '=' + encodeURIComponent(value) + '; Max-Age=' + maxAge + '; Path=/; SameSite=Lax' + secure;
  }

  function hide() {
    banner.hidden = true;
    document.documentElement.classList.remove('has-cookie-banner');
    document.documentElement.style.removeProperty('--cookie-banner-h');
    liftHero(0);
  }

  var MOBILE = window.matchMedia ? window.matchMedia('(max-width: 743px)') : null;
  // Мінімальний зазор між кнопкою банера та cookie-банером (десктоп).
  var DESKTOP_GAP = 2;

  function clearHero() {
    var overlays = document.querySelectorAll('.home-hero__overlay');
    for (var i = 0; i < overlays.length; i += 1) {
      overlays[i].style.paddingBottom = '';
      var act = overlays[i].querySelector('.home-hero__actions');
      if (act) act.style.marginTop = '';
    }
    var hero = document.querySelector('.home-hero');
    if (hero) hero.style.removeProperty('--hero-arrow-lift');
    return overlays;
  }

  function liftHero(overlap) {
    var overlays = clearHero();
    if (!(overlap > 0)) return;
    var pad = overlap + 12 + 'px';
    for (var i = 0; i < overlays.length; i += 1) {
      overlays[i].style.paddingBottom = pad;
    }
  }

  function px(v) {
    return parseFloat(v) || 0;
  }

  // Десктоп: відступи як у макеті; піднімаємо лише якщо cookie-банер
  // (fixed, внизу вікна) перекрив би кнопку активного слайда — рівно
  // настільки, щоб кнопка була над банером. Щоб заголовок не наїхав на
  // стрілки слайдера: (1) стискаємо проміжок заголовок→кнопка до 24u,
  // (2) решту компенсуємо, піднімаючи стрілки над заголовком (лише поки
  // є cookie-банер). Рахуємо для scrollY=0.
  function liftHeroDesktop(hero, h) {
    clearHero();
    var overlay = hero.querySelector('.home-hero__slide.is-active .home-hero__overlay');
    if (!overlay || overlay.hidden) return;
    var heroRect = hero.getBoundingClientRect();
    var heroBottom = heroRect.bottom + (window.pageYOffset || 0);
    var natPad = px(window.getComputedStyle(overlay).paddingBottom);
    var need = Math.ceil(heroBottom - (window.innerHeight - h) + DESKTOP_GAP - natPad);
    if (need <= 0) return;

    var actions = overlay.querySelector('.home-hero__actions');
    var natMargin = actions ? px(window.getComputedStyle(actions).marginTop) : 0;
    var minMargin = (24 * heroRect.width) / 1360;
    var maxCut = Math.max(0, natMargin - minMargin);
    var cut = Math.min(need, maxCut);
    var titleLift = need - cut;

    var title = overlay.querySelector('.home-hero__title');
    var arrow = hero.querySelector('.home-hero__arrow');
    var shift = 0;
    if (title && arrow && arrow.offsetParent !== null) {
      var tr = title.getBoundingClientRect();
      var ar = arrow.getBoundingClientRect();
      if (tr.left < ar.right && tr.right > ar.left) {
        shift = Math.max(0, ar.bottom - (tr.top - titleLift - 8));
        var badges = overlay.querySelector('.home-hero__badges');
        var minTop = badges ? badges.getBoundingClientRect().bottom + 8 : heroRect.top;
        var maxShift = Math.max(0, ar.top - minTop);
        if (shift > maxShift) {
          // Не вміщається: зменшуємо підйом, щоб заголовок не наїхав на стрілку.
          var excess = shift - maxShift;
          shift = maxShift;
          titleLift -= excess;
          need -= excess;
          cut = Math.min(cut, need);
        }
      }
    }
    if (need <= 0) return;
    overlay.style.paddingBottom = natPad + need + 'px';
    if (actions && cut > 0) actions.style.marginTop = natMargin - cut + 'px';
    if (shift > 0) hero.style.setProperty('--hero-arrow-lift', shift + 'px');
  }

  function syncHeight() {
    if (banner.hidden) return;
    var h = banner.offsetHeight;
    document.documentElement.style.setProperty('--cookie-banner-h', h + 'px');
    var hero = document.querySelector('.home-hero');
    if (!hero) {
      liftHero(0);
      return;
    }
    if (MOBILE && MOBILE.matches) {
      var bottom = hero.getBoundingClientRect().bottom;
      liftHero(Math.max(0, Math.ceil(bottom - (window.innerHeight - h))));
    } else {
      liftHeroDesktop(hero, h);
    }
  }

  var existing = readCookie(COOKIE);
  if (existing === 'all' || existing === 'necessary') {
    hide();
    return;
  }

  document.documentElement.classList.add('has-cookie-banner');
  syncHeight();
  window.addEventListener('resize', syncHeight);
  // Шапка/шрифти можуть змінити позицію банера після першого розрахунку.
  window.addEventListener('load', syncHeight);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(syncHeight);
  if (window.ResizeObserver) {
    new ResizeObserver(syncHeight).observe(document.documentElement);
  }
  // Зміна активного слайда (home.js): інша висота заголовка.
  var track = document.querySelector('.home-hero__track');
  if (track && window.MutationObserver) {
    new MutationObserver(syncHeight).observe(track, {
      attributes: true,
      attributeFilter: ['class', 'hidden'],
      subtree: true,
    });
  }

  banner.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-cookie-consent]');
    if (!btn) return;
    var value = btn.getAttribute('data-cookie-consent');
    if (value !== 'all' && value !== 'necessary') return;
    setCookie(value);
    if (value === 'all' && typeof window.gtag === 'function') {
      window.gtag('consent', 'update', {
        ad_storage: 'granted',
        analytics_storage: 'granted',
        ad_user_data: 'granted',
        ad_personalization: 'granted',
      });
    }
    hide();
    if (value === 'all') {
      window.location.reload();
    }
  });
})();
