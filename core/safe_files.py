"""Path-confined file operations. This module never executes file contents."""
import os
import tempfile
from pathlib import Path

class UnsafePathError(ValueError):
    pass

def resolve_inside(root, relative_path):
    root_path = Path(root).resolve()
    candidate = (root_path / relative_path).resolve()
    try:
        common = os.path.commonpath([str(root_path), str(candidate)])
    except ValueError:
        raise UnsafePathError("Path is outside the workspace.")
    if common != str(root_path):
        raise UnsafePathError("Path is outside the workspace.")
    return candidate

def read_text(root, relative_path, max_bytes=2 * 1024 * 1024):
    path = resolve_inside(root, relative_path)
    if not path.is_file():
        raise FileNotFoundError(str(relative_path))
    if path.stat().st_size > max_bytes:
        raise ValueError("File exceeds configured size limit.")
    with path.open("r", encoding="utf-8-sig") as stream:
        return stream.read()

def write_text_atomic(root, relative_path, content, max_bytes=2 * 1024 * 1024):
    if not isinstance(content, str):
        raise TypeError("content must be text")
    data = content.encode("utf-8")
    if len(data) > max_bytes:
        raise ValueError("Content exceeds configured size limit.")
    path = resolve_inside(root, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".superai-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, str(path))
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return path
