  function setStage(unit, requested, save = false) {
    const stage = ['plan','draft','review','next'].includes(requested) ? requested : 'draft';
    for (const node of unit.querySelectorAll('[data-ww-step]')) node.hidden = node.dataset.wwStep !== stage;
    for (const link of unit.querySelectorAll('.ww-progress a')) {
      if (link.hash === '#'+unit.id+'-'+stage) link.setAttribute('aria-current','step');
      else link.removeAttribute('aria-current');
    }
    unit.dataset.wwCurrentStage=stage;
    if (save && field(unit,'stage').value !== stage && !put(field(unit,'stage'), stage)) fail();
    return stage;
  }
