"""Small-project snapshots with checksum verification and atomic restore."""
import hashlib
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from .safe_files import resolve_inside


class BackupManager:
    def __init__(self, workspace, backup_root):
        self.workspace = Path(workspace).resolve()
        self.backup_root = Path(backup_root).resolve()
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.last_rollback = None

    @staticmethod
    def _sha256(path):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _copy_atomic(source, target):
        """Copy bytes to a writable temporary file, fsync, then replace atomically."""
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".superai-backup-", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as destination:
                with source.open("rb") as origin:
                    shutil.copyfileobj(origin, destination)
                destination.flush()
                os.fsync(destination.fileno())
            shutil.copystat(str(source), temp_name)
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
        # Create a rollback copy before replacing an existing destination.
        target.parent.mkdir(parents=True, exist_ok=True)
        target = resolve_inside(self.workspace, relative_path)
        self.last_rollback = None
        if target.exists():
            if not target.is_file():
                raise ValueError("Restore target exists and is not a regular file.")
            rollback_name = "restore-rollback/" + uuid.uuid4().hex + "-" + target.name
            rollback = resolve_inside(self.backup_root, rollback_name)
            self._copy_atomic(target, rollback)
            self.last_rollback = {
                "snapshot": str(rollback),
                "sha256": self._sha256(rollback),
                "size": rollback.stat().st_size,
                "target": str(relative_path),
            }
        self._copy_atomic(snapshot, target)
        return target
