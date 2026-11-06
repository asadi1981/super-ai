"""Checksummed snapshots and crash-recoverable restore operations."""
import hashlib
import json
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
        self.manifest_root = self.backup_root / "restore-manifests"
        self.manifest_root.mkdir(parents=True, exist_ok=True)
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

    @staticmethod
    def _write_json_atomic(path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".superai-manifest-", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, str(path))
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

    def _load_manifest(self, manifest_id):
        name = str(manifest_id)
        if Path(name).name != name or not name.endswith(".json"):
            name += ".json"
        path = resolve_inside(self.manifest_root, name)
        if not path.is_file():
            raise FileNotFoundError(name)
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
        if data.get("version") != 1:
            raise ValueError("Unsupported rollback manifest version.")
        return path, data

    def restore(self, snapshot_path, relative_path, expected_sha256):
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
        target.parent.mkdir(parents=True, exist_ok=True)
        target = resolve_inside(self.workspace, relative_path)
        self.last_rollback = None
        manifest_id = uuid.uuid4().hex
        manifest_path = self.manifest_root / (manifest_id + ".json")
        rollback = None
        if target.exists():
            if not target.is_file():
                raise ValueError("Restore target exists and is not a regular file.")
            rollback_name = "restore-rollback/" + manifest_id + "-" + target.name
            rollback = resolve_inside(self.backup_root, rollback_name)
            self._copy_atomic(target, rollback)
            rollback_info = {
                "snapshot": str(rollback.relative_to(self.backup_root)),
                "sha256": self._sha256(rollback),
                "size": rollback.stat().st_size,
            }
        else:
            rollback_info = None
        # Durable intent is written before the destination is replaced.
        manifest = {
            "version": 1, "id": manifest_id, "state": "prepared",
            "target": str(Path(relative_path)), "rollback": rollback_info,
            "restore_snapshot": str(snapshot.relative_to(self.backup_root)),
            "restore_sha256": expected_sha256,
        }
        self._write_json_atomic(manifest_path, manifest)
        self._copy_atomic(snapshot, target)
        manifest["state"] = "completed"
        self._write_json_atomic(manifest_path, manifest)
        self.last_rollback = {
            "manifest": manifest_id,
            "snapshot": str(rollback) if rollback else None,
            "sha256": rollback_info["sha256"] if rollback_info else None,
            "size": rollback_info["size"] if rollback_info else 0,
            "target": str(relative_path),
        }
        return target

    def pending_recoveries(self):
        """Return restore intents whose final state was not durably recorded."""
        pending = []
        for path in sorted(self.manifest_root.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as stream:
                    item = json.load(stream)
                if item.get("version") == 1 and item.get("state") == "prepared":
                    pending.append({"manifest": path.stem, "target": item.get("target"),
                                    "has_rollback": bool(item.get("rollback"))})
            except (OSError, ValueError):
                # Corrupt manifests are deliberately surfaced, not silently repaired.
                pending.append({"manifest": path.stem, "error": "unreadable_manifest"})
        return pending

    def recover_rollback(self, manifest_id):
        """Explicitly restore the pre-restore file from a durable manifest."""
        manifest_path, item = self._load_manifest(manifest_id)
        rollback_info = item.get("rollback")
        if not rollback_info:
            raise ValueError("This restore has no previous target to roll back.")
        rollback = resolve_inside(self.backup_root, rollback_info["snapshot"])
        if not rollback.is_file() or self._sha256(rollback) != rollback_info["sha256"]:
            raise ValueError("Rollback snapshot is missing or checksum verification failed.")
        target = resolve_inside(self.workspace, item["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target = resolve_inside(self.workspace, item["target"])
        self._copy_atomic(rollback, target)
        item["state"] = "rolled_back"
        self._write_json_atomic(manifest_path, item)
        return target
