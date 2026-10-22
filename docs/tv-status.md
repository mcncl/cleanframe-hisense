# TV evidence

Updated 22 October 2026. These observations apply to one reference installation; they are not a general VIDAA compatibility claim.

| Item | Evidence |
| --- | --- |
| TV | Hisense 55S7NAU CanvasTV, Australian model |
| Firmware | V0000.09.60X.Q0609, VIDAA 9 |
| Browser | Observed Chromium 111 / Odin 111, aarch64 MTK9618 |
| Host | Ubuntu Server, Docker Compose |
| Local connection | PIN-paired MQTT/TLS; real installed apps and HDMI sources read successfully |
| Custom tile | Owner confirmed CleanFrame Home appears, opens and renders |
| Controls | Owner confirmed remote navigation and appearance settings |
| Native apps | Owner confirmed Plex, SBS On Demand, ABC iview, IPTV Smarters and Stremio Lite launch from Home |
| Home return | Owner confirmed two returns from Plex using Hisense Home, including a quick repeat; service logs confirmed cooldown deferral followed by retry |

Still unverified on the physical TV: idle fade/wake, custom uploaded photo appearance, normal power-on after another app, native Art Gallery and sensor/standby behaviour, and tile persistence after restart. The optional 10/9Now paths have not been physically verified. The reference Fire TV fallback is an HDMI switch only.

The standalone cleanup is covered by offline resource, interaction, HTTP integration and Home-return regression checks. It preserves tile identity, URL paths and preference keys. These checks do not themselves reconfirm physical behaviour after a deployment.

For additional TVs, report the model, full firmware, host runtime, pairing result and visible outcomes. Omit serials, tokens, certificate material and network addresses.
