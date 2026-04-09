"""
media_storage.py
────────────────
Thin wrapper around the local filesystem (MEDIA_ROOT).
Swap the _save / _read implementations for S3/GCS without touching
any other part of the app.
"""
import os
import hashlib
from pathlib import Path
from django.conf import settings


def _media_root() -> Path:
    root = Path(settings.MEDIA_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_file(content: bytes, filename: str, subfolder: str = 'documents') -> dict:
    """
    Persist *content* to MEDIA_ROOT/<subfolder>/<filename>.
    Returns a dict with the metadata the DB should store.
    Never stores the binary in the DB.
    """
    dest_dir = _media_root() / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / filename
    # Avoid overwriting — append a short hash if the name already exists
    if dest_path.exists():
        digest = hashlib.md5(content).hexdigest()[:6]
        stem, suffix = os.path.splitext(filename)
        dest_path = dest_dir / f"{stem}_{digest}{suffix}"

    dest_path.write_bytes(content)

    rel_path = dest_path.relative_to(_media_root())
    return {
        'file_path': str(rel_path),
        'file_size': len(content),
    }


def save_text_as_file(text: str, filename: str, subfolder: str = 'documents') -> dict:
    """Convenience wrapper for plain-text / markdown content."""
    return save_file(text.encode('utf-8'), filename, subfolder)


def get_absolute_path(relative_path: str) -> Path:
    """Resolve a DB-stored relative path back to an absolute filesystem path."""
    return _media_root() / relative_path


def file_exists(relative_path: str) -> bool:
    return get_absolute_path(relative_path).exists()