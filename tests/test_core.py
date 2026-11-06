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

if __name__ == "__main__":
    unittest.main()
