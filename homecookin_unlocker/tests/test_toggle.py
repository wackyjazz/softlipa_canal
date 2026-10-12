"""Bidirectional eligibility changes must never roll back unrelated progress."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import unlock as core
import desktop_model as model


class ToggleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = (Path(self.directory.name) / "save.dat").resolve()
        self.data = {"chapter": 3, "isMember": True, "items": ["phone"],
                     "triggeredEvents": ["first_time"], "missionDoneRecords": [1, 2],
                     "unknown": {"繁體中文": [None, 1.2, True]}}
        self.raw = core.encode(self.data)
        self.path.write_bytes(self.raw)
        patcher = patch.object(core.sys, "platform", "linux")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_disable_only_changes_eligibility_and_backs_up(self):
        backup = core.disable(self.path, True)
        self.assertEqual(core.decode(self.path.read_bytes()), dict(self.data, isMember=False))
        self.assertEqual((backup / "save.dat").read_bytes(), self.raw)
        manifest = json.loads((backup / "manifest.json").read_text())
        self.assertEqual(manifest["action"], "disable")
        self.assertEqual(manifest["changed_fields"], ["isMember"])
        self.assertEqual(model.inspect_save(self.path).state, "eligible")
        self.assertIn("解除前", model.list_backups(self.path)[0].label)

    def test_repeated_disable_does_not_write_or_backup(self):
        core.disable(self.path, True)
        raw = self.path.read_bytes()
        self.assertIsNone(core.disable(self.path, True))
        self.assertEqual(raw, self.path.read_bytes())
        self.assertEqual(len(model.list_backups(self.path)), 1)

    def test_toggle_preserves_progress_made_after_enable(self):
        core.disable(self.path, True)
        core.unlock(self.path, True)
        progressed = dict(self.data, items=["phone", "cap"], missionDoneRecords=[1, 2, 3])
        self.path.write_bytes(core.encode(progressed))
        backup = core.disable(self.path, True)
        self.assertEqual(core.decode(self.path.read_bytes()), dict(progressed, isMember=False))
        core.restore(self.path, backup, True)
        self.assertEqual(core.decode(self.path.read_bytes()), progressed)
        self.assertEqual(model.inspect_save(self.path).state, "ready")

    def test_disable_refuses_branched_or_completed_saves(self):
        cases = [{"chapter": 5}, {"items": ["home-cookin"]}]
        cases += [{"triggeredEvents": [flag]} for flag in
                  ["time_traveler", "complete", "find_home_cookin", "ask_old_man_home_cookin",
                   "old_man_talk_home_cookin", "ask_home_cookin_repeat_again"]]
        for changes in cases:
            with self.subTest(changes=changes):
                raw = core.encode(dict(self.data, **changes))
                self.path.write_bytes(raw)
                with self.assertRaises(core.UnlockError):
                    core.disable(self.path, True)
                self.assertEqual(self.path.read_bytes(), raw)
        self.assertFalse((self.path.parent / core.BACKUP_FOLDER).exists())

    def test_disable_needs_closed_game_and_same_reviewed_save(self):
        with self.assertRaises(core.UnlockError):
            core.disable(self.path)
        with self.assertRaisesRegex(core.UnlockError, "重新檢查"):
            core.disable(self.path, True, expected_sha256="wrong")
        self.path.with_name("save.dat.tmp").write_bytes(b"pending")
        with self.assertRaises(core.UnlockError):
            core.disable(self.path, True)
        self.assertEqual(self.path.read_bytes(), self.raw)

    def test_membership_requires_boolean(self):
        for value in [1, 0, None, "false"]:
            with self.assertRaises(core.UnlockError):
                core.set_membership(self.path, value, True)
        self.assertEqual(self.path.read_bytes(), self.raw)

    def test_cli_disable(self):
        result = subprocess.run([sys.executable, core.__file__, "disable", "--save", str(self.path),
                                 "--game-closed"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(core.decode(self.path.read_bytes()), dict(self.data, isMember=False))


if __name__ == "__main__":
    unittest.main()
