# Set up CleanFrame on a VIDAA TV

Use this guide with the [README's agent prompt](../README.md#set-it-up-with-your-ai-agent). It is the setup sequence for both you and your agent. Your agent can handle the commands; you confirm the PIN and what appears on the TV.

## Prerequisites

- A Hisense TV running **VIDAA**. Hisense models running Google TV, Android TV, Fire TV or Roku need a different implementation. Check the TV's own About screen, rather than the About screen of a connected streaming stick.
- A server or NAS that stays on, runs Docker Compose, and can reach the TV on your trusted home network. The tested host is Ubuntu Server. See [tested models and open checks](tv-status.md).
- Access to the server and stable local addresses for the TV and server. Router address reservations are useful. The initial build and pairing-file download need internet access.

No separate Sidee installation, TV app signing, service-menu changes or firmware flashing are needed. The pairing connection uses a client certificate file prepared in step 2. Keep the service on your trusted home network; it has TV controls and no user-login system. Do not expose its port to the internet.

## 1. Prepare the server

For a fresh installation, clone this repository **on the Docker host**:

```sh
git clone https://github.com/mcncl/cleanframe-hisense.git
cd cleanframe-hisense
mkdir -p .local/hisense/state
chmod 700 .local/hisense/state
```

All commands below run from that repository directory. Node.js and host Python are needed only for development, not Docker installation.

Create an ignored `.env` file. Replace the placeholders and use the host user's numeric UID/GID from `id -u` and `id -g`:

```dotenv
TV_HOST=YOUR_TV_IP
CLEANFRAME_BASE_URL=http://YOUR_SERVER_IP:4795
PUID=1000
PGID=1000
```

The TV and server have different addresses. The base URL must be reachable **from the TV**; `localhost` would point back at the TV. Port 4795 must be free on the host. For another port, also set `CLEANFRAME_PORT` and use that port in the base URL.

The default data directory is `.local/hisense/state` in this checkout. It must be writable by the configured UID/GID. Set `CLEANFRAME_DATA_DIR` to an absolute private path if you prefer another location, and prepare that directory instead.

**Existing Compose project:** your agent should adapt the build context, environment and data paths to that project's actual location. Back up the existing configuration first. Use its real Compose file and project directory for later commands, and operate only on the `cleanframe` service. The examples here describe the standalone project.

## 2. Prepare the local pairing file

For a fresh installation using the default data directory, download the certificate bundle from the same pinned Sidee revision as our connection code:

```sh
curl --fail --location --output .local/hisense/state/certs.bin.k \
  https://raw.githubusercontent.com/Empi9245/Sidee/36095890dbf27e3daf1cf9c461bc62f8e7cad175/core/tv-client.bundle
printf '%s  %s\n' \
  955e90447fd7da7680ddcbbf1cc72807f7eaa065f14ff59d057d76811dad6d5c \
  .local/hisense/state/certs.bin.k | sha256sum -c -
chmod 600 .local/hisense/state/certs.bin.k
```

These are Linux commands; on macOS your agent can verify the same SHA-256 using `shasum -a 256`. With a custom data directory, use that location instead. **Continue only after the downloaded file's checksum matches.** The [pinned upstream file](https://github.com/Empi9245/Sidee/blob/36095890dbf27e3daf1cf9c461bc62f8e7cad175/core/tv-client.bundle) is the source; the downloaded bytes must not be printed or committed.

For an existing installation, preserve its working pairing file and private state rather than overwriting them. This encoded file is not an arbitrary PEM certificate: renaming a different certificate will not prepare it correctly. If the source is unavailable or validation fails, stop here and resolve it before requesting a PIN.

## 3. Pair and start the service

Turn the TV on. If a CleanFrame service or another client using this same saved identity is already connected, stop that client before pairing. An upgrade with working pairing does not need a new PIN.

```sh
docker compose --env-file .env -f hisense/compose.yaml config --quiet
docker compose --env-file .env -f hisense/compose.yaml build cleanframe
docker compose --env-file .env -f hisense/compose.yaml run --rm --no-deps cleanframe python hisense/server.py pair
```

Accept any connection prompt on the TV, then enter its PIN at the private terminal prompt. Pairing saves `session.json` in the data directory. Keep that file private.

```sh
docker compose --env-file .env -f hisense/compose.yaml up --no-deps -d cleanframe
```

**Check:** open the configured base URL on your computer or phone. The management page should load. Refresh apps to confirm a current TV response. A healthy container alone does not prove the TV connection works.

## 4. Add CleanFrame to the TV

Have your agent use the running service's [install and open actions](hisense.md#http-actions). Send one install request, then look for **CleanFrame Home** in the TV's apps and open it with the Hisense remote. Your agent can send the open action if needed.

Some firmware omits working custom tiles from its app list. HTTP 202 means installation is unconfirmed; inspect the TV before repeating it. Do not create new tile IDs to work around that response.

**Check:** you can see CleanFrame on the actual TV and navigate with the remote. The management page's **Open CleanFrame** link opens a computer/phone preview; it does not launch the TV app.

## 5. Choose apps and appearance

Install your desired apps through the **VIDAA App Store**, then refresh apps on the management page. The starting Home shortcuts are Plex, SBS On Demand and ABC iview; availability depends on your region and TV.

On the TV, open **All apps → Apps on Home** to add, remove or reorder shortcuts. Refreshing the server's list discovers apps; it does not automatically pin them. Other native apps, such as Stremio Lite, can appear in All apps even when they are absent from the management page's smaller service list. Home holds one to nine apps.

Use the TV's CleanFrame Settings for layout, fonts and wallpaper. Upload a personal photo from the management page, reopen the TV app, then select **Settings → Background → Wallpaper → Your photo**. The management page also sets the idle-fade delay; reopen the TV app after changing it.

VIDAA cannot install Fire TV/Android APKs through this project. An HDMI shortcut can switch to an existing stick. The IPTV Smarters shortcut uses the native app when available; its fallback switches to a Fire TV input and does not open Smarters on the stick.

## 6. Verify, then enable Home return

Open each chosen app and confirm the actual destination. Sign in directly on the TV where required. Once those checks pass, enable **Return to CleanFrame when the TV opens its original Home screen** on the management page.

Test a streaming app → Home on the **Hisense remote** → CleanFrame twice, including a quick repeat. A glimpse of VIDAA can appear. Opening VIDAA Home from CleanFrame pauses return for one minute; launching another app or input ends that pause.

**Check:** app launches and Home return work visibly, and you know how to turn automatic return off. Normal power-on, TV-restart persistence and Art Gallery behaviour are separate checks. A fullscreen wallpaper does not reproduce native Art Gallery's power or sensor features.

## Recovery and updates

Turn automatic Home return off on the management page, or stop only this service:

```sh
docker compose --env-file .env -f hisense/compose.yaml stop cleanframe
```

The TV keeps its original Home configuration. You can remove the tile through its normal app menu. Keep tile ID `cleanframehome` and the server URL stable during updates.

Back up the private data directory and `.env` before updating source or rebuilding:

```sh
docker compose --env-file .env -f hisense/compose.yaml up --no-deps --build -d cleanframe
```

The data directory stores pairing, server settings and uploaded artwork. Appearance and Home order are saved separately in the TV browser for that server URL. A server backup does not automatically restore those TV preferences; changing the URL/port can give the TV a new preference store. Retest after TV firmware updates.

## If something fails

| Symptom | What your agent should check |
| --- | --- |
| Pairing file missing or checksum mismatch | Stop before requesting a PIN. Verify the pinned source, file location and download. |
| Permission denied in the container | Check the data-directory owner and `.env` UID/GID. Preserve private file permissions. |
| No PIN or TV connection timeout | TV power, its actual address, same-network access, VPN/guest-network isolation and access to TCP 36669. |
| Page works on the computer but not the TV | The base URL, published port and host firewall must allow access from the TV. Avoid `localhost` and container-only addresses. |
| Install request is unconfirmed | Check the actual TV apps screen before retrying. The app-list response can omit a working tile. |
| App missing or wrong destination | Check the VIDAA store and fresh All apps catalogue; use returned targets rather than guessing IDs or substituting web players. |
| Home stays on VIDAA | Check automatic return, temporary pause/cooldown and fresh state in the [adapter diagnostics](hisense.md#diagnostics). |
