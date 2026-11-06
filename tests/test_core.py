import tempfile
import unittest
from pathlib import Path
from core.policy import Policy, Operation, PolicyDenied
from core.safe_files import resolve_inside, write_text_atomic, read_text, UnsafePathError
from core.backup import BackupManager

class CoreTests(unittest.TestCase):
    def test_workspace_write_read(self):
        with tempfile.TemporaryDirectory() as root:
            write_text_atomic(root, "src/hello.py", "print('سلام')")
            self.assertIn("سلام", read_text(root, "src/hello.py"))

    def test_reject_parent_escape(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(UnsafePathError):
                resolve_inside(root, "../outside.txt")

    def test_policy_denies_unlisted_tool(self):
        policy = Policy(allowed_tools=["read_file"])
        with self.assertRaises(PolicyDenied):
            policy.check(Operation("delete_file", "external_or_destructive"), confirmed=True)

    def test_destructive_needs_confirmation(self):
        policy = Policy(allowed_tools=["delete_file"], allow_writes=True)
        with self.assertRaises(PolicyDenied):
            policy.check(Operation("delete_file", "external_or_destructive"))
        self.assertTrue(policy.check(Operation("delete_file", "external_or_destructive"), confirmed=True))

    def test_restore_rejects_snapshot_outside_backup_root(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root) / "work"
            backups = Path(root) / "backups"
            workspace.mkdir()
            outside = Path(root) / "outside.snapshot"
            outside.write_text("untrusted", encoding="utf-8")
            manager = BackupManager(workspace, backups)
            import hashlib
            digest = hashlib.sha256(b"untrusted").hexdigest()
            with self.assertRaises(ValueError):
                manager.restore(str(outside), "target.txt", digest)

    def test_snapshot_and_restore(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root) / "work"
            backups = Path(root) / "backups"
            workspace.mkdir()
            (workspace / "a.txt").write_text("original", encoding="utf-8")
            manager = BackupManager(workspace, backups)
            item = manager.snapshot("a.txt", "a.snapshot")
            (workspace / "a.txt").write_text("changed", encoding="utf-8")
            manager.restore(item["snapshot"], "a.txt", item["sha256"])
            self.assertEqual((workspace / "a.txt").read_text(encoding="utf-8"), "original")


    def test_reject_symlink_escape_when_supported(self):
        import os
        with tempfile.TemporaryDirectory() as root:
            outside = Path(root).parent / (Path(root).name + "-outside")
            outside.mkdir()
            try:
                (Path(root) / "link").symlink_to(str(outside), target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation is not permitted on this platform.")
            try:
                with self.assertRaises(UnsafePathError):
                    resolve_inside(root, "link/escape.txt")
            finally:
                (Path(root) / "link").unlink()
                outside.rmdir()

    def test_reject_backup_symlink_escape_when_supported(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root) / "work"
            backups = Path(root) / "backups"
            workspace.mkdir()
            backups.mkdir()
            outside = Path(root) / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            manager = BackupManager(workspace, backups)
            try:
                (backups / "escape.snapshot").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation is not permitted on this platform.")
            with self.assertRaises(UnsafePathError):
                manager.restore("escape.snapshot", "target.txt",
                                __import__("hashlib").sha256(b"outside").hexdigest())

    def test_restore_accepts_backup_relative_snapshot_path(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root) / "work"
            backups = Path(root) / "backups"
            workspace.mkdir()
            (workspace / "data.txt").write_text("before", encoding="utf-8")
            manager = BackupManager(workspace, backups)
            item = manager.snapshot("data.txt", "nested/data.snapshot")
            (workspace / "data.txt").write_text("after", encoding="utf-8")
            manager.restore("nested/data.snapshot", "data.txt", item["sha256"])
            self.assertEqual((workspace / "data.txt").read_text(encoding="utf-8"), "before")

    def test_restore_rejects_modified_snapshot(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root) / "work"
            backups = Path(root) / "backups"
            workspace.mkdir()
            (workspace / "data.txt").write_text("keep", encoding="utf-8")
            manager = BackupManager(workspace, backups)
            item = manager.snapshot("data.txt", "data.snapshot")
            Path(item["snapshot"]).write_text("tampered", encoding="utf-8")
            with self.assertRaises(ValueError):
                manager.restore(item["snapshot"], "data.txt", item["sha256"])
            self.assertEqual((workspace / "data.txt").read_text(encoding="utf-8"), "keep")

if __name__ == "__main__":
    unittest.main()
