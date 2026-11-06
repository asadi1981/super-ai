"""Simple workspace snapshots and verified restore for small local projects."""
import hashlib
import json
import shutil
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

    def snapshot(self, relative_path, snapshot_name):
        source = resolve_inside(self.workspace, relative_path)
        if not source.is_file():
            raise FileNotFoundError(str(relative_path))
        target = resolve_inside(self.backup_root, snapshot_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(target))
        return {"source": str(relative_path), "snapshot": str(target),
                "sha256": self._sha256(target), "size": target.stat().st_size}

    def restore(self, snapshot_path, relative_path, expected_sha256):
        snapshot = Path(snapshot_path).resolve()
        if not snapshot.is_file() or self._sha256(snapshot) != expected_sha256:
            raise ValueError("Snapshot is missing or checksum verification failed.")
        target = resolve_inside(self.workspace, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(snapshot), str(target))
        return target
