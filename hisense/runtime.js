/* Local diagnostics for TV rendering; sent only to the home server. */
(function () {
  'use strict';
  var config = window.CleanFramePlatform || {}, errors = [], tries = 0;
  function report() {
    var xhr = new XMLHttpRequest(), qa = window.ShoreQA, isReady = !!(qa && qa.ready && qa.ready());
    var state = isReady && qa.state ? qa.state() : null;
    var value = { ready: isReady, width: window.innerWidth, height: window.innerHeight,
      engine: navigator.userAgent, errors: errors, location: qa && qa.where ? qa.where() : null };
    if (state) value.preferences = { look: state.look, dock: state.dock, appRecords: state.appRecords,
      wallpaper: state.wallpaper, mode: state.mode, lastApp: state.lastApp };
    xhr.open('POST', '/api/runtime', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-CleanFrame-Key', config.controlKey);
    xhr.send(JSON.stringify(value));
  }
  window.addEventListener('error', function (event) {
    if (errors.length < 8) errors.push(String(event.message || 'Resource failed: ' + (event.target.src || event.target.href || '')).slice(0, 300));
    report();
  }, true);
  function ready() {
    tries++;
    if (window.ShoreQA && window.ShoreQA.ready && window.ShoreQA.ready() || tries >= 30) report();
    else setTimeout(ready, 500);
  }
  window.addEventListener('load', ready);
  document.addEventListener('keyup', function () { setTimeout(report, 100); });
}());
