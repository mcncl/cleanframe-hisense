# Public-release checklist

This is the maintainer's handoff before changing repository visibility. The project can be shared as experimental source for the documented model; it should not be described as a universal or one-click Hisense installer.

## Check the source and docs

1. Review the final diff and run the checks in [testing](testing.md). Confirm the latest `main` commit has a successful `Check` workflow, including **`public-source`**.
2. Run `npm run check:public`. Inspect tracked files and reachable history as well as the current tree. The script is a bounded credential/path/font check, not a complete secret or asset-rights audit.
3. Keep `.env`, `session.json`, `certs.bin.k`, `control-key`, personal photos, addresses, SSH details and private recovery/setup records out of Git and Docker layers. The pairing-file download belongs in the private data mount; do not add the bundle to the repository or image.
4. Check that README links, model evidence and setup instructions agree. The setup guide must include the pinned download/checksum, correct paths and UID/GID, one-client pairing rule, real TV verification and off/stop recovery route.
5. Preserve open checks in [TV evidence](tv-status.md). Browser rendering, API success and Home return do not establish power-on, Art Gallery or restart behaviour.
6. Retain upstream copyright, licences and asset credits. The README demo's edited-photo/browser-render provenance remains in [image notes](images/README.md).

The root source originated from [CleanFrame](https://github.com/nthnclrk/CleanFrame) commit `fa537d1892b71d2de2bf94c24cbff3812e9f70d5`. The selected [Sidee](https://github.com/Empi9245/Sidee) modules are pinned to `36095890dbf27e3daf1cf9c461bc62f8e7cad175`. Their source and MIT notices remain with the project. Public runtime fonts are Manrope, Geist and Newsreader.

## Publication and branch protection

The owner makes the visibility change after reviewing the result. Do not publish automatically as part of a docs, browser or device task.

For `main`, configure protection to:

- Require a pull request and the **`public-source`** check from GitHub Actions. The workflow is named **`Check`**; the actual check-run name is `public-source`.
- Require resolved review conversations and block force pushes/deletion.
- Add review approvals when another reviewer is available. Decide whether the rules also apply to administrators.

Keep the job name stable so the required check continues to match. GitHub Free supports protected branches on public repositories; private-repository availability depends on the plan. See [GitHub's branch-protection documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

After publication, keep setup examples generic and ask contributors for model, firmware and visible results rather than private device identifiers. Add tested models only when evidence is available.
