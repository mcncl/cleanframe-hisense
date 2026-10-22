"""Navigation controls must not act outside the launcher or send power keys."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from server import APP_ID, Bridge


class NavigationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="cleanframe-navigation-test-")
        self.addCleanup(directory.cleanup)
        environment = patch.dict(os.environ, {"SIDEE_STATE_DIR": directory.name})
        environment.start()
        self.addCleanup(environment.stop)
        self.bridge = Bridge(Path(directory.name), "", "http://example.invalid", demo=True)
        self.bridge.demo = False
        self.bridge._connect = Mock()
        self.bridge._publish = Mock()
        self.bridge.mqtt = SimpleNamespace(topics={"ui": "/remoteapp/tv/ui_service/test/"})

    def test_navigation_only_acts_while_cleanframe_is_foreground(self):
        for state in (None, {"statetype": "remote_launcher"},
                      {"statetype": "app", "appId": "plex"},
                      {"statetype": "app", "appId": "art"},
                      {"statetype": "sourceswitch", "sourceid": "HDMI1"}):
            with self.subTest(state=state):
                self.bridge._record_state(state)
                with self.assertRaisesRegex(ValueError, "Open CleanFrame"):
                    self.bridge.key("down")
        self.bridge._publish.assert_not_called()
        self.bridge._record_state({"statetype": "app", "appId": APP_ID})
        self.assertTrue(self.bridge.key("down")["sent"])
        self.bridge._publish.assert_called_once_with(
            "/remoteapp/tv/remote_service/test/actions/sendkey", "KEY_DOWN")

    def test_power_and_other_non_navigation_commands_are_rejected(self):
        for key in ("power", "home", "menu", "KEY_POWER", ""):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "navigation key"):
                self.bridge.key(key)
        self.bridge._connect.assert_not_called()
        self.bridge._publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
