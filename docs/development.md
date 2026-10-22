# Development

Use Node.js 22+ and Python 3.10+ for the static preview. The service is tested with Python 3.12 and the versions in `hisense/requirements.txt`. Run `npm ci`, then `npm run dev`; `/home/` serves the same interface assets used by the TV, with no TV access.

## Runtime map

- `app/index.html`, `main.js`, `style.css`: List/Dock views, settings, panels, focus, preferences and wallpaper rotation.
- `app/platform.js`: browser-preview defaults. The server substitutes `/api/config.js` for live configuration.
- `app/device.js`: ES5 XHR adapter for local app discovery and commands. Only the server holds TV pairing credentials.
- `hisense/server.py`: HTTP routes, paired MQTT/TLS connection, real app/source discovery, wallpaper preparation and optional Home return.
- `hisense/ambient.js` and `ambient.css`: idle fade and remote wake. `runtime.js` reports TV viewport/errors/focus to the local server.
- `hisense/sidee/`: pinned, unmodified connection code; preserve its licence and provenance.

The stage is 1920 × 1080, uniformly scaled. Verify 1920 × 1080 and 1280 × 720. Keep TV JavaScript ES5-compatible; `node --check` alone does not enforce this. The observed reference TV uses Chromium 111 on VIDAA 9. A browser test does not establish another firmware's compatibility.

Preferences retain `cleanframe.home.v1` and fallback migration from `cleanframe.shore.v1`, so existing installations keep their appearance and app order. Do not rename these keys during rebranding. Home holds one to nine apps. New native shortcuts retain their actual target and readable name.

`window.ShoreQA.state()` and `.where()` expose state/focus for isolated browser checks. The historical namespace remains to avoid unnecessary changes to shared interaction code.

## Local service

```sh
python3.12 -m venv .local/venv
.local/venv/bin/pip install -r hisense/requirements.txt
.local/venv/bin/python hisense/server.py serve --demo --port 4796
```

Demo mode never connects to a TV. Use a temporary `SIDEE_STATE_DIR` to isolate settings and uploads. Live pairing/deployment is documented in [setup](agent-tv-setup-guide.md); do not use a live state directory for tests.

The TV app is served under `/home/`; management is `/`. The Docker image contains only `app/`, `hisense/` and project notices. Runtime state is a writable mount at `/data`. Public fonts are bundled; an optional proprietary-font overlay is available only for local static previews and never enters the Docker image.

For rendering recipes read [assets](assets.md). For commands and physical checks read [testing](testing.md). Compatibility evidence belongs in [TV status](tv-status.md), without personal addresses or identifiers.
