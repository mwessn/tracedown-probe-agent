"""Filesystem body storage — for local setups and testing."""

from __future__ import annotations

import shutil
from pathlib import Path

from storage.base import BodyStorage

SCHEME = "file://"


class FilesystemStorage(BodyStorage):
    """Stores bodies on the local filesystem.

    Bodies are copied from the executor's temp directory to a persistent
    volume at ``root_dir``. Storage URIs use the ``file://`` scheme.
    """

    def __init__(self, root_dir: str) -> None:
        self._root = Path(root_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def upload(self, local_path: Path, key: str) -> str:
        """Copy file to persistent storage directory.

        Returns a ``file://`` URI, e.g. ``file:///data/bodies/call_0.json``.
        """
        dest = self._root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)
        return f"{SCHEME}{dest}"

    def download_url(self, uri: str) -> str | None:
        """Return the absolute path if the file exists."""
        path = Path(_strip_scheme(uri))
        return str(path) if path.exists() else None


def _strip_scheme(uri: str) -> str:
    """Remove the file:// prefix, returning the raw path."""
    if uri.startswith(SCHEME):
        return uri[len(SCHEME):]
    return uri
