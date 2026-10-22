# Development and browser preview

For TV installation, use the [Docker setup guide](agent-tv-setup-guide.md). The tools here are for previewing or changing the interface.

## Try it on your computer

Use Node.js 22+ and Python 3.10+:

```sh
git clone https://github.com/mcncl/cleanframe-hisense.git
cd cleanframe-hisense
npm ci
npm run dev
```

Open [localhost:4795/home/](http://localhost:4795/home/). Arrow keys, Enter and Escape mirror remote navigation. The static preview has no TV connection; app/device commands explain that limitation. The preview binds to loopback and uses bundled public fonts. If port 4795 is occupied, use `npm run dev -- --port 4796` and open that port instead.

For browser checks, install Chromium with `npx playwright install chromium`. Linux environments may also need Playwright's system dependencies; CI uses `npx playwright install --with-deps chromium`. See [testing](testing.md) for the full commands.

## Run an isolated service demo

The service is tested on Python 3.12 with pinned requirements:

```sh
python3.12 -m venv .local/venv
.local/venv/bin/pip install -r hisense/requirements.txt
SIDEE_STATE_DIR="$PWD/.local/demo-state" .local/venv/bin/python hisense/server.py serve --demo --port 4796
```

Open `http://localhost:4796/` for management or `/home/` for the interface. Demo mode uses an example app catalogue and never connects to a TV. The separate ignored demo-state directory prevents preview settings/uploads from touching live pairing or artwork. Do not substitute your deployment's data directory. Automated integration tests use their own temporary directory and port.

## Runtime map

- `app/index.html`, `main.js`, `style.css`: List/Dock views, settings, panels, focus, preferences and wallpaper rotation.
- `app/platform.js`: static-preview defaults. The server substitutes `/api/config.js` for live configuration.
- `app/device.js`: ES5 XHR adapter for local app discovery and commands. Only the server holds TV pairing credentials.
- `hisense/server.py`: HTTP actions, paired MQTT/TLS, real app/source discovery, wallpaper preparation and optional Home return.
- `hisense/ambient.js` and `ambient.css`: idle fade and remote wake. `runtime.js` reports TV readiness, viewport, errors, focus and saved appearance/Home preferences to the local server.
- `hisense/sidee/`: pinned connection code; preserve its licence and provenance.

The stage is 1920 × 1080, uniformly scaled. Verify 1920 × 1080 and 1280 × 720. Keep TV JavaScript ES5-compatible; `node --check` alone does not enforce this. The reference TV uses Chromium 111 on VIDAA 9. Browser tests do not establish another firmware's compatibility.

## Preferences and captures

Preferences retain `cleanframe.home.v1` and fallback migration from `cleanframe.shore.v1`. Do not rename these keys during rebranding. Home holds one to nine apps. Native shortcuts retain their real targets and readable names.

The TV and a desktop preview each have their own localStorage. To reproduce an owner's appearance, obtain a fresh authorised `runtime.preferences` snapshot from the home server and seed `cleanframe.home.v1` in an isolated browser before loading `/home/`. Keep this snapshot private. That renders the same source and settings; it is not a direct screenshot of the TV. The adapter does not provide native VIDAA screen pixels.

`window.ShoreQA.state()` and `.where()` expose state/focus for isolated browser checks. Their historical name is retained. Browser tooling may shorten rotation intervals through `ShoreQA.minuteMs` in a test profile.

## Assets and packaging

All public fonts, wallpapers, icon marks and precomputed materials ship with the source. No asset-generation step is required to preview or install. Optional proprietary-font overlays are for local static previews only; `npm run dev` and CI use public fonts, and Docker never includes those private binaries. See [assets](assets.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).

The Docker image contains `app/`, `hisense/` and project notices. Runtime data is a private writable mount at `/data`. There is no signed TV widget to build. Use the setup guide for a real TV and [TV evidence](tv-status.md) for compatibility claims.
