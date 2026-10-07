(function () {
  'use strict';

  var root = document.querySelector('[data-checkout]');
  if (!root) return;

  var prices = {
    np: Number(root.getAttribute('data-price-np') || 80),
    courier: Number(root.getAttribute('data-price-courier') || 150),
    pickup: Number(root.getAttribute('data-price-pickup') || 0),
  };

  function qs(sel, el) {
    return (el || root).querySelector(sel);
  }

  function fmt(n) {
    return Math.round(n).toLocaleString('uk-UA').replace(/\u00a0/g, ' ') + ' ₴';
  }

  function parseMoney(text) {
    if (!text) return 0;
    var n = parseInt(String(text).replace(/[^\d]/g, ''), 10);
    return isNaN(n) ? 0 : n;
  }

  function currentDelivery() {
    var hidden = qs('input[name="delivery_method"]');
    return (hidden && hidden.value) || 'np';
  }

  function syncDeliveryUI() {
    var method = currentDelivery();
    var addr = qs('[data-checkout-addr]');
    var pickup = qs('[data-checkout-pickup]');
    var addrLabel = qs('[data-checkout-addr-label]');
    var addrInput = qs('[data-addr-input]');
    var btn = qs('.checkout-choice[data-name="delivery_method"][data-value="' + method + '"]');

    if (addr) {
      if (method === 'pickup') addr.classList.add('is-hidden');
      else addr.classList.remove('is-hidden');
    }
    if (pickup) {
      if (method === 'pickup') pickup.classList.add('is-visible');
      else pickup.classList.remove('is-visible');
    }
    if (btn) {
      if (addrLabel) {
        var lab = btn.getAttribute('data-addr-label') || (window.t ? window.t('Адреса') : 'Адреса');
        addrLabel.textContent = lab + '*';
      }
      if (addrInput) {
        addrInput.setAttribute('placeholder', btn.getAttribute('data-addr-ph') || '');
      }
    }

    var ship = prices[method] != null ? prices[method] : prices.np;
    var shipEl = qs('#summary-delivery');
    if (shipEl) {
      shipEl.textContent = ship === 0 ? (window.t ? window.t('Безкоштовно') : 'Безкоштовно') : fmt(ship);
      shipEl.classList.toggle('is-ship-free', ship === 0);
      shipEl.classList.remove('is-ship-muted');
    }

    var subEl = qs('#summary-subtotal');
    var totalEl = qs('#summary-total');
    var sub = parseMoney(subEl && subEl.textContent);
    if (totalEl) totalEl.textContent = fmt(sub + ship);
  }

  root.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-choice][data-name="delivery_method"]');
    if (btn) {
      window.setTimeout(syncDeliveryUI, 0);
    }
  });

  document.body.addEventListener('htmx:afterSwap', function (e) {
    if (e.detail && e.detail.target && e.detail.target.id === 'checkout-items') {
      syncDeliveryUI();
    }
  });

  syncDeliveryUI();
})();
