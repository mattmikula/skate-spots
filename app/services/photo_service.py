"""Service layer for handling photo uploads and storage."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image

from app.core.config import get_settings


class PhotoStorageError(Exception):
    """Raised when photo storage operations fail."""

    pass


class PhotoService:
    """Service for managing photo uploads and storage operations."""

    def __init__(self) -> None:
        """Initialize the photo service with configuration."""
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.photo_upload_path)
        self.max_size = self.settings.photo_max_size_bytes
        self.allowed_types = self.settings.photo_allowed_types

    def ensure_upload_directory_exists(self) -> None:
        """Create the upload directory if it doesn't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> None:
        """Validate that an uploaded file meets requirements.

        Args:
            file: The uploaded file to validate

        Raises:
            PhotoStorageError: If the file is invalid
        """
        if not file.filename:
            raise PhotoStorageError("File must have a filename")

        if not file.content_type or file.content_type not in self.allowed_types:
            raise PhotoStorageError(
                f"File type '{file.content_type}' not allowed. "
                f"Allowed types: {', '.join(self.allowed_types)}"
            )

    async def save_photo(
        self,
        file: UploadFile,
        original_filename: str | None = None,
    ) -> tuple[str, str]:
        """Save an uploaded photo to storage and return path and filename info.

        Args:
            file: The uploaded file
            original_filename: Optional override for the original filename

        Returns:
            Tuple of (stored_filename, stored_file_path)
            - stored_filename: UUID-based filename
            - stored_file_path: Relative path from uploads root (e.g., "2024-10/uuid/file.jpg")

        Raises:
            PhotoStorageError: If the save operation fails
        """
        self.validate_file(file)
        self.ensure_upload_directory_exists()

        try:
            # Generate unique identifiers
            file_uuid = str(uuid4())
            date_folder = datetime.utcnow().strftime("%Y-%m")
            uuid_folder = self.upload_dir / date_folder / file_uuid
            uuid_folder.mkdir(parents=True, exist_ok=True)

            # Get the original filename for storage
            original_name = original_filename or file.filename or "photo.jpg"
            extension = Path(original_name).suffix.lower()
            if not extension:
                extension = ".jpg"

            stored_filename = f"{file_uuid}{extension}"
            stored_path = uuid_folder / stored_filename

            # Read file content
            if file.file:
                content = await file.read()
            else:
                raise PhotoStorageError("Could not read uploaded file")

            # Check file size
            if len(content) > self.max_size:
                raise PhotoStorageError(
                    f"File size {len(content)} bytes exceeds maximum "
                    f"allowed size of {self.max_size} bytes"
                )

            # Save original file
            with open(stored_path, "wb") as f:
                f.write(content)

            # Optimize image (resize if needed and re-compress)
            self._optimize_image(stored_path)

            # Return relative path from uploads root
            relative_path = f"{date_folder}/{file_uuid}/{stored_filename}"
            return stored_filename, relative_path

        except PhotoStorageError:
            raise
        except Exception as e:
            raise PhotoStorageError(f"Failed to save photo: {str(e)}") from e

    def _optimize_image(self, file_path: Path, max_width: int = 2000) -> None:
        """Optimize image by resizing if needed and re-compressing.

        Args:
            file_path: Path to the image file
            max_width: Maximum width in pixels (aspect ratio preserved)
        """
        try:
            with Image.open(file_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background

                # Resize if necessary
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Save with compression
                img.save(file_path, "JPEG", quality=85, optimize=True)
        except Exception:
            # Log but don't fail if optimization fails - we have the original
            pass

    def delete_photo(self, file_path: str) -> bool:
        """Delete a photo file from storage.

        Args:
            file_path: Relative path to the photo (from uploads root)

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            full_path = self.upload_dir / file_path
            if full_path.exists():
                full_path.unlink()

                # Try to clean up empty directories
                try:
                    # Remove the UUID folder if empty
                    uuid_folder = full_path.parent
                    if uuid_folder.exists() and not any(uuid_folder.iterdir()):
                        uuid_folder.rmdir()

                    # Remove the date folder if empty
                    date_folder = uuid_folder.parent
                    if date_folder.exists() and not any(date_folder.iterdir()):
                        date_folder.rmdir()
                except OSError:
                    # Folders might not be empty or other issues
                    pass

                return True
            return False
        except Exception:
            return False

    def get_photo_url(self, file_path: str) -> str:
        """Get the URL for a photo.

        Args:
            file_path: Relative path to the photo

        Returns:
            URL path that can be used in img tags or links
        """
        return f"/media/{file_path}"
