# Validation

All automated checks below are isolated from the TV.

```sh
npm ci
npm run check
npx playwright install chromium
CLEANFRAME_PUBLIC_FONTS=1 npm run check:browser
python3.12 -m venv .local/venv
.local/venv/bin/pip install -r hisense/requirements.txt
npm run check:hisense
.local/venv/bin/python -m unittest discover -s hisense -p 'test_*.py' -v
npm run check:public
```

`check` validates JavaScript syntax and bundled HTML/CSS/catalogue resources. `check:browser` exercises the actual UI and HTTP adapter with isolated mocked transport: migrations, both layouts, focus, settings, failure recovery, app editing, fonts, all wallpaper bundles and 720p scaling. Nine-app fixtures deliberately exercise the maximum; live defaults remain Plex, SBS and ABC. Reports and screenshots go to ignored `.local/qa/`.

`check:hisense` runs the real Python service in demo mode with a temporary state directory, then checks routes, request protection, shortcuts, honest Fire TV fallback, preference persistence, runtime appearance snapshots, generated photo materials, idle fade and held-key wake. It uses `.local/venv/bin/python` by default; set `CLEANFRAME_PYTHON` to another Python with the required dependencies.

Unit tests cover Home pauses, cooldown retries without another broadcast, worker timeouts, native launches clearing pauses, latest-state precedence and leaving Art/input/standby states alone. Navigation tests reject power/non-navigation keys and commands when CleanFrame is not foreground. `check:public` checks candidate source and reachable Git paths for private state, known credential formats and unexpected font files. It is a bounded check, not a complete secret audit.

CI uses Node.js 22 and Python 3.12, installs the pinned Python requirements, then runs these same checks. Its stable check name is **`public-source`** in the **`Check`** workflow. The integration test consumes every HTTP response body, including status-only image checks, for compatibility with Node 22's HTTP client.

For documentation changes, check local links/anchors, verify command names against the code, and validate the example Compose configuration without starting it. The pinned pairing download can be verified by checksum without contacting a TV. Do not exercise real pairing, installation or navigation just to validate documentation.

Manual browser review should include List/Dock, Photo/Light/Dark, one and nine apps, explicit OK selection, Back cancellation and single visible focus. The optional `node scripts/check-performance.mjs` audit is a Chromium comparison, not a TV benchmark.

Device checks require an owner-authorised task. Announce installations, launches and restarts. Confirm real app destinations, Home from Plex (including rapid repeat), saved appearance and uploaded artwork, idle/wake, Art Gallery, normal power-on and restart persistence. Keep observed results separate from API success; see [TV evidence](tv-status.md).
