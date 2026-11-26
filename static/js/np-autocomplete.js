(function () {
  'use strict';

  var root = document.querySelector('[data-checkout]');
  if (!root) return;

  var citiesUrl = root.getAttribute('data-np-cities-url') || '';
  var warehousesUrl = root.getAttribute('data-np-warehouses-url') || '';
  var cityInput = root.querySelector('[data-np-city]');
  var warehouseInput = root.querySelector('[data-np-warehouse]');
  var cityRef = root.querySelector('input[name="np_city_ref"]');
  var warehouseRef = root.querySelector('input[name="np_warehouse_ref"]');
  if (!citiesUrl || !warehousesUrl || !cityInput || !warehouseInput) return;

  var silent = false;
  var methodName = '';

  function t(text) {
    return window.t ? window.t(text) : text;
  }

  function method() {
    var input = root.querySelector('input[name="delivery_method"]');
    return (input && input.value) || 'np';
  }

  function boxFor(input, kind) {
    var wrap = input.closest ? input.closest('.np-ac') : null;
    var list = wrap ? wrap.querySelector('.np-ac__list') : null;
    if (!wrap || !list) return null;
    return {
      kind: kind,
      input: input,
      wrap: wrap,
      list: list,
      card: input.closest ? input.closest('.checkout-card') : null,
      items: [],
      active: -1,
      timer: null,
      ctrl: null,
      hold: false,
      holdTimer: null,
    };
  }

  var cityBox = boxFor(cityInput, 'city');
  var warehouseBox = boxFor(warehouseInput, 'warehouse');
  if (!cityBox || !warehouseBox) return;

  function setExpanded(box, open) {
    box.input.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) box.wrap.classList.add('is-open');
    else box.wrap.classList.remove('is-open');
    var card = (cityBox && cityBox.card) || (warehouseBox && warehouseBox.card);
    if (!card) return;
    var cityOpen = cityBox && !cityBox.list.hidden;
    var warehouseOpen = warehouseBox && !warehouseBox.list.hidden;
    card.classList.toggle('is-np-open', !!(cityOpen || warehouseOpen));
  }

  function clearList(box) {
    while (box.list.firstChild) box.list.removeChild(box.list.firstChild);
    box.items = [];
    box.active = -1;
    box.input.removeAttribute('aria-activedescendant');
  }

  function closeBox(box) {
    box.list.hidden = true;
    box.list.classList.remove('is-up');
    setExpanded(box, false);
    clearList(box);
  }

  function closeAll() {
    closeBox(cityBox);
    closeBox(warehouseBox);
  }

  function place(box) {
    var rect = box.input.getBoundingClientRect();
    var below = window.innerHeight - rect.bottom;
    if (below < 180 && rect.top > below) box.list.classList.add('is-up');
    else box.list.classList.remove('is-up');
  }

  function openBox(box) {
    var other = box.kind === 'city' ? warehouseBox : cityBox;
    if (other && other !== box && !other.list.hidden) closeBox(other);
    place(box);
    box.list.hidden = false;
    setExpanded(box, true);
  }

  function setActive(box, index) {
    var options = box.list.querySelectorAll('.np-ac__opt:not(.is-empty)');
    var i;
    for (i = 0; i < options.length; i += 1) {
      options[i].classList.remove('is-active');
      options[i].setAttribute('aria-selected', 'false');
    }
    if (!options.length || index < 0 || index >= options.length) {
      box.active = -1;
      box.input.removeAttribute('aria-activedescendant');
      return;
    }
    options[index].classList.add('is-active');
    options[index].setAttribute('aria-selected', 'true');
    box.active = index;
    if (options[index].id) box.input.setAttribute('aria-activedescendant', options[index].id);
    if (options[index].scrollIntoView) {
      try {
        options[index].scrollIntoView(false);
      } catch (err) {
        /* старий iOS */
      }
    }
  }

  function render(box, items) {
    clearList(box);
    box.items = items || [];
    if (!box.items.length) {
      var empty = document.createElement('li');
      empty.className = 'np-ac__opt is-empty';
      empty.setAttribute('role', 'option');
      empty.setAttribute('aria-disabled', 'true');
      empty.textContent = t('Нічого не знайдено');
      box.list.appendChild(empty);
      openBox(box);
      return;
    }
    var i;
    for (i = 0; i < box.items.length; i += 1) {
      var item = box.items[i] || {};
      var li = document.createElement('li');
      li.className = 'np-ac__opt';
      li.setAttribute('role', 'option');
      li.id = (box.kind === 'city' ? 'np-city-opt-' : 'np-wh-opt-') + i;
      li.setAttribute('data-i', String(i));
      li.textContent = item.label || '';
      box.list.appendChild(li);
    }
    openBox(box);
    setActive(box, -1);
  }

  function setInput(input, value) {
    silent = true;
    input.value = value;
    silent = false;
  }

  function choose(box, index) {
    var item = box.items[index];
    if (!item || !item.ref) return;
    setInput(box.input, item.label || '');
    if (box.kind === 'city') {
      if (cityRef) cityRef.value = item.ref;
      if (warehouseRef) warehouseRef.value = '';
      setInput(warehouseInput, '');
      closeBox(warehouseBox);
    } else if (warehouseRef) {
      warehouseRef.value = item.ref;
    }
    closeBox(box);
  }

  function endpoint(box, query) {
    var base = box.kind === 'city' ? citiesUrl : warehousesUrl;
    var url = base + (base.indexOf('?') === -1 ? '?' : '&') + 'q=' + encodeURIComponent(query);
    if (box.kind === 'warehouse' && cityRef && cityRef.value) {
      url += '&city=' + encodeURIComponent(cityRef.value);
    }
    return url;
  }

  function queryBox(box) {
    if (method() !== 'np') {
      closeBox(box);
      return;
    }
    var value = (box.input.value || '').trim();
    if (value.length < 2) {
      closeBox(box);
      return;
    }
    if (box.ctrl && box.ctrl.abort) {
      try {
        box.ctrl.abort();
      } catch (err) {
        /* вже скасовано */
      }
    }
    var ctrl = typeof AbortController === 'function' ? new AbortController() : null;
    box.ctrl = ctrl;
    var opts = {
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
    };
    if (ctrl) opts.signal = ctrl.signal;
    fetch(endpoint(box, value), opts)
      .then(function (response) {
        if (!response.ok) throw new Error('np');
        return response.json();
      })
      .then(function (data) {
        if (box.ctrl !== ctrl || method() !== 'np') return;
        if (!data || data.available === false) {
          closeBox(box);
          return;
        }
        render(box, data.items || []);
      })
      .catch(function (err) {
        if (err && err.name === 'AbortError') return;
        if (box.ctrl === ctrl) closeBox(box);
      });
  }

  function schedule(box) {
    if (box.timer) clearTimeout(box.timer);
    if (method() !== 'np') {
      closeBox(box);
      return;
    }
    if ((box.input.value || '').trim().length < 2) {
      closeBox(box);
      return;
    }
    box.timer = setTimeout(function () {
      queryBox(box);
    }, 250);
  }

  function move(box, step) {
    var options = box.list.querySelectorAll('.np-ac__opt:not(.is-empty)');
    if (!options.length) return;
    var next = box.active + step;
    if (next < 0) next = options.length - 1;
    if (next >= options.length) next = 0;
    setActive(box, next);
  }

  function onKey(box, event) {
    if (method() !== 'np') return;
    var open = !box.list.hidden;
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      if (!open && (box.input.value || '').trim().length < 2) return;
      event.preventDefault();
      if (!open) {
        queryBox(box);
        return;
      }
      move(box, event.key === 'ArrowDown' ? 1 : -1);
      return;
    }
    if (event.key === 'Enter' && open) {
      event.preventDefault();
      if (event.stopPropagation) event.stopPropagation();
      if (box.active >= 0) choose(box, box.active);
      return;
    }
    if (event.key === 'Escape' && open) {
      event.preventDefault();
      closeBox(box);
    }
  }

  function bindList(box) {
    box.list.addEventListener('mousedown', function (event) {
      box.hold = true;
      event.preventDefault();
    });
    box.list.addEventListener(
      'touchstart',
      function () {
        box.hold = true;
      },
      { passive: true }
    );
    box.list.addEventListener('click', function (event) {
      var option = event.target.closest ? event.target.closest('.np-ac__opt') : null;
      box.hold = false;
      if (!option || option.getAttribute('aria-disabled') === 'true') return;
      choose(box, parseInt(option.getAttribute('data-i'), 10));
    });
    box.list.addEventListener('mouseover', function (event) {
      var option = event.target.closest ? event.target.closest('.np-ac__opt') : null;
      if (!option || option.classList.contains('is-empty')) return;
      setActive(box, parseInt(option.getAttribute('data-i'), 10));
    });
  }

  function bindBlur(box) {
    box.input.addEventListener('blur', function () {
      setTimeout(function () {
        if (box.hold) {
          box.hold = false;
          if (box.holdTimer) clearTimeout(box.holdTimer);
          box.holdTimer = setTimeout(function () {
            if (document.activeElement !== box.input) closeBox(box);
          }, 400);
          return;
        }
        closeBox(box);
      }, 200);
    });
  }

  function arm(input, box, onType) {
    input.addEventListener('input', function () {
      if (silent) return;
      onType();
      schedule(box);
    });
    input.addEventListener('keydown', function (event) {
      onKey(box, event);
    });
    bindList(box);
    bindBlur(box);
  }

  arm(cityInput, cityBox, function () {
    if (cityRef) cityRef.value = '';
    if (warehouseRef) warehouseRef.value = '';
  });
  arm(warehouseInput, warehouseBox, function () {
    if (warehouseRef) warehouseRef.value = '';
  });

  function syncMode() {
    var np = method() === 'np';
    var boxes = [cityBox, warehouseBox];
    var i;
    for (i = 0; i < boxes.length; i += 1) {
      var box = boxes[i];
      if (np) {
        box.input.setAttribute('role', 'combobox');
        box.input.setAttribute('aria-autocomplete', 'list');
        box.input.setAttribute('aria-controls', box.list.id);
        box.input.setAttribute('aria-expanded', box.list.hidden ? 'false' : 'true');
        box.input.setAttribute('aria-haspopup', 'listbox');
        box.input.setAttribute('autocorrect', 'off');
        box.input.setAttribute('autocapitalize', 'none');
        box.input.setAttribute('spellcheck', 'false');
      } else {
        closeBox(box);
        box.input.removeAttribute('role');
        box.input.removeAttribute('aria-autocomplete');
        box.input.removeAttribute('aria-controls');
        box.input.removeAttribute('aria-expanded');
        box.input.removeAttribute('aria-haspopup');
        box.input.removeAttribute('aria-activedescendant');
        box.input.removeAttribute('autocorrect');
        box.input.removeAttribute('autocapitalize');
        box.input.removeAttribute('spellcheck');
      }
    }
    if (np) warehouseInput.setAttribute('autocomplete', 'off');
    else warehouseInput.removeAttribute('autocomplete');
  }

  document.addEventListener('click', function (event) {
    var target = event.target;
    var choice = target.closest ? target.closest('[data-choice][data-name="delivery_method"]') : null;
    if (choice && root.contains(choice)) {
      var next = choice.getAttribute('data-value') || '';
      if (next !== methodName) {
        methodName = next;
        closeAll();
        if (cityRef) cityRef.value = '';
        if (warehouseRef) warehouseRef.value = '';
        syncMode();
      }
      return;
    }
    var inside = target.closest ? target.closest('.np-ac') : null;
    if (!inside || !root.contains(inside)) closeAll();
  });

  methodName = method();
  syncMode();
})();
