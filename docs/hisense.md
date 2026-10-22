# Hisense adapter reference

For installation, follow [the setup guide](agent-tv-setup-guide.md). This page is the technical reference for agents and contributors.

The Python service hosts the interface and uses PIN-paired MQTT/TLS to control the TV. The TV's web-app tile points at this server. The host must stay running. TV firmware and native Home/startup settings are preserved.

## Configuration and storage

| Setting | Meaning |
| --- | --- |
| `TV_HOST` | TV address reachable from the server. |
| `CLEANFRAME_BASE_URL` | Server HTTP URL reachable from the TV, including the published port. Keep it stable for the tile and TV preferences. |
| `CLEANFRAME_PORT` | Optional host port for the example Compose project; default 4795. Update the base URL to match. |
| `PUID`, `PGID` | Container UID/GID; the mounted data directory must be writable by them. Defaults are 1000/1000. |
| `CLEANFRAME_DATA_DIR` | Optional host data path; use an absolute path when overriding it. The example defaults to this checkout's `.local/hisense/state`. |
| `SIDEE_STATE_DIR` | Python's in-container state path, set to `/data` by the Docker image. This is different from the host mount path. |

The data mount holds `certs.bin.k`, `session.json`, `control-key`, cached app/source metadata, server settings and uploaded wallpaper materials. Keep it private and back it up separately from source. The pinned [connection-module provenance](../hisense/sidee/PROVENANCE.txt) and MIT notice remain with the code; the pairing-file source/checksum are in the setup guide.

Home order and appearance live in the TV's localStorage for the server origin. They are not automatically shared with a computer preview or restored from the server's data backup. The example Compose timezone affects server logs; the UI clock uses the TV browser's local time.

## HTTP actions

All paths below are relative to `CLEANFRAME_BASE_URL`. JSON POSTs require `Content-Type: application/json` and `X-CleanFrame-Key`. Read the current key from `window.CleanFramePlatform.controlKey` on the management page, or privately parse `/api/config.js` in an agent's HTTP client. Do not print or commit the key. Browser requests must come from the same host/port as the page.

| Method / path | Body or result | Effect |
| --- | --- | --- |
| `GET /health` | Server health and demo flag | Does not establish TV connectivity. |
| `GET /api/status` | Settings, services, TV state, runtime and Home-return diagnostics | Read-only. |
| `GET /api/apps` | Catalogue with `appId`, `name`, `brand`, `icon` | Use these returned targets for launching and pinning. |
| `GET /api/config.js` | Browser configuration and local control key | Pairing tokens never leave the server. |
| `POST /api/refresh` | `{}` | Queries the TV for installed apps/sources. |
| `POST /api/install` | `{}` | Registers only `cleanframehome` at the configured URL. Announce first. |
| `POST /api/open` | `{}` | Requests CleanFrame on the TV. Announce first. |
| `POST /api/launch` | `{"id":"TARGET_FROM_CATALOGUE"}` | Launches an app or input. Announce first. |
| `POST /api/key` | `{"key":"down"}` | Navigation in foreground CleanFrame only. |
| `POST /api/settings` | `{"idle_seconds":120,"home_takeover":false}` | Saves server settings; omitted fields keep their current values. |
| `POST /api/wallpaper` | Raw image bytes and image content type | Prepares the personal wallpaper on the server. |

For example, on the management page's **computer browser** console:

```js
async function cleanframeAction(action, body = {}) {
  const response = await fetch('/api/' + action, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CleanFrame-Key': window.CleanFramePlatform.controlKey
    },
    body: JSON.stringify(body)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  return {status: response.status, result};
}
await cleanframeAction('install');
```

Inspect the TV's apps before retrying installation. HTTP 202 means the request was sent but the tile was not found in app-list readback. A working tile can be omitted by firmware; this is not proof of failure. `await cleanframeAction('open')` sends a separate launch request. Other device errors return an explanation, generally HTTP 400 or 503. For HTTP 403, reload the management page and check the key and browser origin.

The request key and same-origin checks are local control protections, not a user-authentication system. Keep this service on a trusted home network.

## Apps and artwork

Initial Home shortcuts are Plex, SBS On Demand and ABC iview. The service also recognises IPTV Smarters, 10 and 9Now by installed-app names. Other installed apps, including Stremio Lite, appear as native targets. Never reuse a native ID from the reference TV as a universal ID.

The management page shows the curated service list; **All apps** also includes other native apps and HDMI inputs. Discovery does not pin apps. Use **All apps → Apps on Home** to edit the TV's menu. Home holds one to nine apps.

Unavailable native apps show an explanation rather than a guessed web player. If IPTV Smarters is absent, its fallback switches to the HDMI source identified as Fire TV Stick. It does not open Smarters on the stick. The Art control launches the existing Art Gallery app when found; it does not send a power-key fallback or establish sensor/standby behaviour.

Wallpaper uploads are limited to 20 MB. The management page accepts JPEG, PNG and WebP. The server prepares a 1920 × 1080 crop and registered materials; the TV performs no live blur. Reopen the TV app and choose **Settings → Background → Wallpaper → Your photo**. Idle delay options are 0 (disabled), 30, 60, 120, 300 and 600 seconds. Reopen the TV app after changing that delay.

## Diagnostics

`/api/status` reports:

- `paired`: saved pairing state exists; this alone does not prove a live connection.
- `last_state`: latest TV-reported screen. Missing/stale data is not a visible-screen observation.
- `home_return`: connection, defer reason, pause/cooldown and state age.
- `runtime`: TV browser readiness, viewport, errors, focus and timestamp.
- `runtime.preferences`: saved appearance, Home order and app records. This read-only snapshot can reproduce the owner's look in a browser capture. It is not direct TV pixel access.

Runtime reports normally come only from the configured TV address, through `POST /api/runtime`. Computer previews do not overwrite the live TV report. After a restart, wait for the TV page to report again; closing/reopening its tile may be necessary. A launch of an already active tile may not reload it. Treat runtime snapshots and app names as private diagnostic data.

For agent-assisted editing, `/api/key` accepts only `up`, `down`, `left`, `right`, `ok` and `back`. Read status after each key and wait for a newer `runtime.observed_at` before choosing the next action. Power and other keys are rejected, and the TV must report `cleanframehome` as foreground. This uses the same menu actions and preference writes as the physical remote.

## Home return and recovery

Automatic return is initially **off**; idle fade defaults to **120 seconds**. When enabled, the service observes `remote_launcher` and opens CleanFrame after Home settles. A five-second launch cooldown avoids repeated launches. It rechecks the latest received state when a cooldown or pause expires, without needing another broadcast. A newer app/input/Art state supersedes an older Home event.

The CleanFrame **VIDAA Home** action pauses return for one minute. Launching an app or switching input ends that pause. To disable return permanently, turn it off on the management page or stop the Compose service. Native Home configuration is unchanged.

Firmware can omit the required broadcasts. Home on a Fire TV remote and HDMI-CEC may behave differently from the Hisense remote. Native startup, Art Gallery and restart persistence need separate physical tests; see [TV evidence](tv-status.md).

Use [testing](testing.md) for isolated checks. They never contact a TV.
