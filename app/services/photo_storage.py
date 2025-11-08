"""Utilities for persisting uploaded skate spot photos to disk."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final
from uuid import uuid4

from app.core.config import get_settings

if TYPE_CHECKING:
    from collections.abc import Iterable

    from fastapi import UploadFile

_ALLOWED_MIME_PREFIX: Final[str] = "image/"


class PhotoStorageError(RuntimeError):
    """Base exception raised when photo persistence fails."""


@dataclass(slots=True)
class StoredPhoto:
    """Result returned when a photo upload has been stored on disk."""

    path: str
    original_filename: str | None


def _ensure_within_media_root(path: Path, media_root: Path) -> None:
    """Ensure ``path`` resides under ``media_root`` to avoid directory traversal."""

    try:
        path.resolve().relative_to(media_root.resolve())
    except ValueError as exc:  # pragma: no cover - safety net
        raise PhotoStorageError("attempted to access path outside media directory") from exc


def _generate_destination(upload: UploadFile, media_root: Path) -> tuple[Path, str]:
    """Return destination path for an upload and the stored relative path string."""

    suffix = Path(upload.filename or "").suffix.lower()
    timestamp = datetime.now(UTC)
    subdir = Path(str(timestamp.year), f"{timestamp.month:02d}")
    destination_dir = media_root / subdir
    destination_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{suffix}"
    destination = destination_dir / filename
    relative_path = str(subdir / filename).replace("\\", "/")
    _ensure_within_media_root(destination, media_root)
    return destination, relative_path


def save_photo_upload(upload: UploadFile) -> StoredPhoto:
    """Persist an uploaded file under the configured media directory."""

    if not upload.filename:
        raise PhotoStorageError("uploaded file is missing a filename")

    if not upload.content_type or not upload.content_type.startswith(_ALLOWED_MIME_PREFIX):
        raise PhotoStorageError("unsupported file type; only image uploads are allowed")

    settings = get_settings()
    media_root = Path(settings.media_directory)
    media_root.mkdir(parents=True, exist_ok=True)

    destination, relative_path = _generate_destination(upload, media_root)

    upload.file.seek(0)
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
    except OSError as exc:  # pragma: no cover - filesystem failure
        raise PhotoStorageError("failed to write uploaded photo to disk") from exc

    return StoredPhoto(path=relative_path, original_filename=upload.filename)


def delete_photo(path: str) -> None:
    """Remove a stored photo from disk, ignoring missing files."""

    settings = get_settings()
    media_root = Path(settings.media_directory)
    file_path = media_root / Path(path)
    _ensure_within_media_root(file_path, media_root)

    try:
        file_path.unlink(missing_ok=True)
    except OSError as exc:  # pragma: no cover - filesystem failure
        raise PhotoStorageError("failed to delete photo from disk") from exc


def delete_photos(paths: Iterable[str]) -> None:
    """Remove multiple stored photos, suppressing individual errors."""

    for path in paths:
        if not path:
            continue
        try:
            delete_photo(path)
        except PhotoStorageError:
            # We log these downstream; avoid raising to keep cleanup best-effort.
            continue
