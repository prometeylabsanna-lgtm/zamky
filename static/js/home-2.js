(function () {
  'use strict';

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function t(s) {
    return window.t ? window.t(s) : s;
  }

  function getCsrf() {
    var inp = qs('input[name=csrfmiddlewaretoken]');
    return inp ? inp.value : '';
  }

  (function initPhotoModal() {
    var modal = qs('#home-photo-modal');
    if (!modal) return;
    var form = qs('#home-photo-form');
    var fileInput = qs('#home-photo-files');
    var drop = qs('[data-photo-drop]');
    var previews = qs('[data-photo-previews]');
    var body = qs('#home-photo-body');
    var done = qs('#home-photo-done');
    var doneMsg = qs('[data-photo-done-msg]');
    var files = [];

    function openModal() {
      modal.hidden = false;
      modal.classList.add('is-open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }

    function closeModal() {
      modal.classList.remove('is-open');
      modal.hidden = true;
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }

    qsa('[data-photo-open]').forEach(function (btn) {
      btn.addEventListener('click', openModal);
    });
    qsa('[data-photo-close]', modal).forEach(function (btn) {
      btn.addEventListener('click', closeModal);
    });

    function renderPreviews() {
      if (!previews) return;
      if (!files.length) {
        previews.hidden = true;
        previews.innerHTML = '';
        if (drop) drop.hidden = false;
        updateSubmitLabel();
        return;
      }
      if (drop) drop.hidden = true;
      previews.hidden = false;
      previews.innerHTML = '';
      files.forEach(function (file, idx) {
        var wrap = document.createElement('div');
        wrap.className = 'home-photo-previews__item';
        var img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.alt = '';
        var rm = document.createElement('button');
        rm.type = 'button';
        rm.className = 'home-photo-previews__remove';
        rm.setAttribute('aria-label', t('Видалити'));
        rm.innerHTML =
          '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.5"><path d="M6 6l12 12M18 6 6 18"></path></svg>';
        rm.addEventListener('click', function () {
          files.splice(idx, 1);
          renderPreviews();
        });
        wrap.appendChild(img);
        wrap.appendChild(rm);
        previews.appendChild(wrap);
      });
      if (files.length < 5) {
        var add = document.createElement('button');
        add.type = 'button';
        add.className = 'home-photo-drop__btn';
        add.style.minHeight = '76px';
        add.textContent = '+';
        add.addEventListener('click', pickFiles);
        previews.appendChild(add);
      }
      updateSubmitLabel();
    }

    function updateSubmitLabel() {
      var btn = qs('[data-photo-submit] span', form);
      if (!btn) return;
      btn.textContent =
        files.length > 0
          ? t('Надіслати') + ' ' + files.length + ' ' + t('фото')
          : t('Надіслати фото');
    }

    function addFiles(list) {
      Array.from(list || [])
        .filter(function (f) {
          return f.type && f.type.indexOf('image/') === 0;
        })
        .slice(0, 5 - files.length)
        .forEach(function (f) {
          files.push(f);
        });
      renderPreviews();
    }

    function pickFiles() {
      if (fileInput) fileInput.click();
    }

    qsa('[data-photo-pick]').forEach(function (btn) {
      btn.addEventListener('click', pickFiles);
    });

    if (fileInput) {
      fileInput.addEventListener('change', function () {
        addFiles(fileInput.files);
        fileInput.value = '';
      });
    }

    if (drop) {
      drop.addEventListener('dragover', function (e) {
        e.preventDefault();
        drop.classList.add('is-over');
      });
      drop.addEventListener('dragleave', function () {
        drop.classList.remove('is-over');
      });
      drop.addEventListener('drop', function (e) {
        e.preventDefault();
        drop.classList.remove('is-over');
        addFiles(e.dataTransfer.files);
      });
    }

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var global = qs('[data-photo-global]', form);
        if (!files.length) {
          if (global) global.textContent = t('Додайте хоча б одне фото');
          return;
        }
        if (window.ZamkyFormValidation && !window.ZamkyFormValidation.validateForm(form)) {
          return;
        }
        if (global) global.textContent = '';
        var fd = new FormData(form);
        fd.delete('photos');
        files.forEach(function (f) {
          fd.append('photos', f);
        });
        fetch(form.action, {
          method: 'POST',
          body: fd,
          headers: {
            Accept: 'application/json',
            'X-CSRFToken': getCsrf(),
          },
          credentials: 'same-origin',
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            if (data && data.ok) {
              if (body) body.hidden = true;
              if (done) done.hidden = false;
              if (doneMsg) {
                doneMsg.textContent =
                  t('Майстер перегляне фото і надішле варіанти протягом 15 хвилин.');
              }
            } else if (global) {
              global.textContent = t('Не вдалося надіслати. Перевірте дані.');
            }
          })
          .catch(function () {
            if (global) global.textContent = t('Не вдалося надіслати. Спробуйте ще раз.');
          });
      });
    }

    var again = qs('[data-photo-again]', modal);
    if (again) {
      again.addEventListener('click', function () {
        files = [];
        renderPreviews();
        if (body) body.hidden = false;
        if (done) done.hidden = true;
      });
    }
  })();
})();
