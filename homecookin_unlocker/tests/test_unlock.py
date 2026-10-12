import gzip
import hmac
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("homecookin_unlock", Path(__file__).parents[1] / "unlock.py")
u = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(u)


def sample(**changes):
    data = {
        "chapter": 4, "displayChapter": 4, "isMember": False,
        "items": ["phone", "cap"], "triggeredEvents": ["first_time", "ask_home_cookin"],
        "missionDoneRecords": [1, 2], "missionOngoingRecords": [4],
        "scene": "record_store", "location": {"x": 200.5, "y": -12},
        "future_unknown_field": {"text": "家常音樂🎵", "values": [None, True, 0, 1.25]},
    }
    data.update(changes)
    return data


def signed_payload(unpacked):
    payload = gzip.compress(unpacked)
    return u.MAGIC + hmac.digest(u.SECRET, payload, "sha256") + payload


class SaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "中文 space"
        self.folder.mkdir()
        self.path = self.folder / "save.dat"
        self.raw = u.encode(sample())
        self.path.write_bytes(self.raw)
        # Unit tests never inspect or modify actual host game processes.
        self.platform = patch.object(u.sys, "platform", "linux")
        self.platform.start()
        self.addCleanup(self.platform.stop)

    def test_unlock_changes_only_member_and_backs_up_exact_bytes(self):
        backup = u.unlock(self.path, True)
        expected = sample(isMember=True)
        self.assertEqual(u.decode(self.path.read_bytes()), expected)
        self.assertEqual((backup / "save.dat").read_bytes(), self.raw)
        manifest = json.loads((backup / "manifest.json").read_text())
        self.assertEqual(manifest["changed_fields"], ["isMember"])
        self.assertEqual(manifest["backup_sha256"], u.digest(self.raw))
        self.assertEqual(manifest["output_sha256"], u.digest(self.path.read_bytes()))
        self.assertFalse(self.path.with_name("save.dat.homecookin.lock").exists())

    def test_repeat_is_noop_with_no_second_backup(self):
        u.unlock(self.path, True)
        before = self.path.read_bytes()
        self.assertIsNone(u.unlock(self.path, True))
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(len(list((self.folder / u.BACKUP_FOLDER).iterdir())), 1)

    def test_restore_exact_bytes_and_back_up_later_progress(self):
        backup = u.unlock(self.path, True)
        progressed = u.encode(sample(chapter=5, isMember=True, items=["phone", "home-cookin"]))
        self.path.write_bytes(progressed)
        undo = u.restore(self.path, backup, True)
        self.assertEqual(self.path.read_bytes(), self.raw)
        self.assertEqual((undo / "save.dat").read_bytes(), progressed)
        self.assertIsNone(u.restore(self.path, backup, True))

    def test_restore_can_replace_damaged_current_save(self):
        backup = u.unlock(self.path, True)
        self.path.write_bytes(b"damaged")
        undo = u.restore(self.path, backup, True)
        self.assertEqual(self.path.read_bytes(), self.raw)
        self.assertEqual((undo / "save.dat").read_bytes(), b"damaged")

    def test_restore_rejects_different_target(self):
        backup = u.unlock(self.path, True)
        other = self.folder / "other.dat"
        other.write_bytes(self.raw)
        with self.assertRaises(u.UnlockError):
            u.restore(other, backup, True)
        self.assertEqual(other.read_bytes(), self.raw)

    def test_restore_rejects_tampered_backup(self):
        backup = u.unlock(self.path, True)
        before = self.path.read_bytes()
        (backup / "save.dat").write_bytes(u.encode(sample(chapter=2)))
        with self.assertRaises(u.UnlockError):
            u.restore(self.path, backup, True)
        self.assertEqual(self.path.read_bytes(), before)

    def test_no_write_without_closed_acknowledgement(self):
        with self.assertRaises(u.UnlockError):
            u.unlock(self.path)
        self.assertEqual(self.path.read_bytes(), self.raw)
        self.assertFalse((self.folder / u.BACKUP_FOLDER).exists())

    def test_game_temp_file_prevents_write(self):
        self.path.with_name("save.dat.tmp").write_bytes(b"pending")
        with self.assertRaises(u.UnlockError):
            u.unlock(self.path, True)
        self.assertEqual(self.path.read_bytes(), self.raw)

    def test_other_tool_lock_prevents_write_and_is_retained(self):
        lock = self.path.with_name("save.dat.homecookin.lock")
        lock.write_text("another tool")
        with self.assertRaises(u.UnlockError):
            u.unlock(self.path, True)
        self.assertEqual(lock.read_text(), "another tool")

    def test_progress_matrix(self):
        for chapter in range(5):
            for events in ([], ["ask_home_cookin"]):
                with self.subTest(chapter=chapter, events=events):
                    self.assertTrue(u.assess(sample(chapter=chapter, triggeredEvents=events))[0])
        for flag in ["time_traveler", "complete", "old_man_talk_home_cookin",
                     "find_home_cookin", "ask_old_man_home_cookin", "ask_home_cookin_repeat_again"]:
            with self.subTest(flag=flag):
                raw = u.encode(sample(triggeredEvents=["ask_home_cookin", flag]))
                self.path.write_bytes(raw)
                with self.assertRaises(u.UnlockError):
                    u.unlock(self.path, True)
                self.assertEqual(self.path.read_bytes(), raw)
        for changes in ({"chapter": 5}, {"chapter": 12}, {"items": ["home-cookin"]}):
            self.assertFalse(u.assess(sample(**changes))[0])
        self.assertFalse((self.folder / u.BACKUP_FOLDER).exists())

    def test_corrupt_and_unknown_formats_rejected(self):
        for raw in [b"", b"{}", b"CLSAVE3\0" + self.raw[8:],
                    self.raw[:20], self.raw[:-1], self.raw[:-1] + bytes([self.raw[-1] ^ 1])]:
            with self.subTest(raw_length=len(raw)):
                with self.assertRaises(u.UnlockError):
                    u.decode(raw)

    def test_gzip_and_json_validation(self):
        for body in [b"[]", b'{"chapter":4,"chapter":4}', b'{"value":NaN}', b"\xff", b"{"]:
            with self.assertRaises(u.UnlockError):
                u.decode(signed_payload(body))
        payload = b"not gzip"
        with self.assertRaises(u.UnlockError):
            u.decode(u.MAGIC + hmac.digest(u.SECRET, payload, "sha256") + payload)

    def test_decompression_limit(self):
        raw = signed_payload(b" " * 2048)
        with patch.object(u, "MAX_SIZE", 1024):
            with self.assertRaises(u.UnlockError):
                u.decode(raw)

    def test_schema_rejects_wrong_types(self):
        for changes in [{"chapter": True}, {"chapter": 13}, {"chapter": -1},
                        {"isMember": "false"}, {"items": [1]}, {"triggeredEvents": {}}]:
            with self.subTest(changes=changes):
                with self.assertRaises(u.UnlockError):
                    u.decode(signed_payload(json.dumps(sample(**changes)).encode()))

    def test_backup_failure_leaves_original_untouched(self):
        with patch.object(u, "make_backup", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                u.unlock(self.path, True)
        self.assertEqual(self.path.read_bytes(), self.raw)

    def test_replace_failure_preserves_original_and_backup(self):
        with patch.object(u.os, "replace", side_effect=OSError("permission denied")):
            with self.assertRaises(u.UnlockError):
                u.unlock(self.path, True)
        self.assertEqual(self.path.read_bytes(), self.raw)
        backup = next((self.folder / u.BACKUP_FOLDER).iterdir())
        self.assertEqual((backup / "save.dat").read_bytes(), self.raw)
        self.assertFalse(list(self.folder.glob(".homecookin-*.tmp")))

    def test_concurrent_save_change_is_not_overwritten(self):
        original_backup = u.make_backup
        newer = u.encode(sample(chapter=3))

        def mutate_after_backup(*args):
            result = original_backup(*args)
            self.path.write_bytes(newer)
            return result

        with patch.object(u, "make_backup", side_effect=mutate_after_backup):
            with self.assertRaises(u.UnlockError):
                u.unlock(self.path, True)
        self.assertEqual(self.path.read_bytes(), newer)

    def test_native_process_guard(self):
        for platform, process in [("win32", "運河 幻の南都"),
                                  ("darwin", "/Applications/運河 幻の南都.app/Contents/MacOS/運河 幻の南都")]:
            with self.subTest(platform=platform), patch.object(u.sys, "platform", platform):
                with patch.object(u.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, process)):
                    with self.assertRaises(u.UnlockError):
                        u.ensure_closed(self.path, True)
                with patch.object(u.subprocess, "run", side_effect=subprocess.TimeoutExpired("ps", 15)):
                    with self.assertRaises(u.UnlockError):
                        u.ensure_closed(self.path, True)

    def test_default_paths(self):
        with patch.object(u.sys, "platform", "win32"), patch.dict(u.os.environ, {"APPDATA": str(self.folder)}):
            self.assertEqual(u.default_save(), self.folder / "canal-legend/gameData/save.dat")
        with patch.object(u.sys, "platform", "darwin"), patch.object(u.Path, "home", return_value=self.folder):
            self.assertEqual(u.default_save(), self.folder / "Library/Application Support/canal-legend/gameData/save.dat")

    def test_cli_status_is_read_only_and_unlock_restore_work(self):
        tool = str(Path(u.__file__))
        status = subprocess.run([sys.executable, tool, "status", "--save", str(self.path)], capture_output=True)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(self.path.read_bytes(), self.raw)
        self.assertEqual(list(self.folder.iterdir()), [self.path])
        result = subprocess.run([sys.executable, tool, "unlock", "--save", str(self.path), "--game-closed"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        backup = next((self.folder / u.BACKUP_FOLDER).iterdir())
        result = subprocess.run([sys.executable, tool, "restore", "--save", str(self.path),
                                 "--backup", str(backup), "--game-closed"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.path.read_bytes(), self.raw)


if __name__ == "__main__":
    unittest.main()
