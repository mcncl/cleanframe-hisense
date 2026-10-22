# CleanFrame Hisense

Read `docs/development.md` and `docs/interaction-behaviour.md` before app changes. Read `docs/for-agents.md` before device work and `docs/assets.md` before changing image materials or icon geometry.

For a new installation, follow `docs/agent-tv-setup-guide.md` in order and use `docs/hisense.md` for the protected HTTP actions. Confirm VIDAA as the TV operating system, verify the pinned pairing-file checksum, and preserve existing working state. Keep physical confirmation separate from API success. Use the running service rather than opening a competing paired connection.

Use ES5-compatible JavaScript in `app/` and the TV-facing files in `hisense/`. Node tools can use modern JavaScript. Preserve remote focus/navigation, localStorage preference migrations and precomputed material rendering. Keep device commands in `hisense/server.py` and the HTTP adapter in `app/device.js`.

Run `npm run check`; for UI changes also run `CLEANFRAME_PUBLIC_FONTS=1 npm run check:browser`. Run `npm run check:hisense` for server/adapter/idle changes and `.local/venv/bin/python -m unittest discover -s hisense -p 'test_*.py'` for Home-return changes. Tests must use isolated demo state and never contact a TV. Run `npm run check:public` before sharing source. Follow `CONTRIBUTING.md` and retain upstream copyright, licences and asset records.

Browser or repository work does not authorise TV access. Device tasks need the owner's instruction; announce installations, launches and restarts. Preserve the existing `cleanframehome` tile identity and server URL for upgrades. Confirm physical results with the owner; a sent request is not proof of a visible destination. Do not flash firmware or change native startup settings as part of launcher setup.

Keep pairing tokens, certificate bundles, control keys, personal photos, device identifiers, addresses and SSH details in ignored `.local/` or private deployment state. Do not put them in source, images, Docker layers, logs or issues. Public fonts must work without proprietary files. See `THIRD_PARTY_NOTICES.md`.

Preserve shared and uncommitted work. Use reversible deletion; do not reset, force-push or rewrite history without explicit authority. Use the contributor's own authenticated GitHub account. Publication and visibility changes require the owner's instruction.

Use a feature branch and pull request for repository changes. The required GitHub Actions check is `public-source` in the `Check` workflow; keep that job name stable for branch protection. Do not merge, change visibility or alter protection rules unless the task includes it.
