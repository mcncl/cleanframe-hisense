# Hisense adapter

This independent project adapts CleanFrame's UI, wallpapers, preferences and remote
navigation to VIDAA. Follow the [setup guide](agent-tv-setup-guide.md) for pairing
and installation; this page describes the running adapter.

The service serves the interface and talks to the TV through its PIN-paired local
MQTT/TLS connection. It runs on an Ubuntu Docker host. The TV opens a permanent
web-app tile whose address points to this service; the host must remain running.
It does not replace firmware or write native Home/startup settings.

## Configuration

Use `hisense/compose.yaml`, or add that service to an existing Compose project
with an adjusted build context. Set `TV_HOST` to the TV address and
`CLEANFRAME_BASE_URL` to the HTTP URL reachable from the TV (including port).
Mount a private writable directory at `/data`; it holds `session.json`,
`certs.bin.k`, settings and uploaded photographs. These are excluded from Git
and the image build context. Do not publish the pairing files.

The Python connection modules come from Sidee; their pinned provenance and MIT
licence are in `hisense/sidee/`. The certificate bundle is supplied separately
as local configuration. Initial pairing requires the PIN displayed on the TV.

After starting the service, open its base URL on a computer or phone to choose
the idle interval, upload artwork and refresh installed apps. Uploading generates
all image derivatives on the server; the TV never renders live blur. Reload
CleanFrame and select **Settings → Background → Wallpaper → Your photo** to
apply an uploaded image. Idle mode fades the complete interface into the current
photograph. The first navigation press wakes it, including when OK is held.

## App shortcuts

The initial shortcuts are Plex, SBS On Demand and ABC iview. Optional shortcuts
for IPTV Smarters, 10 and 9Now are available in All apps. Their launch targets
are resolved from the actual TV app list.
Unavailable native apps show an explanation; the adapter does not substitute
arbitrary websites for streaming apps. Install apps from the TV's App Store,
then refresh the list in the web settings.

If IPTV Smarters is missing, its fallback switches to the HDMI input identified
by the TV as Fire TV Stick. **It does not launch Smarters on the stick.** Direct
Fire TV app launching would require a separate, authorized ADB setup. Other
installed apps and HDMI inputs are available in All apps and can be pinned.

The Art Mode control opens the TV's existing Art Gallery application. A sent
request does not prove that the destination has the TV's standby/motion-sensor
behaviour; physical confirmation is required.

## Installation and Home

The protected `/api/install` action registers only `cleanframehome` at
the configured URL and confirms both its ID and URL in a fresh TV app list.
If the TV omits the tile from that list, it returns an unconfirmed result
(HTTP 202). Check the actual TV app screen before retrying: a missing entry is
not proof that installation failed.
`/api/open` sends a launch request. Both use the server's live connection so
they do not interrupt it by opening a second connection with the same identity.
Their request key is delivered by `/api/config.js`; pairing credentials never
leave the server. The service is intended for the home network.

For agent-assisted menu editing, protected `POST /api/key` accepts a `key` of
`up`, `down`, `left`, `right`, `ok` or `back`. It works only while CleanFrame is
the TV's reported foreground app. Read `/api/status` after each key and wait for
a fresh `runtime.observed_at` before using `runtime.location` to choose the next
action. This edits preferences through the same menu as the physical remote.
Power and other keys are rejected. Navigation requires an owner-authorised
device task; announce any app launch or service restart.

Home return is optional and disabled initially. When enabled in web settings,
the service listens for the TV's `remote_launcher` state broadcast and opens
CleanFrame. It does not poll for, or interrupt, streaming/Art Gallery states.
It rechecks the latest received screen after a temporary pause or launch
cooldown, even when the TV does not send another Home broadcast. Repeated
notifications are coalesced, so old Home events cannot override a newer app
or Art Gallery state.
Some firmware may not emit the needed broadcast. Home from Fire TV also depends
on which remote is used and HDMI-CEC behaviour. Verify physical Home and normal
power-on on the actual TV before treating this as the default interface.

Opening VIDAA Home from inside CleanFrame pauses Home return for one minute.
Launching another app or switching an input ends that temporary pause. If you
stay on VIDAA Home, automatic return resumes after the minute expires.
To stop automatic return permanently, turn it off in the web settings or stop
the Compose service. The TV's original Home configuration is retained. The
CleanFrame tile can be removed through the normal TV app menu.

## Checks

Run `npm run check` and `CLEANFRAME_PUBLIC_FONTS=1 npm run check:browser` for the
interface. For the VIDAA integration, create `.local/venv` with Python 3.12,
install `hisense/requirements.txt`, then run `node scripts/check-hisense.mjs`.
The latter always starts an isolated `--demo` server and never contacts a TV.
Home-return regressions run with
`.local/venv/bin/python -m unittest discover -s hisense -p 'test_*.py'`; these
also use an isolated bridge without TV access.
It checks routes, request protection, missing-app/fallback behaviour, preferences,
uploaded image materials and idle/wake behaviour. Screenshots go to ignored
`.local/qa/`. Browser checks cannot verify TV rendering or physical destinations.
