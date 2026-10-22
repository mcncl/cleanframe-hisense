# Hisense / VIDAA setup

This setup hosts a web-app launcher and uses PIN-paired local TV controls. It preserves the TV firmware and native Home configuration. Read [tested hardware and open checks](tv-status.md) first.

## Prerequisites

- A VIDAA TV reachable from an always-on Docker Compose host on the home network.
- Stable local addresses for the TV and server; reserve them in your router.
- A Sidee-compatible `certs.bin.k` TV client certificate bundle, supplied locally from your own configured Sidee environment. It is not an author signing certificate or the TV's serial number. This repository does not distribute it or provide an automatic certificate-provisioning step. Without it, pairing cannot begin.
- Apps installed through the TV's VIDAA App Store. Fire TV APKs are not VIDAA apps.

Keep the service on a trusted home network. It has local TV controls and does not implement an internet-facing login. The per-request control key and same-origin checks are not a user authentication system.

## Configure and pair

Clone the repository on the Docker host. From the repository root, create a private state directory writable by the container UID/GID:

```sh
mkdir -p .local/hisense/state
chmod 700 .local/hisense/state
install -m 600 /path/to/your/certs.bin.k .local/hisense/state/certs.bin.k
```

Create an ignored `.env` file with your values:

```dotenv
TV_HOST=YOUR_TV_IP
CLEANFRAME_BASE_URL=http://YOUR_SERVER_IP:4795
PUID=1000
PGID=1000
```

The base URL must be reachable by the TV; `localhost` would refer to the TV itself. Use the host user's numeric UID/GID from `id -u` and `id -g`. The default state mount is `.local/hisense/state`; set `CLEANFRAME_DATA_DIR` to an absolute private path if preferred, and prepare that directory instead.

```sh
docker compose --env-file .env -f hisense/compose.yaml build
docker compose --env-file .env -f hisense/compose.yaml run --rm --no-deps cleanframe python hisense/server.py pair
```

Keep the TV on, accept any connection prompt, and enter the displayed PIN at the terminal. Pairing writes `session.json` into the state directory. Do not run a second client with the same saved identity while the service is connected.

```sh
docker compose --env-file .env -f hisense/compose.yaml up -d
```

Open the configured base URL on your computer or phone. Refresh apps and verify that Plex, SBS and ABC are listed if installed. See [the adapter details](hisense.md) for routes and Home timing.

## Add and open the TV tile

The service provides protected `/api/install` and `/api/open` actions. On the management page, open your browser's developer console and run:

```js
async function cleanframeAction(action) {
  const response = await fetch('/api/' + action, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CleanFrame-Key': window.CleanFramePlatform.controlKey
    },
    body: '{}'
  });
  console.log(await response.json());
}
await cleanframeAction('install');
```

Check the TV's apps for **CleanFrame Home**, then open it with the remote. Some firmware omits working custom tiles from its app list. HTTP 202 means the install request was sent but not confirmed; inspect the TV before repeating it. `await cleanframeAction('open')` requests a launch if needed.

Keep tile ID `cleanframehome` and the base URL stable during upgrades. If changing the host/port, update the URL and register the tile once with the new URL. The page stores appearance preferences on the TV for that origin.

## Verify before enabling Home return

Use the Hisense remote to navigate List/Dock, open each required app and enter TV settings. Confirm what appears physically. Then enable automatic Home return in management. Test Plex → Hisense Home → CleanFrame twice, including a quick repeat. VIDAA may appear briefly. Turning Home return off or stopping the container restores ordinary Home behaviour.

The Art control requests the existing Art Gallery app. Verify its actual behaviour separately; a fullscreen photograph in CleanFrame does not reproduce the native power, brightness or motion-sensor features. Confirm normal power-on and tile persistence after restart independently.

## Recovery and upgrades

Disable automatic return at the base URL, or stop only this service:

```sh
docker compose --env-file .env -f hisense/compose.yaml stop cleanframe
```

The original Home configuration remains intact. Remove the tile through the TV's normal app menu if desired. Back up the private state before updates. Retest after TV firmware updates; local protocol behaviour can change.

Rebuild the service after source updates with `docker compose --env-file .env -f hisense/compose.yaml up --build -d cleanframe`. When adding it to an existing Compose project, adjust build context and state paths and use `--no-deps` to avoid restarting unrelated services.
