"""Small-project snapshots with checksum verification and atomic restore."""
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from .safe_files import resolve_inside


class BackupManager:
    def __init__(self, workspace, backup_root):
        self.workspace = Path(workspace).resolve()
        self.backup_root = Path(backup_root).resolve()
        self.backup_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sha256(path):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _copy_atomic(source, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".superai-backup-", dir=str(target.parent))
        os.close(fd)
        try:
            shutil.copy2(str(source), temp_name)
            with open(temp_name, "rb") as stream:
                os.fsync(stream.fileno())
            os.replace(temp_name, str(target))
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def snapshot(self, relative_path, snapshot_name):
        source = resolve_inside(self.workspace, relative_path)
        if not source.is_file():
            raise FileNotFoundError(str(relative_path))
        target = resolve_inside(self.backup_root, snapshot_name)
        if source == target:
            raise ValueError("Source and snapshot paths must be different.")
        self._copy_atomic(source, target)
        return {"source": str(relative_path), "snapshot": str(target),
                "sha256": self._sha256(target), "size": target.stat().st_size}

    def restore(self, snapshot_path, relative_path, expected_sha256):
        # Accept either a path relative to backup_root or an absolute path
        # already contained by backup_root. resolve_inside rejects symlink escapes.
        raw_snapshot = Path(snapshot_path)
        if raw_snapshot.is_absolute():
            try:
                relative_snapshot = raw_snapshot.resolve().relative_to(self.backup_root)
            except ValueError:
                raise ValueError("Snapshot must be inside the managed backup directory.")
        else:
            relative_snapshot = raw_snapshot
        snapshot = resolve_inside(self.backup_root, relative_snapshot)
        if not snapshot.is_file() or self._sha256(snapshot) != expected_sha256:
            raise ValueError("Snapshot is missing or checksum verification failed.")
        target = resolve_inside(self.workspace, relative_path)
        if snapshot == target:
            raise ValueError("Snapshot and restore target must be different.")
        # Revalidate after creating parent directories before the atomic replace.
        target.parent.mkdir(parents=True, exist_ok=True)
        target = resolve_inside(self.workspace, relative_path)
        self._copy_atomic(snapshot, target)
        return target
