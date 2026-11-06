"""Append-only JSONL audit log; avoid writing secrets into event fields."""
import json
import os
import time
from pathlib import Path

class AuditLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event, actor="system", tool="", target="", result="ok", details=None):
        row = {"timestamp": time.time(), "event": str(event), "actor": str(actor),
               "tool": str(tool), "target": str(target), "result": str(result),
               "details": details or {}}
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
        return row
