"""Tests for the iCloud shared-album sync.

Everything network-facing is faked: these check the parts that decide what to
download and what to delete, which is where a mistake would either blank the
panel or hammer Apple with needless traffic.
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))

import icloud_album as ia  # noqa: E402


class TestParseToken(unittest.TestCase):
    def test_accepts_the_shapes_apple_hands_out(self):
        for url in ("https://www.icloud.com/sharedalbum/#B0AbcDef123",
                    "https://www.icloud.com/sharedalbum/?#B0AbcDef123",
                    "  https://www.icloud.com/sharedalbum/#B0AbcDef123  ",
                    "B0AbcDef123"):
            self.assertEqual(ia.parse_token(url), "B0AbcDef123")

    def test_rejects_rubbish(self):
        for bad in ("", None, "https://example.com/album", "short", "has spaces here"):
            with self.assertRaises(ia.AlbumError):
                ia.parse_token(bad)


class TestPickDerivative(unittest.TestCase):
    def _photo(self, sizes):
        return {"derivatives": {
            str(i): {"width": w, "height": h, "fileSize": w * h,
                     "checksum": f"ck{w}x{h}"}
            for i, (w, h) in enumerate(sizes)}}

    def test_picks_smallest_that_still_covers_the_panel(self):
        p = self._photo([(342, 342), (1024, 1024), (4032, 3024)])
        self.assertEqual(ia.pick_derivative(p, 64), "ck342x342")

    def test_falls_back_to_largest_when_all_are_too_small(self):
        p = self._photo([(16, 16), (32, 32)])
        self.assertEqual(ia.pick_derivative(p, 64), "ck16x16")

    def test_uses_shortest_edge_not_longest(self):
        # A 200x50 panorama does NOT cover a 64px square: its short edge is 50.
        p = self._photo([(200, 50), (800, 600)])
        self.assertEqual(ia.pick_derivative(p, 64), "ck800x600")

    def test_no_derivatives(self):
        self.assertIsNone(ia.pick_derivative({"derivatives": {}}, 64))
        self.assertIsNone(ia.pick_derivative({}, 64))

    def test_ignores_malformed_entries(self):
        p = {"derivatives": {
            "a": {"width": "oops", "height": 10, "checksum": "x"},
            "b": {"width": 500, "height": 500},              # no checksum
            "c": {"width": 500, "height": 500, "checksum": "good"}}}
        self.assertEqual(ia.pick_derivative(p, 64), "good")


class TestSyncMirroring(unittest.TestCase):
    """The mirror logic: add what's new, remove what's gone, touch nothing else."""

    def setUp(self):
        self.dest = tempfile.mkdtemp()

    def _album(self, guids):
        return [{"photoGuid": g, "derivatives": {
            "1": {"width": 342, "height": 342, "fileSize": 1000, "checksum": f"ck-{g}"}}}
            for g in guids]

    def _existing(self, *guids):
        for g in guids:
            open(os.path.join(self.dest, f"icloud-{g}.png"), "wb").write(b"x")

    def test_dry_run_reports_without_touching_anything(self):
        self._existing("old")
        with mock.patch.object(ia, "fetch_stream",
                               return_value=("base", self._album(["new"]))):
            r = ia.sync("B0token1234", self.dest, dry_run=True, log=lambda *a: None)
        self.assertEqual((r["added"], r["removed"]), (1, 1))
        self.assertTrue(os.path.exists(os.path.join(self.dest, "icloud-old.png")))

    def test_removes_photos_no_longer_in_the_album(self):
        self._existing("gone", "stays")
        with mock.patch.object(ia, "fetch_stream",
                               return_value=("base", self._album(["stays"]))), \
             mock.patch.object(ia, "asset_urls", return_value={}):
            r = ia.sync("B0token1234", self.dest, log=lambda *a: None)
        self.assertEqual(r["removed"], 1)
        self.assertFalse(os.path.exists(os.path.join(self.dest, "icloud-gone.png")))
        self.assertTrue(os.path.exists(os.path.join(self.dest, "icloud-stays.png")))

    def test_leaves_other_peoples_photos_alone(self):
        """Mac-synced and hand-uploaded files must survive an iCloud sync."""
        for name in ("mac-holiday.png", "up-1234-0.png", "notes.txt"):
            open(os.path.join(self.dest, name), "wb").write(b"x")
        with mock.patch.object(ia, "fetch_stream", return_value=("base", [])), \
             mock.patch.object(ia, "asset_urls", return_value={}):
            ia.sync("B0token1234", self.dest, log=lambda *a: None)
        for name in ("mac-holiday.png", "up-1234-0.png", "notes.txt"):
            self.assertTrue(os.path.exists(os.path.join(self.dest, name)), name)

    def test_one_bad_photo_does_not_fail_the_whole_sync(self):
        def half_broken(src, dst, size):
            if "bad" in dst:
                raise OSError("corrupt")
            open(dst, "wb").write(b"png")
        with mock.patch.object(ia, "fetch_stream",
                               return_value=("base", self._album(["good", "bad"]))), \
             mock.patch.object(ia, "asset_urls",
                               return_value={"ck-good": "u1", "ck-bad": "u2"}), \
             mock.patch.object(ia, "_download"), \
             mock.patch.object(ia, "_to_panel", side_effect=half_broken):
            r = ia.sync("B0token1234", self.dest, log=lambda *a: None)
        self.assertEqual(r["added"], 1)
        self.assertTrue(os.path.exists(os.path.join(self.dest, "icloud-good.png")))

    def test_already_present_photos_are_not_redownloaded(self):
        self._existing("a", "b")
        dl = mock.Mock()
        with mock.patch.object(ia, "fetch_stream",
                               return_value=("base", self._album(["a", "b"]))), \
             mock.patch.object(ia, "asset_urls", return_value={}) as urls, \
             mock.patch.object(ia, "_download", dl):
            r = ia.sync("B0token1234", self.dest, log=lambda *a: None)
        self.assertEqual((r["added"], r["removed"]), (0, 0))
        urls.assert_not_called()
        dl.assert_not_called()


class TestStreamErrors(unittest.TestCase):
    def test_missing_photos_key_is_a_clear_error(self):
        with mock.patch.object(ia, "_post", return_value=(200, {}, {"nope": 1})):
            with self.assertRaises(ia.AlbumError) as cm:
                ia.fetch_stream("B0token1234")
        self.assertIn("Public Website", str(cm.exception))

    def test_partition_redirect_is_followed(self):
        calls = []

        def fake_post(base, path, payload):
            calls.append(base)
            if len(calls) == 1:
                return 330, {"X-Apple-MMe-Host": "p42-sharedstreams.icloud.com"}, {}
            return 200, {}, {"photos": []}

        with mock.patch.object(ia, "_post", side_effect=fake_post):
            base, photos = ia.fetch_stream("B0token1234")
        self.assertEqual(len(calls), 2)
        self.assertIn("p42-sharedstreams.icloud.com", base)
        self.assertEqual(photos, [])


if __name__ == "__main__":
    unittest.main()
