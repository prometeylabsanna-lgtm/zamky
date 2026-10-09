(function () {
  'use strict';

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }
  function csrf() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  var menuData = [];
  var dataEl = qs('#header-menu-data');
  if (dataEl) {
    try {
      menuData = JSON.parse(dataEl.textContent);
    } catch (e) {
      menuData = [];
    }
  }

  function closeDropdowns(except) {
    qsa('.dropdown.is-open').forEach(function (el) {
      if (el !== except) {
        el.classList.remove('is-open');
        var btn = qs('[data-dropdown-toggle]', el);
        if (btn) btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  document.addEventListener('click', function (e) {
    var toggle = e.target.closest('[data-dropdown-toggle]');
    if (toggle) {
      e.preventDefault();
      var wrap = toggle.closest('.dropdown');
      if (!wrap) return;
      var open = wrap.classList.contains('is-open');
      closeDropdowns();
      if (!open) {
        wrap.classList.add('is-open');
        var btn = qs('[data-dropdown-toggle]', wrap);
        if (btn) btn.setAttribute('aria-expanded', 'true');
      }
      return;
    }
    if (!e.target.closest('.dropdown')) closeDropdowns();
  });

  var mega = qs('#mega-menu');
  var megaBtn = qs('[data-open-mega]');
  var colSubs = qs('.mega__col--subs');
  var colLeaves = qs('.mega__col--leaves');
  var megaState = { cat: null, sub: null };

  function lockIcon(kind, size) {
    size = size || 44;
    if (kind === 'cyl') {
      return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M8.4 9.6A4 4 0 1 1 15.6 9.6L14.6 19a1.6 1.6 0 0 1-1.6 1.5h-2A1.6 1.6 0 0 1 9.4 19z"></path><circle cx="12" cy="8" r="1.3"></circle><path d="M12 9.3v2.7"></path></svg>';
    }
    if (kind === 'pad') {
      return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"></path><rect x="4.75" y="10.5" width="14.5" height="10.5" rx="3.5"></rect><circle cx="12" cy="14.8" r="1.6"></circle><path d="M12 16.4v2"></path></svg>';
    }
    if (kind === 'shield') {
      return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 3l7 2.8v5.4c0 4.4-3 7.9-7 9.3-4-1.4-7-4.9-7-9.3V5.8L12 3z"></path><rect x="9" y="11" width="6" height="4.8" rx="1"></rect><path d="M10.4 11V9.7a1.6 1.6 0 0 1 3.2 0V11"></path></svg>';
    }
    return '';
  }

  function catMark(cat, size) {
    if (!cat) return '';
    if (cat.lock) return lockIcon(cat.lock, size);
    if (cat.logo) {
      var src = '/static/' + cat.logo;
      var w = size > 40 ? 54 : 48;
      var h = size > 40 ? 44 : 40;
      return '<img src="' + src + '" alt="" width="' + w + '" height="' + h + '">';
    }
    return '';
  }

  function rowHtml(name, idx, attr) {
    return '<li><button type="button" class="mega__row" ' + attr + '="' + idx + '"><span class="mega__name">' +
      name + '</span><svg class="mega__arrow" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3.5L10.5 8 6 12.5"></path></svg></button></li>';
  }

  function catalogUrl() {
    var pref = (location.pathname.match(/^\/(ua|ru)(?=\/|$)/) || [])[0] || '/ua';
    return pref + '/catalog/';
  }

  function renderMega() {
    if (!mega) return;
    var cat = megaState.cat != null ? menuData[megaState.cat] : null;
    mega.classList.toggle('is-l2', !!cat);
    mega.classList.toggle('is-l3', !!(cat && megaState.sub != null));
    qsa('[data-mega-cat]', mega).forEach(function (btn) {
      btn.classList.toggle('is-active', Number(btn.getAttribute('data-mega-cat')) === megaState.cat);
    });
    if (colSubs) {
      if (cat) {
        colSubs.hidden = false;
        var name = cat.name;
        qsa('[data-mega-cat-name],[data-mega-cat-title]', colSubs).forEach(function (n) {
          n.textContent = name;
        });
        var ico = qs('[data-mega-title-ico]', colSubs);
        if (ico) ico.innerHTML = catMark(cat, 44);
        var list = qs('[data-mega-subs]', colSubs);
        if (list) {
          list.innerHTML = cat.subs.map(function (s, i) {
            return rowHtml(s.name, i, 'data-mega-sub');
          }).join('');
          qsa('[data-mega-sub]', list).forEach(function (btn) {
            btn.classList.toggle('is-active', Number(btn.getAttribute('data-mega-sub')) === megaState.sub);
          });
        }
      } else {
        colSubs.hidden = true;
      }
    }
    if (colLeaves) {
      if (cat && megaState.sub != null) {
        colLeaves.hidden = false;
        var sub = cat.subs[megaState.sub];
        qsa('[data-mega-sub-name],[data-mega-sub-title]', colLeaves).forEach(function (n) {
          n.textContent = sub.name;
        });
        var ico2 = qs('[data-mega-leaf-ico]', colLeaves);
        if (ico2) ico2.innerHTML = catMark(cat, 44);
        var leaves = qs('[data-mega-leaves]', colLeaves);
        if (leaves) {
          leaves.innerHTML = sub.leaves.map(function (n, i) {
            return rowHtml(n, i, 'data-mega-leaf');
          }).join('');
        }
        var find = qs('[data-mega-find]', colLeaves);
        if (find) find.setAttribute('href', catalogUrl() + '#' + encodeURIComponent(sub.name));
      } else {
        colLeaves.hidden = true;
      }
    }
  }

  function openMega() {
    if (!mega) return;
    mega.hidden = false;
    megaState = { cat: null, sub: null };
    renderMega();
    if (megaBtn) megaBtn.classList.add('is-active');
    document.body.style.overflowY = 'hidden';
  }

  function closeMega() {
    if (!mega) return;
    mega.hidden = true;
    megaState = { cat: null, sub: null };
    if (megaBtn) megaBtn.classList.remove('is-active');
    if (!qs('.mnav.is-open') && !qs('.cart-drawer.is-open')) {
      document.body.style.overflowY = '';
    }
  }

  if (megaBtn) {
    megaBtn.addEventListener('click', function () {
      if (mega && !mega.hidden) closeMega();
      else openMega();
    });
  }
  qsa('[data-close-mega]').forEach(function (btn) {
    btn.addEventListener('click', closeMega);
  });
  if (mega) {
    mega.addEventListener('click', function (e) {
      var catBtn = e.target.closest('[data-mega-cat]');
      if (catBtn) {
        megaState.cat = Number(catBtn.getAttribute('data-mega-cat'));
        megaState.sub = null;
        renderMega();
        return;
      }
      var subBtn = e.target.closest('[data-mega-sub]');
      if (subBtn) {
        megaState.sub = Number(subBtn.getAttribute('data-mega-sub'));
        renderMega();
      }
    });
  }

  var mnav = qs('#mobile-menu');
  var mnavState = { cat: null, sub: null };

  function showMnavLevel(n) {
    qsa('[data-mnav-level]', mnav).forEach(function (el) {
      var on = Number(el.getAttribute('data-mnav-level')) === n;
      el.hidden = !on;
      el.classList.toggle('is-active', on);
    });
  }

  function renderMnav() {
    if (!mnav) return;
    var cat = mnavState.cat != null ? menuData[mnavState.cat] : null;
    if (!cat) {
      showMnavLevel(0);
      return;
    }
    if (mnavState.sub == null) {
      showMnavLevel(1);
      var title = qs('[data-mnav-title]', mnav);
      if (title) title.textContent = cat.name;
      var ico = qs('[data-mnav-ico]', mnav);
      if (ico) ico.innerHTML = catMark(cat, 40);
      var list = qs('[data-mnav-subs]', mnav);
      if (list) {
        list.innerHTML = cat.subs.map(function (s, i) {
          return '<li><button type="button" class="mnav__row" data-mnav-sub="' + i + '"><span class="mega__name">' +
            s.name + '</span><svg class="mega__arrow" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 3.5L10.5 8 6 12.5"></path></svg></button></li>';
        }).join('');
      }
      return;
    }
    showMnavLevel(2);
    var sub = cat.subs[mnavState.sub];
    var backName = qs('[data-mnav-back-name]', mnav);
    if (backName) backName.textContent = cat.name;
    var subTitle = qs('[data-mnav-sub-title]', mnav);
    if (subTitle) subTitle.textContent = sub.name;
    var ico2 = qs('[data-mnav-leaf-ico]', mnav);
    if (ico2) ico2.innerHTML = catMark(cat, 40);
    var leaves = qs('[data-mnav-leaves]', mnav);
    if (leaves) {
      leaves.innerHTML = sub.leaves.map(function (n, i) {
        return '<li><button type="button" class="mnav__row" data-mnav-leaf="' + i + '"><span class="mega__name">' +
          n + '</span><svg class="mega__arrow" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 3.5L10.5 8 6 12.5"></path></svg></button></li>';
      }).join('');
    }
    var find = qs('[data-mnav-find]', mnav);
    if (find) find.setAttribute('href', catalogUrl() + '#' + encodeURIComponent(sub.name));
  }

  function openMnav() {
    if (!mnav) return;
    mnav.classList.add('is-open');
    mnav.setAttribute('aria-hidden', 'false');
    mnavState = { cat: null, sub: null };
    renderMnav();
    document.body.style.overflowY = 'hidden';
  }

  function closeMnav() {
    if (!mnav) return;
    mnav.classList.remove('is-open');
    mnav.setAttribute('aria-hidden', 'true');
    mnavState = { cat: null, sub: null };
    renderMnav();
    if (!qs('.cart-drawer.is-open')) document.body.style.overflowY = '';
    window.scrollTo(0, window.scrollY || 0);
  }

  qsa('[data-open-menu]').forEach(function (btn) {
    btn.addEventListener('click', openMnav);
  });
  qsa('[data-close-menu]').forEach(function (btn) {
    btn.addEventListener('click', closeMnav);
  });
  if (mnav) {
    mnav.addEventListener('click', function (e) {
      var catBtn = e.target.closest('[data-mnav-cat]');
      if (catBtn) {
        mnavState.cat = Number(catBtn.getAttribute('data-mnav-cat'));
        mnavState.sub = null;
        renderMnav();
        return;
      }
      var subBtn = e.target.closest('[data-mnav-sub]');
      if (subBtn) {
        mnavState.sub = Number(subBtn.getAttribute('data-mnav-sub'));
        renderMnav();
        return;
      }
      var back = e.target.closest('[data-mnav-back]');
      if (back) {
        var to = Number(back.getAttribute('data-mnav-back'));
        if (to === 0) mnavState = { cat: null, sub: null };
        else mnavState.sub = null;
        renderMnav();
      }
    });
  }

  function setLang(code) {
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/lang/';
    form.style.display = 'none';
    function field(name, value) {
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = name;
      input.value = value;
      form.appendChild(input);
    }
    field('csrfmiddlewaretoken', csrf());
    field('lang', code);
    field('next', window.location.pathname + window.location.search + window.location.hash);
    document.body.appendChild(form);
    form.submit();
  }

  document.addEventListener('click', function (e) {
    var langBtn = e.target.closest('[data-set-lang]');
    if (!langBtn) return;
    e.preventDefault();
    setLang(langBtn.getAttribute('data-set-lang'));
  });

  window.addEventListener('scroll', function () {
    var head = qs('.site-header');
    if (head) head.classList.toggle('is-scrolled', window.scrollY > 4);
  }, { passive: true });

  window.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    closeDropdowns();
    closeMega();
    closeMnav();
  });

  window.addEventListener('resize', function () {
    if (window.innerWidth >= 1100) closeMnav();
    else closeMega();
  });

  window.ZamkyHeader = { openMega: openMega, closeMega: closeMega, openMnav: openMnav, closeMnav: closeMnav };
})();
