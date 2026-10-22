# CleanFrame Hisense

A quiet home screen for Hisense VIDAA TVs: your apps, a photograph and the time, controlled with the TV remote.

This is an independent adaptation of [CleanFrame by Nathan Clark](https://github.com/nthnclrk/CleanFrame). Its interface, remote navigation, wallpapers and rendering approach come from that project. This repository maintains the Hisense implementation, with a Docker service and local TV controls in place of the original Samsung integration.

![Hisense browser preview with Plex, SBS On Demand and ABC iview](docs/images/cleanframe-hisense.jpg)

## What it does

- List and Dock layouts, app selection and ordering, wallpaper rotation and saved appearance settings.
- Launch installed VIDAA apps and switch HDMI inputs using the TV's PIN-paired local connection.
- Upload your own photograph and fade the interface after an idle interval; the first remote press brings the controls back.
- Optionally return to CleanFrame when the Hisense remote opens VIDAA Home.
- Open the TV's existing Art Gallery and settings.

The interface runs as a TV web-app tile. An always-on home server hosts it and handles TV commands. This is a launcher, not replacement firmware: the TV keeps its operating system and native apps. VIDAA does not become Android, and Fire TV APKs cannot be installed through this project. A Fire TV shortcut can switch to the stick's HDMI input.

## Compatibility

The reference installation is a **Hisense 55S7NAU CanvasTV**, firmware **V0000.09.60X.Q0609**, VIDAA 9, with an Ubuntu Server Docker host. The owner has confirmed the tile, remote navigation, Plex, SBS and ABC launching, appearance settings, and repeated Home return from Plex.

Other VIDAA models and firmware remain unverified. Normal power-on, persistence after a TV restart, native Art Gallery behaviour and physical idle/wake behaviour still need testing. See [device evidence](docs/tv-status.md).

## Preview without a TV

Install Node.js 22+ and Python 3.10+, then:

```sh
git clone https://github.com/mcncl/cleanframe-hisense.git
cd cleanframe-hisense
npm ci
npm run dev
```

Open [localhost:4795/home/](http://localhost:4795/home/). Use arrows, Enter and Escape. The preview uses bundled fonts and reports that TV commands require a real installation.

## Install on a home server

Follow the [Hisense setup guide](docs/agent-tv-setup-guide.md). You need Docker Compose, a reachable VIDAA TV, and a locally supplied Sidee-compatible TV client certificate bundle. The bundle and pairing credentials are deliberately excluded from this repository and image. Fresh installation is not yet a one-command process.

After pairing, the service hosts the TV interface at `/home/` and management at `/`. Default shortcuts are Plex, SBS On Demand and ABC iview; install them through the VIDAA App Store. Other installed apps and HDMI inputs can be pinned from All apps.

Automatic Home return is optional and initially disabled. It observes VIDAA Home and opens CleanFrame after a short delay. A glimpse of VIDAA may appear. Turn it off in management or stop the container to return to ordinary TV behaviour. The server must stay running.

## Develop

```sh
npm run check
npx playwright install chromium
CLEANFRAME_PUBLIC_FONTS=1 npm run check:browser
python3.12 -m venv .local/venv
.local/venv/bin/pip install -r hisense/requirements.txt
npm run check:hisense
.local/venv/bin/python -m unittest discover -s hisense -p 'test_*.py'
npm run check:public
```

All these checks are isolated from the TV. Read [development](docs/development.md), [testing](docs/testing.md), [contributing](CONTRIBUTING.md) and [agent guidance](docs/for-agents.md).

## Credits and licence

Based on [nthnclrk/CleanFrame](https://github.com/nthnclrk/CleanFrame), imported from commit `fa537d1892b71d2de2bf94c24cbff3812e9f70d5`. Nathan Clark's original copyright and MIT licence are retained in [LICENSE](LICENSE). Hisense changes are also MIT licensed. Selected [Sidee](https://github.com/Empi9245/Sidee) connection modules retain their own MIT notice and pinned [provenance](hisense/sidee/PROVENANCE.txt).

Fonts, photographs and service marks retain their own terms; see [third-party notices](THIRD_PARTY_NOTICES.md) and [asset sources](docs/asset-sources.md). This project is independent of Hisense, VIDAA and the streaming services.
