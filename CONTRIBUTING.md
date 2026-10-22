# Contributing to CleanFrame Hisense

Start with the README and [development guide](docs/development.md). Keep remote interaction simple, use ES5-compatible TV JavaScript, and preserve preference migration and cached rendering. Use bundled public fonts for screenshots and checks.

Run `npm run check`, the relevant browser/integration/Home-return checks from [testing](docs/testing.md), and `npm run check:public`. Automated tests must use isolated demo state and never contact a TV.

For a bug, describe the trigger, expected and actual behaviour, model/firmware and what was observed physically. For a feature, explain how it helps someone using the remote. Contributions should state validation and untested device behaviour. Test List/Dock and single focus when changing interaction; include a screenshot for visual changes.

Use a feature branch and open a pull request against `main`. The `Check` workflow's `public-source` check must pass. Keep installation guidance consistent with `hisense/compose.yaml` and the actual HTTP actions; describe prerequisites, commands, expected results and recovery. A documentation example must not require the maintainer's private files or a live TV for automated validation.

Device work needs the owner's instruction. Preserve existing tile identity and state. Never include pairing tokens, certificate bundles, control keys, serials, personal photos, addresses or SSH configuration in issues or commits. Keep private diagnostics under `.local/`.

Original CleanFrame code remains credited to Nathan Clark under MIT; Hisense contributions use MIT as well. Preserve Sidee and asset notices. Add only assets you have permission to redistribute and record their provenance. The app must work without paid fonts. Read [third-party notices](THIRD_PARTY_NOTICES.md) before adding assets.
