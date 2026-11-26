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

  function liftHero(overlap) {
    var overlays = document.querySelectorAll('.home-hero__overlay');
    var lift = MOBILE ? MOBILE.matches : false;
    var pad = lift && overlap > 0 ? overlap + 12 + 'px' : '';
    for (var i = 0; i < overlays.length; i += 1) {
      overlays[i].style.paddingBottom = pad;
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
    var bottom = hero.getBoundingClientRect().bottom;
    var overlap = Math.max(0, Math.ceil(bottom - (window.innerHeight - h)));
    liftHero(overlap);
  }

  var existing = readCookie(COOKIE);
  if (existing === 'all' || existing === 'necessary') {
    hide();
    return;
  }

  document.documentElement.classList.add('has-cookie-banner');
  syncHeight();
  window.addEventListener('resize', syncHeight);

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
