/* Browser preview defaults. Live configuration comes from the home server. */
(function () {
  'use strict';
  window.CleanFramePlatform = window.CleanFramePlatform || {
    name: 'Hisense', homeName: 'VIDAA Home', apps: [
      { id: 'plex', name: 'Plex', appId: 'service.plex', mark: false },
      { id: 'sbs', name: 'SBS On Demand', appId: 'service.sbs', mark: true },
      { id: 'abciview', name: 'ABC iview', appId: 'service.abciview', mark: true }
    ]
  };
}());
