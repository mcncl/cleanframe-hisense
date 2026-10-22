/* VIDAA bridge. Only the server holds the TV pairing credentials. */
(function () {
  'use strict';
  var config = window.CleanFramePlatform || {};
  function preview(done) {
    if (config.controlKey) return false;
    done({ message: 'Open CleanFrame on the TV to use this control.', detail: 'The web preview cannot control the TV.' });
    return true;
  }
  function request(path, value, done) {
    if (preview(done)) return;
    var xhr = new XMLHttpRequest(), finished = false;
    function finish(error, result) { if (finished) return; finished = true; done(error, result); }
    xhr.open(value ? 'POST' : 'GET', path, true);
    xhr.timeout = 15000;
    if (value) { xhr.setRequestHeader('Content-Type', 'application/json'); xhr.setRequestHeader('X-CleanFrame-Key', config.controlKey); }
    xhr.onload = function () {
      var result;
      try { result = JSON.parse(xhr.responseText); }
      catch (e) { finish({ message: 'The home server returned an unreadable response.' }); return; }
      if (xhr.status < 200 || xhr.status >= 300) finish({ message: result.error || 'The TV did not accept this action.' });
      else finish(null, result);
    };
    xhr.onerror = xhr.ontimeout = function () { finish({ message: 'Cannot reach your home server.', detail: 'Check that the server is running and the TV is connected to your network.' }); };
    xhr.send(value ? JSON.stringify(value) : null);
  }
  function launchApp(id, done) { request('/api/launch', { id: id }, done); }
  window.FrameDevice = {
    apps: function (done) { request('/api/apps', null, function (err, value) { done(err, value && value.apps); }); },
    launchApp: launchApp,
    launch: function (id, done) { launchApp('service.' + id, done); },
    art: function (done) { launchApp('control.art', done); },
    home: function (done) { launchApp('control.home', done); },
    settings: function (done) { launchApp('control.settings', done); }
  };
}());
