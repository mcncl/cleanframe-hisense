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

`check:hisense` runs the real Python service in demo mode with a temporary state directory, then checks routes, request protection, shortcuts, honest Fire TV fallback, preference persistence, generated photo materials, idle fade and held-key wake. It uses `.local/venv/bin/python` by default; set `CLEANFRAME_PYTHON` to another Python with the required dependencies.

Home-return unit tests cover pauses, cooldown retries without another broadcast, worker timeouts, native launches clearing pauses, latest-state precedence and leaving Art/input/standby states alone. `check:public` checks candidate source and reachable Git paths for private state, known credential formats and unexpected font files. It is a bounded check, not a complete secret audit.

Manual browser review should include List/Dock, Photo/Light/Dark, one and nine apps, explicit OK selection, Back cancellation and single visible focus. The optional `node scripts/check-performance.mjs` audit is a Chromium comparison, not a TV benchmark.

Device checks require an owner-authorised task. Announce installations, launches and restarts. Confirm real app destinations, Home from Plex (including rapid repeat), saved appearance and uploaded artwork, idle/wake, Art Gallery, normal power-on and restart persistence. Keep observed results separate from API success; see [TV evidence](tv-status.md).
