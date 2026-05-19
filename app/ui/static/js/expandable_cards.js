(function () {
  function initExpandableCards(root) {
    (root || document).querySelectorAll('.js-expandable-card').forEach(card => {
      if (card.dataset.expandableReady === 'true') return;

      const summary = card.querySelector('summary');
      if (!summary) return;

      card.dataset.expandableReady = 'true';
      summary.addEventListener('click', event => {
        event.preventDefault();

        if (card.classList.contains('is-open')) {
          card.classList.remove('is-open');
          setTimeout(() => card.removeAttribute('open'), 240);
          return;
        }

        card.setAttribute('open', '');
        requestAnimationFrame(() => card.classList.add('is-open'));
      });
    });
  }

  window.MockAPI = window.MockAPI || {};
  window.MockAPI.initExpandableCards = initExpandableCards;
  document.addEventListener('DOMContentLoaded', () => initExpandableCards(document));
})();
