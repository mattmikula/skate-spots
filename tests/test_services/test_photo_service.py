"""Tests for the photo storage service."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.services.photo_service import PhotoService, PhotoStorageError


@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for test uploads."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def photo_service(temp_upload_dir):
    """Create a PhotoService with a temporary upload directory."""
    service = PhotoService()
    service.upload_dir = temp_upload_dir
    return service


def test_ensure_upload_directory_exists(photo_service):
    """Test that upload directory is created if it doesn't exist."""
    photo_service.upload_dir.rmdir()  # Remove the directory
    assert not photo_service.upload_dir.exists()

    photo_service.ensure_upload_directory_exists()

    assert photo_service.upload_dir.exists()


def test_validate_file_no_filename():
    """Test that validation fails when file has no filename."""
    service = PhotoService()
    file = MagicMock(spec=UploadFile)
    file.filename = None

    with pytest.raises(PhotoStorageError, match="File must have a filename"):
        service.validate_file(file)


def test_validate_file_invalid_content_type():
    """Test that validation fails with unsupported content type."""
    service = PhotoService()
    file = MagicMock(spec=UploadFile)
    file.filename = "test.txt"
    file.content_type = "text/plain"

    with pytest.raises(PhotoStorageError, match="File type .* not allowed"):
        service.validate_file(file)


def test_validate_file_success():
    """Test that validation passes with valid file."""
    service = PhotoService()
    file = MagicMock(spec=UploadFile)
    file.filename = "test.jpg"
    file.content_type = "image/jpeg"

    # Should not raise
    service.validate_file(file)


def test_validate_file_png_support():
    """Test that PNG files are supported."""
    service = PhotoService()
    file = MagicMock(spec=UploadFile)
    file.filename = "test.png"
    file.content_type = "image/png"

    service.validate_file(file)  # Should not raise


def test_validate_file_webp_support():
    """Test that WebP files are supported."""
    service = PhotoService()
    file = MagicMock(spec=UploadFile)
    file.filename = "test.webp"
    file.content_type = "image/webp"

    service.validate_file(file)  # Should not raise


@pytest.mark.asyncio
async def test_save_photo_file_too_large(photo_service):
    """Test that oversized files are rejected."""
    file = AsyncMock(spec=UploadFile)
    file.filename = "test.jpg"
    file.content_type = "image/jpeg"

    # Create content that exceeds max size
    oversized_content = b"x" * (photo_service.max_size + 1)
    file.read = AsyncMock(return_value=oversized_content)
    file.file = MagicMock()

    with pytest.raises(PhotoStorageError, match="exceeds maximum allowed size"):
        await photo_service.save_photo(file)


@pytest.mark.asyncio
async def test_save_photo_missing_file_attribute():
    """Test that save_photo fails when file.file is None."""
    service = PhotoService()

    file = MagicMock()
    file.filename = "test.jpg"
    file.content_type = "image/jpeg"
    file.file = None  # No file attribute

    with pytest.raises(PhotoStorageError, match="Could not read uploaded file"):
        await service.save_photo(file)


def test_delete_photo_success(photo_service):
    """Test successful photo deletion."""
    # Create a test file
    test_file = photo_service.upload_dir / "2024-10" / "test-uuid" / "test.jpg"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("test content")

    # Delete the file
    success = photo_service.delete_photo("2024-10/test-uuid/test.jpg")

    assert success is True
    assert not test_file.exists()


def test_delete_photo_not_found(photo_service):
    """Test deletion of non-existent photo returns False."""
    success = photo_service.delete_photo("nonexistent/file.jpg")
    assert success is False


def test_delete_photo_cleans_empty_directories(photo_service):
    """Test that empty directories are cleaned up after deletion."""
    # Create a test file
    test_file = photo_service.upload_dir / "2024-10" / "test-uuid" / "test.jpg"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("test content")

    uuid_dir = test_file.parent
    date_dir = uuid_dir.parent

    assert uuid_dir.exists()
    assert date_dir.exists()

    # Delete the file
    photo_service.delete_photo("2024-10/test-uuid/test.jpg")

    # Directories should be cleaned up
    assert not uuid_dir.exists()
    assert not date_dir.exists()


def test_get_photo_url():
    """Test that photo URLs are properly formatted."""
    service = PhotoService()
    file_path = "2024-10/abc-uuid/photo.jpg"

    url = service.get_photo_url(file_path)

    assert url.startswith("/")
    assert file_path in url
