(function () {
  'use strict';

  var NAME_RE = /^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ'ʼ'`’\- ]+$/;
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function t(s) {
    return window.t ? window.t(s) : s;
  }

  var MSG = {
    required: 'Поле обовʼязкове для заповнення',
    name: 'Імʼя не може містити цифри або спецсимволи. Будь ласка, використовуйте лише букви',
    nameShort: 'Вкажіть імʼя (мінімум 2 літери)',
    phone: 'Введіть номер у форматі +38 (0XX) XXX XX XX',
    email: 'Некоректний формат email',
    message: 'Напишіть хоча б кілька слів (від 10 символів)',
    consent: 'Потрібна згода на обробку даних',
    city: 'Вкажіть місто.',
    address: 'Вкажіть адресу або відділення.',
  };

  function digitsOnly(value) {
    return String(value || '').replace(/\D+/g, '');
  }

  function toUaDigits(raw) {
    var d = digitsOnly(raw);
    if (!d) return '';
    if (d.indexOf('380') === 0) return d.slice(0, 12);
    if (d.indexOf('38') === 0) return d.slice(0, 12);
    if (d.charAt(0) === '0') return ('38' + d).slice(0, 12);
    return ('380' + d).slice(0, 12);
  }

  function formatUaPhone(raw) {
    var d = toUaDigits(raw);
    if (!d) return '';
    var rest = d.indexOf('38') === 0 ? d.slice(2) : d;
    var a = rest.slice(0, 3);
    var b = rest.slice(3, 6);
    var c = rest.slice(6, 8);
    var e = rest.slice(8, 10);
    var out = '+38';
    if (!rest.length) return out;
    out += ' (' + a;
    if (a.length < 3) return out;
    out += ')';
    if (b.length) out += ' ' + b;
    if (c.length) out += ' ' + c;
    if (e.length) out += ' ' + e;
    return out;
  }

  function isValidUaPhone(raw) {
    var d = toUaDigits(raw);
    return d.length === 12 && /^380\d{9}$/.test(d);
  }

  function fieldWrap(input) {
    return (
      input.closest('.field, .pdp-quick__phone-wrap, .info-consent-wrap') ||
      input.closest('label')
    );
  }

  function errorEl(input) {
    var wrap = fieldWrap(input);
    if (!wrap) return null;
    return (
      wrap.querySelector('[data-field-error]') ||
      wrap.querySelector('.field__err') ||
      wrap.querySelector('.info-consent__err') ||
      wrap.querySelector('.pdp-quick__error') ||
      wrap.querySelector('.cb-field__err')
    );
  }

  function setState(input, ok, message) {
    var wrap = fieldWrap(input);
    var err = errorEl(input);
    var hasValue =
      input.type === 'checkbox' ? !!input.checked : !!String(input.value || '').trim();
    if (wrap) {
      wrap.classList.toggle('is-invalid', !ok);
      wrap.classList.toggle('is-valid', !!ok && hasValue);
    }
    input.setAttribute('aria-invalid', ok ? 'false' : 'true');
    if (err) err.textContent = ok ? '' : t(message || MSG.required);
  }

  function clearState(input) {
    var wrap = fieldWrap(input);
    var err = errorEl(input);
    if (wrap) {
      wrap.classList.remove('is-invalid', 'is-valid');
    }
    input.removeAttribute('aria-invalid');
    if (err) err.textContent = '';
  }

  function deliveryNeedsAddress(form) {
    var method = form.querySelector('input[name="delivery_method"]');
    var value = method ? method.value : '';
    return value === 'np' || value === 'courier';
  }

  function validateName(value, required) {
    var v = String(value || '').trim();
    if (!v) return required ? { ok: false, msg: MSG.required } : { ok: true, msg: '' };
    if (v.length < 2) return { ok: false, msg: MSG.nameShort };
    if (/\d/.test(v) || !NAME_RE.test(v)) return { ok: false, msg: MSG.name };
    return { ok: true, msg: '' };
  }

  function validatePhone(value) {
    var v = String(value || '').trim();
    if (!v) return { ok: false, msg: MSG.required };
    if (!isValidUaPhone(v)) return { ok: false, msg: MSG.phone };
    return { ok: true, msg: '' };
  }

  function validateEmail(value) {
    var v = String(value || '').trim();
    if (!v) return { ok: true, msg: '' };
    if (!EMAIL_RE.test(v)) return { ok: false, msg: MSG.email };
    return { ok: true, msg: '' };
  }

  function validateMessage(value) {
    var v = String(value || '').trim();
    if (!v) return { ok: false, msg: MSG.required };
    if (v.length < 10) return { ok: false, msg: MSG.message };
    return { ok: true, msg: '' };
  }

  function validateField(input, form) {
    var kind = input.getAttribute('data-validate');
    if (!kind || input.disabled || input.type === 'hidden') return true;

    var result = { ok: true, msg: '' };
    var value = input.type === 'checkbox' ? input.checked : input.value;

    if (kind === 'name') result = validateName(value, true);
    else if (kind === 'name-optional') result = validateName(value, false);
    else if (kind === 'phone') result = validatePhone(value);
    else if (kind === 'email') result = validateEmail(value);
    else if (kind === 'message') result = validateMessage(value);
    else if (kind === 'consent') {
      result = input.checked
        ? { ok: true, msg: '' }
        : { ok: false, msg: MSG.consent };
    } else if (kind === 'city') {
      if (deliveryNeedsAddress(form) && !String(value || '').trim()) {
        result = { ok: false, msg: MSG.city };
      }
    } else if (kind === 'address') {
      if (deliveryNeedsAddress(form) && !String(value || '').trim()) {
        result = { ok: false, msg: MSG.address };
      }
    } else if (kind === 'required') {
      if (!String(value || '').trim()) result = { ok: false, msg: MSG.required };
    }

    if (!String(input.value || '').trim() && kind !== 'consent' && result.ok) {
      clearState(input);
      return true;
    }

    setState(input, result.ok, result.msg);
    return result.ok;
  }

  function fields(form) {
    return Array.prototype.slice.call(form.querySelectorAll('[data-validate]'));
  }

  function validateForm(form) {
    var ok = true;
    var first = null;
    fields(form).forEach(function (input) {
      var valid = validateField(input, form);
      if (!valid && !first) first = input;
      if (!valid) ok = false;
    });
    form._firstInvalid = first;
    return ok;
  }

  function focusFirstInvalid(form) {
    var input = form._firstInvalid || form.querySelector('.is-invalid [data-validate], [aria-invalid="true"]');
    if (!input) return;
    try {
      input.focus({ preventScroll: false });
    } catch (e) {
      input.focus();
    }
    if (typeof input.scrollIntoView === 'function') {
      input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function applyPhoneMask(input) {
    var formatted = formatUaPhone(input.value);
    if (input.value !== formatted) input.value = formatted;
  }

  function onPhoneFocus(input) {
    if (!String(input.value || '').trim()) {
      input.value = '+38 (';
    }
  }

  function onPhoneBlur(input) {
    var d = toUaDigits(input.value);
    if (!d || d === '38' || d === '380') {
      input.value = '';
      clearState(input);
    }
  }

  document.addEventListener(
    'input',
    function (e) {
      var input = e.target;
      if (!input || !input.getAttribute) return;
      if (input.getAttribute('data-validate') === 'phone') {
        applyPhoneMask(input);
        if (input._touched) validateField(input, input.form || input.closest('form'));
        return;
      }
      if (input.getAttribute('data-validate') && input._touched) {
        validateField(input, input.form || input.closest('form'));
      }
    },
    true
  );

  document.addEventListener(
    'focusin',
    function (e) {
      var input = e.target;
      if (!input || input.getAttribute('data-validate') !== 'phone') return;
      onPhoneFocus(input);
    },
    true
  );

  document.addEventListener(
    'focusout',
    function (e) {
      var input = e.target;
      if (!input || !input.getAttribute || !input.getAttribute('data-validate')) return;
      input._touched = true;
      if (input.getAttribute('data-validate') === 'phone') onPhoneBlur(input);
      var form = input.form || input.closest('form');
      if (form) validateField(input, form);
    },
    true
  );

  document.addEventListener(
    'submit',
    function (e) {
      var form = e.target;
      if (!form || !form.matches || !form.matches('[data-validate-form]')) return;
      fields(form).forEach(function (el) {
        el._touched = true;
      });
      if (!validateForm(form)) {
        e.preventDefault();
        e.stopPropagation();
        if (typeof e.stopImmediatePropagation === 'function') e.stopImmediatePropagation();
        focusFirstInvalid(form);
      } else {
        fields(form).forEach(function (input) {
          if (input.getAttribute('data-validate') === 'phone' && isValidUaPhone(input.value)) {
            var d = toUaDigits(input.value);
            input.value = '+' + d;
          }
        });
      }
    },
    true
  );

  document.body.addEventListener('htmx:configRequest', function (e) {
    var form = e.target && e.target.closest ? e.target.closest('[data-validate-form]') : null;
    if (!form && e.target && e.target.matches && e.target.matches('[data-validate-form]')) {
      form = e.target;
    }
    if (!form) return;
    fields(form).forEach(function (el) {
      el._touched = true;
    });
    if (!validateForm(form)) {
      e.preventDefault();
      focusFirstInvalid(form);
    }
  });

  window.ZamkyFormValidation = {
    formatUaPhone: formatUaPhone,
    isValidUaPhone: isValidUaPhone,
    validateForm: validateForm,
  };
})();
