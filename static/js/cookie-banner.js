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
    }
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

  // Десктоп: відступ як у макеті, а піднімаємо лише якщо cookie-банер
  // (fixed, внизу вікна) перекрив би кнопку: підняти рівно настільки,
  // щоб низ контенту банера був над cookie-банером. Рахуємо для scrollY=0.
  function liftHeroDesktop(hero, h) {
    var overlays = clearHero();
    var heroBottom = hero.getBoundingClientRect().bottom + (window.pageYOffset || 0);
    var bannerTop = window.innerHeight - h;
    var need = Math.ceil(heroBottom - bannerTop + DESKTOP_GAP);
    if (need <= 0) return;
    for (var i = 0; i < overlays.length; i += 1) {
      var natural = parseFloat(window.getComputedStyle(overlays[i]).paddingBottom) || 0;
      if (need > natural) overlays[i].style.paddingBottom = need + 'px';
    }
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
