(function () {
  'use strict';

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function reducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function initCarousel(section) {
    var track = qs('[data-carousel-track]', section);
    if (!track) return;
    var items = Array.prototype.filter.call(track.children, function (node) {
      return node.nodeType === 1;
    });
    var prev = qs('[data-carousel-prev]', section);
    var next = qs('[data-carousel-next]', section);

    function stepSize() {
      if (!items.length) return 200;
      if (items.length < 2) return items[0].getBoundingClientRect().width;
      var first = items[0].getBoundingClientRect();
      var second = items[1].getBoundingClientRect();
      var delta = second.left - first.left;
      return Math.abs(delta) > 8 ? delta : first.width + 12;
    }

    function atEnd() {
      return track.scrollLeft + track.clientWidth >= track.scrollWidth - 8;
    }

    function scrollByStep(dir) {
      var behavior = reducedMotion() ? 'auto' : 'smooth';
      if (dir > 0 && atEnd()) {
        track.scrollTo({ left: 0, behavior: behavior });
        return;
      }
      track.scrollBy({ left: stepSize() * dir, behavior: behavior });
    }

    if (prev) {
      prev.addEventListener('click', function () {
        scrollByStep(-1);
      });
    }
    if (next) {
      next.addEventListener('click', function () {
        scrollByStep(1);
      });
    }
  }

  qsa('[data-home-carousel]').forEach(initCarousel);
})();
