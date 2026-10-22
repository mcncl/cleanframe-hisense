/* One idle timer; the first navigation press wakes without activating a tile. */
(function () {
  'use strict';
  var config = window.CleanFramePlatform || {}, timer = 0, asleep = false, wakeKey = null, overlay;
  var navigation = { 8: true, 13: true, 27: true, 37: true, 38: true, 39: true, 40: true, 461: true, 10009: true };
  overlay = document.createElement('div'); overlay.id = 'ambientPhoto'; overlay.setAttribute('aria-hidden', 'true');
  document.body.appendChild(overlay);
  function isHome() { return window.ShoreQA && window.ShoreQA.state().view === 'home'; }
  function schedule() {
    clearTimeout(timer);
    if (!config.idleSeconds || document.hidden) return;
    timer = setTimeout(function () {
      if (isHome()) {
        var photo = document.getElementById('photo');
        if (!photo || !photo.complete || !photo.naturalWidth) { schedule(); return; }
        overlay.style.backgroundImage = 'url("' + photo.src.replace(/"/g, '%22') + '")';
        document.body.classList.add('ambient'); asleep = true;
      } else schedule();
    }, config.idleSeconds * 1000);
  }
  function wake(event) {
    if (event.type === 'keydown' && !navigation[event.keyCode]) return;
    if (event.type === 'keydown' && wakeKey === event.keyCode) { event.preventDefault(); event.stopImmediatePropagation(); return; }
    if (asleep) {
      asleep = false; document.body.classList.remove('ambient');
      if (event.type === 'keydown') wakeKey = event.keyCode;
      if (event.type !== 'mousemove') { event.preventDefault(); event.stopImmediatePropagation(); }
    }
    schedule();
  }
  document.addEventListener('keydown', wake, true);
  document.addEventListener('keyup', function (event) { if (wakeKey === event.keyCode) wakeKey = null; }, true);
  document.addEventListener('click', wake, true);
  document.addEventListener('mousemove', wake, true);
  document.addEventListener('visibilitychange', function () { asleep = false; document.body.classList.remove('ambient'); schedule(); });
  window.addEventListener('focus', schedule);
  window.Hisense_onAppShow = function () { document.dispatchEvent(new Event('visibilitychange')); window.dispatchEvent(new Event('focus')); };
  window.Hisense_onAppHide = function () { clearTimeout(timer); };
  window.CleanFrameAmbient = { sleeping: function () { return asleep; }, reset: schedule };
  schedule();
}());
