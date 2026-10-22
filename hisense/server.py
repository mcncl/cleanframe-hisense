"""CleanFrame's local VIDAA adapter. Pairing state stays in the data volume."""
from __future__ import annotations

import argparse
import io
import json
import logging
import mimetypes
import os
from pathlib import Path
import queue
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from sidee import client, protocol

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
APP_ID = "cleanframehome"
APP_NAME = "CleanFrame Home"
DEFAULT_HOME = ("plex", "sbs", "abciview")
SERVICES = [
    ("plex", "Plex", ["plex"]),
    ("smarters", "IPTV Smarters", ["iptv smarters", "smarters pro", "smarters player"]),
    ("sbs", "SBS On Demand", ["sbs on demand", "sbs"]),
    ("ten", "10", ["10", "10 play", "10play", "tenplay"]),
    ("nine", "9Now", ["9now", "9 now"]),
    ("abciview", "ABC iview", ["abc iview", "iview"]),
]
LOG = logging.getLogger("cleanframe")


class Bridge:
    def __init__(self, state: Path, host: str, base_url: str, demo=False):
        self.state = state
        self.host = host
        self.base_url = base_url.rstrip("/")
        self.demo = demo
        self.lock = threading.RLock()
        self.mqtt = None
        self.apps = []
        self.sources = []
        self.updated = 0.0
        self.events = queue.Queue(maxsize=1)
        self.state_lock = threading.Lock()
        self.last_state = None
        self.last_state_at = None
        self.home_since = None
        self.home_decision = None
        self.runtime = None
        self.pause_home_until = 0.0
        self.last_home_launch = 0.0
        self.stopping = threading.Event()
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        key_path = state / "control-key"
        try:
            self.control_key = key_path.read_text().strip()
            if len(self.control_key) < 32:
                raise ValueError("Invalid control key")
        except (OSError, ValueError):
            self.control_key = secrets.token_urlsafe(32)
            key_path.write_text(self.control_key)
            key_path.chmod(0o600)
        os.environ["SIDEE_STATE_DIR"] = str(state)
        self.settings = {"idle_seconds": 120, "home_takeover": False}
        try:
            saved = json.loads((state / "settings.json").read_text())
            self.settings.update({k: saved[k] for k in self.settings if k in saved})
        except (OSError, ValueError):
            pass
        if demo:
            self.apps = [
                {"appId": "demo." + key, "name": name, "url": "https://example.invalid/" + key, "storeType": 99}
                for key, name, _ in SERVICES if key != "smarters"
            ] + [{"appId": "demo.art", "name": "Art Gallery", "url": "https://example.invalid/art", "storeType": 99}]
            self.sources = [{"sourceid": "HDMI1", "sourcename": "HDMI1", "displayname2": "Fire TV Stick"}]
        else:
            try:
                cached = json.loads((state / "catalogue.json").read_text())
                self.apps, self.sources = cached["apps"], cached["sources"]
            except (OSError, ValueError, KeyError):
                pass

    def _connect(self):
        if self.demo:
            return
        if self.mqtt and self.mqtt.client.is_connected():
            return
        if self.mqtt:
            self.mqtt.stop()
        # A stale Home state from a previous connection must not interrupt an
        # app or Art Gallery after the TV wakes. Wait for a fresh broadcast.
        self._record_state(None)
        session = client._ensure_ready(client.Session.load())
        session.host = self.host
        self.mqtt = client._saved_connection(session, None if session.tokenless else session.access_token)
        if self.mqtt.start() != 0:
            self.mqtt.stop()
            self.mqtt = None
            raise ConnectionError("The TV did not accept the saved pairing. It may need a new PIN.")
        original = self.mqtt.client.on_message

        def receive(c, u, message):
            original(c, u, message)
            if message.topic.endswith("ui_service/state"):
                try:
                    value = json.loads(message.payload)
                    if isinstance(value, dict):
                        self._record_state(value)
                except ValueError:
                    pass

        self.mqtt.client.on_message = receive
        topics = self.mqtt.topics
        self.mqtt.subscribe([
            topics["applist_reply"],
            topics["mobile"] + "ui_service/data/sourcelist",
            topics["mobile"] + "ui_service/state",
            topics["broadcast"] + "ui_service/state",
        ])
        time.sleep(0.3)

    def _publish(self, topic, payload):
        if self.demo:
            return
        result = self.mqtt.client.publish(topic, payload)
        result.wait_for_publish(timeout=4)
        if not result.is_published():
            raise TimeoutError("The TV control request could not be sent.")

    def _query(self, action, suffix, payload="0", timeout=8):
        self._connect()
        if len(self.mqtt.messages) > 1000:
            self.mqtt.messages = self.mqtt.messages[-100:]
        since = len(self.mqtt.messages)
        self._publish(self.mqtt.topics["ui"] + "actions/" + action, payload)
        raw = self.mqtt.wait_for(suffix, timeout, since)
        if raw is None:
            raise TimeoutError("The TV did not answer the " + action + " request.")
        return json.loads(raw)

    def refresh(self):
        with self.lock:
            if not self.demo:
                apps = self._query("applist", "ui_service/data/applist")
                if not isinstance(apps, list):
                    raise ValueError("The TV returned an invalid app list.")
                self.apps = apps
                try:
                    sources = self._query("sourcelist", "ui_service/data/sourcelist", timeout=4)
                    if isinstance(sources, list):
                        self.sources = sources
                except TimeoutError:
                    LOG.warning("Input discovery did not respond; keeping the previous input list.")
            self.updated = time.time()
            if not self.demo:
                (self.state / "catalogue.json").write_text(json.dumps({"apps": self.apps, "sources": self.sources}))
            return self.status()

    def matching(self, names):
        return next((app for app in self.apps if str(app.get("name", "")).strip().casefold() in names), None)

    def firestick(self):
        return next((source for source in self.sources
                     if "fire" in (source.get("displayname2", "") + source.get("displayname", "")).casefold()), None)

    def services(self):
        return [{"id": key, "name": name, "available": self.matching(aliases) is not None,
                 "fallback": key == "smarters" and self.matching(aliases) is None and self.firestick() is not None}
                for key, name, aliases in SERVICES]

    def status(self):
        try:
            verification = json.loads((self.state / "verification.json").read_text())
        except (OSError, ValueError):
            verification = {}
        return {"settings": self.settings, "services": self.services(), "updated": self.updated,
                "paired": self.demo or (self.state / "session.json").is_file(),
                "last_state": self.last_state,
                "runtime": self.runtime,
                "home_takeover_verified": verification.get("home_return", False),
                "verification": verification,
                "home_return": self.home_status()}

    def _record_state(self, value, now=None):
        now = time.monotonic() if now is None else now
        with self.state_lock:
            was_home = (self.last_state or {}).get("statetype") == "remote_launcher"
            is_home = (value or {}).get("statetype") == "remote_launcher"
            self.last_state = value
            self.last_state_at = now if value is not None else None
            if is_home and not was_home:
                self.home_since = now
            elif not is_home:
                self.home_since = None
        try:
            self.events.put_nowait(None)
        except queue.Full:
            pass  # Wakeups are coalesced; the state itself is always current.

    def _home_reason(self, now):
        if not self.settings["home_takeover"]:
            return "disabled"
        if self.last_state is None:
            return "waiting_for_tv_state"
        if self.last_state.get("statetype") != "remote_launcher":
            return "another_screen"
        if now < self.pause_home_until:
            return "temporary_pause"
        if self.home_since is None or now < self.home_since + .75:
            return "waiting_for_home_to_settle"
        if now < self.last_home_launch + 5:
            return "launch_cooldown"
        return "ready"

    def home_status(self):
        now = time.monotonic()
        with self.state_lock:
            return {"reason": self._home_reason(now),
                    "pause_seconds": round(max(0, self.pause_home_until - now), 1),
                    "cooldown_seconds": round(max(0, self.last_home_launch + 5 - now), 1),
                    "state_age_seconds": round(max(0, now - self.last_state_at), 1) if self.last_state_at is not None else None,
                    "connected": bool(self.mqtt and self.mqtt.client.is_connected())}

    def _reconcile_home(self, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            with self.state_lock:
                reason = self._home_reason(now)
                if reason != self.home_decision:
                    if reason in ("temporary_pause", "launch_cooldown"):
                        LOG.info("Home return deferred: %s; it will retry when eligible.", reason)
                    self.home_decision = reason
                if reason != "ready":
                    return False
                self.last_home_launch = now
            LOG.info("TV is on its original Home; returning to CleanFrame.")
            self.open()
            return True

    def catalogue(self):
        result = [{"appId": "service." + key, "name": name,
                   "brand": key if key in ("sbs", "abciview") else "", "icon": ""}
                  for key, name, _ in SERVICES]
        for app in self.apps:
            required = any(self.matching(aliases) is app for _, _, aliases in SERVICES)
            if app.get("appId") != APP_ID and not required:
                result.append({"appId": "native." + str(app["appId"]), "name": app["name"], "brand": "", "icon": ""})
        for source in self.sources:
            if str(source.get("sourceid", "")).startswith("HDMI"):
                label = source.get("displayname2") or source.get("displayname") or source["sourceid"]
                result.append({"appId": "input." + source["sourceid"], "name": label, "brand": "", "icon": ""})
        return result

    def _launch_native(self, app):
        self._connect()
        self.pause_home_until = 0.0
        # Do not treat the previous screen as current while an app is opening.
        self._record_state(None)
        if self.demo:
            return
        value = {k: app[k] for k in ("appId", "name", "url", "storeType", "urlType") if k in app}
        value.setdefault("urlType", 37)
        self._publish(self.mqtt.topics["ui"] + "actions/launchapp", json.dumps(value))

    def _input(self, source):
        self._connect()
        self.pause_home_until = 0.0
        self._record_state(None)
        if not self.demo:
            self._publish(self.mqtt.topics["ui"] + "actions/changesource", json.dumps({k: source[k] for k in ("sourceid", "sourcename") if k in source}))

    def launch(self, target):
        with self.lock:
            if target.startswith("service."):
                key = target[8:]
                service = next((s for s in SERVICES if s[0] == key), None)
                if service:
                    app = self.matching(service[2])
                    if app:
                        self._launch_native(app)
                        return {"sent": True, "destination": service[1]}
                    if key == "smarters" and self.firestick():
                        self._input(self.firestick())
                        return {"sent": True, "destination": "Fire TV Stick", "note": "Select IPTV Smarters on your Fire TV Stick."}
                    raise ValueError(service[1] + " is not in the TV’s app list. Install it from the TV’s App Store, then refresh apps in CleanFrame’s web settings.")
            elif target.startswith("native."):
                app = next((a for a in self.apps if str(a.get("appId")) == target[7:] and a.get("appId") != APP_ID), None)
                if app:
                    self._launch_native(app)
                    return {"sent": True, "destination": app["name"]}
            elif target.startswith("input."):
                source = next((s for s in self.sources if s.get("sourceid") == target[6:]), None)
                if source:
                    self._input(source)
                    return {"sent": True, "destination": source.get("displayname2") or source["sourceid"]}
            elif target == "control.art":
                app = self.matching(["art gallery"])
                if app:
                    self._launch_native(app)
                    return {"sent": True, "destination": "Art Gallery"}
            elif target in ("control.home", "control.settings"):
                self._connect()
                if target == "control.home":
                    self.pause_home_until = time.monotonic() + 60
                if not self.demo:
                    remote = self.mqtt.topics["ui"].replace("/ui_service/", "/remote_service/")
                    self._publish(remote + "actions/sendkey", "KEY_HOME" if target == "control.home" else "KEY_MENU")
                return {"sent": True, "destination": "TV Home" if target.endswith("home") else "TV menu"}
            raise ValueError("This shortcut is unavailable. Refresh the app list and try again.")

    def key(self, key):
        keys = {"up": "KEY_UP", "down": "KEY_DOWN", "left": "KEY_LEFT",
                "right": "KEY_RIGHT", "ok": "KEY_OK", "back": "KEY_RETURNS"}
        if key not in keys:
            raise ValueError("Choose a navigation key: up, down, left, right, ok or back.")
        with self.lock:
            self._connect()
            if not self.demo:
                if (self.last_state or {}).get("appId") != APP_ID:
                    raise ValueError("Open CleanFrame before sending navigation keys.")
                remote = self.mqtt.topics["ui"].replace("/ui_service/", "/remote_service/")
                self._publish(remote + "actions/sendkey", keys[key])
            return {"sent": True}

    def install(self):
        with self.lock:
            self._connect()
            url = self.base_url + "/home/"
            if self.demo:
                return {"installed": True, "url": url}
            payload = protocol.install_payload(APP_ID, APP_NAME, url, self.base_url + "/home/icon.png")
            self._publish(self.mqtt.topics["ui"] + "actions/uievent", payload)
            for _ in range(3):
                time.sleep(3)
                apps = self._query("applist", "ui_service/data/applist")
                if any(client.tile_matches_request(a, APP_ID, url) for a in apps):
                    self.apps = apps
                    return {"installed": True, "url": url}
            return {"installed": None, "confirmation": "not_in_app_list", "url": url,
                    "message": "Install request sent, but the tile is absent from the TV’s app list. Check the TV’s apps before retrying: some firmware omits working custom tiles from this list."}

    def open(self):
        with self.lock:
            self._launch_native({"appId": APP_ID, "name": APP_NAME, "url": self.base_url + "/home/", "storeType": 99, "urlType": 37})

    def save_settings(self, value):
        seconds = value.get("idle_seconds", self.settings["idle_seconds"])
        takeover = value.get("home_takeover", self.settings["home_takeover"])
        if type(seconds) is not int or seconds not in (0, 30, 60, 120, 300, 600) or type(takeover) is not bool:
            raise ValueError("Choose a supported idle interval and Home setting.")
        self.settings = {"idle_seconds": seconds, "home_takeover": takeover}
        temp = self.state / "settings.tmp"
        temp.write_text(json.dumps(self.settings)); temp.replace(self.state / "settings.json")
        try:
            self.events.put_nowait(None)
        except queue.Full:
            pass
        return self.settings

    def watch(self):
        while not self.stopping.is_set():
            try:
                with self.lock:
                    self._connect()
                try:
                    self.events.get(timeout=.5)
                except queue.Empty:
                    pass
                # Re-evaluate even without another TV packet: a Home event
                # during the cooldown/pause remains pending until it expires.
                self._reconcile_home()
            except Exception as error:
                LOG.warning("TV connection waiting: %s", error)
                self.stopping.wait(10)


def prepare_wallpaper(state: Path, content: bytes):
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    Image.MAX_IMAGE_PIXELS = 40_000_000
    with Image.open(io.BytesIO(content)) as source:
        image = ImageOps.fit(ImageOps.exif_transpose(source).convert("RGB"), (1920, 1080), method=Image.Resampling.LANCZOS)
    folder = state / "wallpaper"
    folder.mkdir(exist_ok=True)
    # All derivatives use the identical registered crop; no live blur on the TV.
    images = {"personal.jpg": image, "personal-thumb.jpg": image.resize((320, 180))}
    for suffix, radius in (("field-blur", 28), ("field-frost", 42), ("field-clear", 2), ("study-soft", 14)):
        material = image.filter(ImageFilter.GaussianBlur(radius))
        if suffix == "study-soft":
            material = ImageEnhance.Brightness(material).enhance(.60)
        images["personal-" + suffix + ".jpg"] = material
    images["personal-panel.jpg"] = images["personal-field-frost.jpg"].resize((960, 540))
    for name, value in images.items():
        value.save(folder / name, "JPEG", quality=90)


class Handler(BaseHTTPRequestHandler):
    server_version = "CleanFrame/1.0"

    @property
    def bridge(self):
        return self.server.bridge

    def reply(self, body, content_type="application/json", status=200):
        if not isinstance(body, bytes):
            body = (json.dumps(body) if content_type == "application/json" else body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        try:
            if path == "/health":
                return self.reply({"ok": True, "demo": self.bridge.demo})
            if path == "/api/config.js":
                apps = [{"id": key, "name": name, "appId": "service." + key,
                         "mark": key in ("sbs", "abciview")} for key, name, _ in SERVICES if key in DEFAULT_HOME]
                data = {"name": "Hisense", "homeName": "VIDAA Home", "apps": apps,
                        "controlKey": self.bridge.control_key, "idleSeconds": self.bridge.settings["idle_seconds"]}
                return self.reply("window.CleanFramePlatform=" + json.dumps(data) + ";", "application/javascript")
            if path == "/api/apps":
                return self.reply({"apps": self.bridge.catalogue()})
            if path == "/api/status":
                return self.reply(self.bridge.status())
            if path in ("/", "/manage"):
                return self.reply((HERE / "manage.html").read_bytes(), "text/html; charset=utf-8")
            if path in ("/home", "/home/", "/home/index.html"):
                value = (ROOT / "app/index.html").read_text()
                value = value.replace('<script src="platform.js"></script>', '<script src="/api/config.js"></script><script src="/hisense/runtime.js"></script>')
                value = value.replace('</head>', '<link rel="stylesheet" href="/hisense/ambient.css"></head>')
                value = value.replace('</body>', '<script src="/hisense/ambient.js"></script></body>')
                if (self.bridge.state / "wallpaper/personal.jpg").is_file():
                    custom = {"id": "personal", "name": "Your photo", "tone": "dark", "ut": {"tr": "light", "br": "light"}, "frostVeil": .2}
                    value = value.replace('<script src="main.js">', '<script>window.CleanFrameWallpapers.push(' + json.dumps(custom) + ');</script><script src="main.js">')
                return self.reply(value, "text/html; charset=utf-8")
            if path.startswith("/hisense/") and path.split("/")[-1] in ("ambient.js", "ambient.css", "runtime.js"):
                file = HERE / path.split("/")[-1]
            elif path.startswith("/home/"):
                file = (ROOT / "app" / path[6:]).resolve()
                if ROOT / "app" not in file.parents:
                    return self.reply({"error": "Not found"}, status=404)
                if file.name.startswith("personal") and (self.bridge.state / "wallpaper" / file.name).is_file():
                    file = self.bridge.state / "wallpaper" / file.name
            else:
                return self.reply({"error": "Not found"}, status=404)
            if not file.is_file():
                return self.reply({"error": "Not found"}, status=404)
            return self.reply(file.read_bytes(), mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        except Exception as error:
            LOG.exception("GET failed")
            self.reply({"error": str(error)}, status=503)

    def do_POST(self):
        origin = self.headers.get("Origin")
        path = urlsplit(self.path).path
        supplied_key = self.headers.get("X-CleanFrame-Key", "")
        # A running TV page can survive a service upgrade. Allow that paired
        # TV's existing page to keep launching apps with its previous page key.
        existing_tv_page = (self.client_address[0] == self.bridge.host and bool(supplied_key)
                            and path in ("/api/launch", "/api/runtime"))
        if (origin and urlsplit(origin).netloc != self.headers.get("Host")) or not (existing_tv_page or secrets.compare_digest(supplied_key, self.bridge.control_key)):
            return self.reply({"error": "Reload CleanFrame before using these controls."}, status=403)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 0 or size > 20_000_000:
                return self.reply({"error": "Choose an image smaller than 20 MB."}, status=413)
            content = self.rfile.read(size)
            path = urlsplit(self.path).path
            if path == "/api/wallpaper":
                prepare_wallpaper(self.bridge.state, content)
                return self.reply({"saved": True})
            value = json.loads(content or b"{}")
            if not isinstance(value, dict):
                raise ValueError("Expected an object.")
            if path == "/api/launch":
                return self.reply(self.bridge.launch(str(value.get("id", ""))))
            if path == "/api/key":
                return self.reply(self.bridge.key(str(value.get("key", ""))))
            if path == "/api/settings":
                return self.reply(self.bridge.save_settings(value))
            if path == "/api/refresh":
                return self.reply(self.bridge.refresh())
            if path == "/api/runtime":
                if self.client_address[0] == self.bridge.host or self.bridge.demo:
                    self.bridge.runtime = {key: value[key] for key in ("ready", "width", "height", "engine", "errors", "location") if key in value}
                    self.bridge.runtime["observed_at"] = time.time()
                return self.reply({"received": True})
            if path == "/api/install":
                result = self.bridge.install()
                return self.reply(result, status=202 if result.get("installed") is None else 200)
            if path == "/api/open":
                self.bridge.open()
                return self.reply({"sent": True})
            return self.reply({"error": "Not found"}, status=404)
        except ValueError as error:
            self.reply({"error": str(error)}, status=400)
        except Exception as error:
            LOG.warning("TV action failed: %s", error)
            self.reply({"error": str(error)}, status=503)

    def log_message(self, format, *args):
        if args and str(args[0]).startswith(("GET /health", "GET /home/assets/", "POST /api/runtime")):
            return
        LOG.info("%s %s", self.client_address[0], format % args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["serve", "pair", "install", "open", "status"])
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4795)
    parser.add_argument("--demo", action="store_true", help="Isolated browser checks; never connect to a TV")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    state = Path(os.environ.get("SIDEE_STATE_DIR", str(ROOT / ".local/hisense/state"))).resolve()
    bridge = Bridge(state, os.environ.get("TV_HOST", ""), os.environ.get("CLEANFRAME_BASE_URL", "http://localhost:4795"), args.demo)
    if args.command == "pair":
        import getpass
        client.pair(bridge.host, lambda: getpass.getpass("PIN shown on your TV: "))
        print("Pairing confirmed.")
        return
    if not args.demo and not bridge.host:
        parser.error("Set TV_HOST to your TV's local address.")
    try:
        try:
            bridge.refresh()
        except Exception:
            if args.command != "serve":
                raise
            LOG.warning("TV unavailable at startup; serving the saved catalogue until it reconnects.")
        if args.command == "install":
            print(json.dumps(bridge.install()))
        elif args.command == "open":
            bridge.open()
            print("Launch request sent. Confirm the visible screen on the TV.")
        elif args.command == "status":
            print(json.dumps(bridge.status(), indent=2))
        else:
            server = ThreadingHTTPServer((args.bind, args.port), Handler)
            server.bridge = bridge
            if not args.demo:
                threading.Thread(target=bridge.watch, daemon=True).start()
            LOG.info("CleanFrame listening on %s:%s", args.bind, server.server_port)
            server.serve_forever()
    finally:
        bridge.stopping.set()
        if bridge.mqtt:
            bridge.mqtt.stop()


if __name__ == "__main__":
    main()
