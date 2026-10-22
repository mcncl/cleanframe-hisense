"""Home-return regressions with an isolated bridge; never contacts a TV."""
import os
from pathlib import Path
import queue
import tempfile
import unittest
from unittest.mock import Mock, patch

from server import Bridge


class HomeReturnTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="cleanframe-home-test-")
        self.addCleanup(directory.cleanup)
        environment = patch.dict(os.environ, {"SIDEE_STATE_DIR": directory.name})
        environment.start()
        self.addCleanup(environment.stop)
        self.bridge = Bridge(Path(directory.name), "", "http://example.invalid", demo=True)
        self.bridge.settings["home_takeover"] = True
        self.bridge.open = Mock()

    def home(self, now=100):
        self.bridge._record_state({"statetype": "remote_launcher"}, now=now)

    def test_home_during_pause_is_retried_without_a_second_broadcast(self):
        self.home()
        self.bridge.pause_home_until = 110
        self.assertFalse(self.bridge._reconcile_home(now=105))
        self.assertTrue(self.bridge._reconcile_home(now=110))
        self.bridge.open.assert_called_once()

    def test_rapid_return_during_cooldown_is_retried(self):
        self.bridge.last_home_launch = 100
        self.home(now=101)
        self.assertFalse(self.bridge._reconcile_home(now=102))
        self.assertTrue(self.bridge._reconcile_home(now=105))
        self.bridge.open.assert_called_once()

    def test_worker_reconciles_after_queue_timeout(self):
        self.home()
        self.bridge.pause_home_until = 102
        clock = [100]

        def no_new_broadcast(timeout):
            clock[0] += 1
            if clock[0] > 103:
                self.bridge.stopping.set()
            raise queue.Empty

        self.bridge.open.side_effect = self.bridge.stopping.set
        with patch("server.time.monotonic", side_effect=lambda: clock[0]), patch.object(self.bridge.events, "get", side_effect=no_new_broadcast):
            self.bridge.watch()
        self.bridge.open.assert_called_once()

    def test_launching_plex_ends_the_explicit_vidaa_home_pause(self):
        self.bridge.pause_home_until = 160
        self.home()
        self.bridge.launch("service.plex")
        self.assertEqual(self.bridge.pause_home_until, 0)
        self.assertIsNone(self.bridge.last_state)
        self.home(now=101)
        self.assertTrue(self.bridge._reconcile_home(now=102))

    def test_newer_app_state_wins_over_a_queued_home_wakeup(self):
        self.home()
        self.bridge._record_state({"statetype": "app", "appId": "plex"}, now=101)
        self.assertFalse(self.bridge._reconcile_home(now=110))
        self.bridge.open.assert_not_called()

    def test_transient_home_does_not_interrupt_art_or_inputs(self):
        for value in ({"statetype": "app", "appId": "art"},
                      {"statetype": "sourceswitch", "sourceid": "HDMI1"},
                      {"statetype": "standby"}):
            with self.subTest(screen=value):
                self.home()
                self.bridge._record_state(value, now=100.3)
                self.assertFalse(self.bridge._reconcile_home(now=102))
        self.bridge.open.assert_not_called()

    def test_home_must_settle_but_duplicates_do_not_delay_it_forever(self):
        self.home()
        self.home(now=100.5)
        self.assertFalse(self.bridge._reconcile_home(now=100.74))
        self.assertTrue(self.bridge._reconcile_home(now=100.75))

    def test_disabled_or_unknown_state_does_not_launch(self):
        self.home()
        self.bridge.settings["home_takeover"] = False
        self.assertFalse(self.bridge._reconcile_home(now=110))
        self.bridge.settings["home_takeover"] = True
        self.bridge._record_state(None)
        self.assertFalse(self.bridge._reconcile_home(now=110))
        self.bridge.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
