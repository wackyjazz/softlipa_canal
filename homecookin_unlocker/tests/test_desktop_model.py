import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import desktop_model as model
import unlock as core


def sample(**kw):
    return dict({"chapter": 3, "isMember": False, "items": [], "triggeredEvents": []}, **kw)


class DesktopModelTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = (Path(self.directory.name) / "save.dat").resolve()
        self.path.write_bytes(core.encode(sample()))
        patcher = patch.object(core.sys, "platform", "linux")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_player_states(self):
        cases = [(sample(), "eligible"), (sample(isMember=True), "ready"),
                 (sample(chapter=5), "blocked"),
                 (sample(triggeredEvents=["time_traveler"]), "completed")]
        for data, expected in cases:
            self.path.write_bytes(core.encode(data))
            view = model.inspect_save(self.path)
            self.assertEqual(view.state, expected)
            self.assertEqual(view.sha256, core.digest(self.path.read_bytes()))
        self.path.write_bytes(b"broken")
        self.assertEqual(model.inspect_save(self.path).state, "invalid")
        self.path.unlink()
        self.assertEqual(model.inspect_save(self.path).state, "missing")

    def test_backup_list_excludes_wrong_target_and_tampered_files(self):
        backup = core.unlock(self.path, True)
        listing = model.list_backups(self.path)
        self.assertEqual(len(listing), 1)
        self.assertEqual(listing[0].folder, backup)
        self.assertIn("第 3 章", listing[0].label)
        metadata_path = backup / "manifest.json"
        original = metadata_path.read_bytes()
        metadata = json.loads(original)
        metadata["target"] = str(self.path.parent / "other.dat")
        metadata_path.write_text(json.dumps(metadata))
        self.assertEqual(model.list_backups(self.path), [])
        metadata_path.write_bytes(original)
        (backup / "save.dat").write_bytes(b"damaged")
        self.assertEqual(model.list_backups(self.path), [])

    def test_unlock_requires_same_snapshot_user_reviewed(self):
        view = model.inspect_save(self.path)
        newer = core.encode(sample(chapter=4))
        self.path.write_bytes(newer)
        with self.assertRaisesRegex(core.UnlockError, "重新檢查"):
            core.unlock(self.path, True, expected_sha256=view.sha256)
        self.assertEqual(self.path.read_bytes(), newer)
        self.assertFalse((self.path.parent / core.BACKUP_FOLDER).exists())

    def test_restore_requires_same_snapshot_user_reviewed(self):
        backup = core.unlock(self.path, True)
        view = model.inspect_save(self.path)
        newer = core.encode(sample(chapter=4, isMember=True))
        self.path.write_bytes(newer)
        with self.assertRaisesRegex(core.UnlockError, "重新檢查"):
            core.restore(self.path, backup, True, expected_sha256=view.sha256)
        self.assertEqual(self.path.read_bytes(), newer)


if __name__ == "__main__":
    unittest.main()
