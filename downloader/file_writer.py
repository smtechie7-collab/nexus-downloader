import os
import tempfile
import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple, BinaryIO, Dict
from monitoring.logger import get_logger

logger = get_logger("FileWriter")

class SafeFileWriter:
    """
    Safe atomic file writer with collision prevention.
    Constitution Blueprint: Atomic writes with collision handling.
    """

    def __init__(self, base_dir: str = "./downloads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _generate_unique_filename(self, original_filename: str, url: str = "") -> str:
        """
        Generates a unique filename to prevent collisions.
        Uses content hash + timestamp for uniqueness.
        """
        # Extract base name and extension
        name_parts = original_filename.rsplit('.', 1)
        base_name = name_parts[0]
        extension = name_parts[1] if len(name_parts) > 1 else ""

        # Create hash from URL + timestamp for uniqueness
        hash_input = f"{url}{time.time()}{original_filename}".encode('utf-8')
        content_hash = hashlib.md5(hash_input).hexdigest()[:8]

        # Format: basename_hash.extension or basename_hash if no extension
        if extension:
            return f"{base_name}_{content_hash}.{extension}"
        else:
            return f"{base_name}_{content_hash}"

    def _find_available_filename(self, desired_path: Path) -> Path:
        """
        Finds an available filename by appending numbers if needed.
        """
        if not desired_path.exists():
            return desired_path

        stem = desired_path.stem
        suffix = desired_path.suffix
        parent = desired_path.parent
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def write_atomic(self, content: bytes, filename: str, url: str = "") -> Tuple[bool, str, Optional[str]]:
        """
        Atomically writes content to file with collision prevention.

        Args:
            content: Binary content to write
            filename: Desired filename
            url: Source URL for uniqueness hashing

        Returns:
            (success, final_filepath, error_message)
        """
        try:
            # Generate unique filename
            unique_filename = self._generate_unique_filename(filename, url)
            final_path = self.base_dir / unique_filename

            # Ensure no collision even with unique name
            final_path = self._find_available_filename(final_path)

            # Use atomic write with temporary file
            with tempfile.NamedTemporaryFile(
                dir=self.base_dir,
                prefix=f"temp_{final_path.stem}_",
                suffix=final_path.suffix,
                delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)

                # Write content to temporary file
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Force write to disk

            # Atomic move to final location
            temp_path.replace(final_path)

            logger.info("File written atomically", extra={
                "context": {
                    "filename": final_path.name,
                    "size": len(content),
                    "path": str(final_path)
                }
            })

            return True, str(final_path), None

        except Exception as e:
            error_msg = f"Atomic write failed: {str(e)}"
            logger.error("File write failed", extra={
                "context": {
                    "filename": filename,
                    "error": error_msg
                }
            })
            return False, "", error_msg

    def write_stream_atomic(self, stream: BinaryIO, filename: str, url: str = "",
                           chunk_size: int = 8192) -> Tuple[bool, str, Optional[str]]:
        """
        Atomically writes from a stream with collision prevention.

        Args:
            stream: Binary stream to read from
            filename: Desired filename
            url: Source URL for uniqueness
            chunk_size: Size of chunks to read/write

        Returns:
            (success, final_filepath, error_message)
        """
        try:
            # Generate unique filename
            unique_filename = self._generate_unique_filename(filename, url)
            final_path = self.base_dir / unique_filename
            final_path = self._find_available_filename(final_path)

            # Use atomic write with temporary file
            with tempfile.NamedTemporaryFile(
                dir=self.base_dir,
                prefix=f"temp_{final_path.stem}_",
                suffix=final_path.suffix,
                delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)

                # Stream content to temporary file
                if hasattr(stream, 'read'):
                    while True:
                        chunk = stream.read(chunk_size)
                        if not chunk:
                            break
                        temp_file.write(chunk)
                else:
                    for chunk in stream:
                        if not chunk:
                            continue
                        temp_file.write(chunk)

                temp_file.flush()
                os.fsync(temp_file.fileno())  # Force write to disk

            # Atomic move to final location
            temp_path.replace(final_path)

            file_size = final_path.stat().st_size
            logger.info("Stream written atomically", extra={
                "context": {
                    "filename": final_path.name,
                    "size": file_size,
                    "path": str(final_path)
                }
            })

            return True, str(final_path), None

        except Exception as e:
            error_msg = f"Stream write failed: {str(e)}"
            logger.error("Stream write failed", extra={
                "context": {
                    "filename": filename,
                    "error": error_msg
                }
            })
            return False, "", error_msg

    def cleanup_temp_files(self, max_age_seconds: int = 3600) -> int:
        """
        Cleans up temporary files older than max_age_seconds.
        Returns number of files cleaned up.
        """
        cleaned_count = 0
        current_time = time.time()

        try:
            with os.scandir(self.base_dir) as scan:
                for entry in scan:
                    if not entry.name.startswith("temp_") or not entry.is_file():
                        continue

                    file_path = Path(entry.path)
                    stat_result = file_path.stat()
                    mtime = getattr(stat_result, 'st_mtime', None)
                    if mtime is None:
                        continue
                    try:
                        file_age = current_time - float(mtime)
                    except (TypeError, ValueError):
                        continue

                    if file_age > max_age_seconds:
                        os.unlink(entry.path)
                        cleaned_count += 1
                        logger.debug("Cleaned up temp file", extra={
                            "context": {"file": entry.path, "age_seconds": int(file_age)}
                        })

        except Exception as e:
            logger.warning("Temp file cleanup failed", extra={"context": {"error": str(e)}})

        return cleaned_count

    def get_file_info(self, filepath: str) -> Optional[Dict]:
        """
        Gets information about a written file.
        """
        try:
            path = Path(filepath)
            if path.exists() and path.is_file():
                stat = path.stat()
                return {
                    "path": str(path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "exists": True
                }
        except Exception as e:
            logger.warning("File info retrieval failed", extra={
                "context": {"filepath": filepath, "error": str(e)}
            })

        return None