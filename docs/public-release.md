# Preparing a release

The repository is maintained as an independent Hisense project. Keep the README's CleanFrame attribution, original MIT copyright, Sidee provenance and all font/icon/photo notices.

Before sharing source, run the checks in [testing](testing.md), inspect `git status` and the staged diff, and run `npm run check:public`. Review tracked paths and reachable history as well as current files. Pairing state, `certs.bin.k`, `control-key`, `.env`, personal photographs, home-network details and SSH credentials must remain private.

The Docker build copies only `app/`, `hisense/` and project notices. Check `.dockerignore` before expanding the context. Runtime credentials belong in the private `/data` mount, never an image layer. Public runtime fonts are Manrope, Geist and Newsreader; paid font binaries stay out of source and images.

Browser checks establish interface behaviour, not physical compatibility. Publish the exact model/firmware evidence and open checks from [TV status](tv-status.md), and disclose the separately supplied client-bundle prerequisite. Another firmware may reject tile installation or omit the state broadcasts needed for Home return.

Create releases or change repository visibility only when the owner requests it. A private repository is not permission to commit secrets.
