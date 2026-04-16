import os
import re
import hashlib
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from monitoring.logger import get_logger

logger = get_logger("Helpers")

class StringUtils:
    """String manipulation utilities."""

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        Sanitizes filename by removing/replacing invalid characters.
        """
        if not filename:
            return "download"

        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

        # Trim whitespace and dots
        filename = filename.strip(' .')

        # Truncate if too long
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            ext_len = len(ext)
            name = name[:max_length - ext_len - 1]  # -1 for dot
            filename = name + ext

        # Ensure not empty
        return filename or "download"

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncates text to max_length with optional suffix."""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extracts domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalizes whitespace in text."""
        return re.sub(r'\s+', ' ', text.strip())


class FileUtils:
    """File system utilities."""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> bool:
        """Ensures directory exists, creates if necessary."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error("Directory creation failed", extra={
                "context": {"path": str(path), "error": str(e)}
            })
            return False

    @staticmethod
    def get_file_size_mb(filepath: Union[str, Path]) -> float:
        """Gets file size in MB."""
        try:
            return Path(filepath).stat().st_size / (1024 * 1024)
        except:
            return 0.0

    @staticmethod
    def calculate_hash(filepath: Union[str, Path], algorithm: str = 'md5') -> Optional[str]:
        """Calculates file hash."""
        try:
            hash_func = hashlib.new(algorithm)
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.warning("Hash calculation failed", extra={
                "context": {"file": str(filepath), "error": str(e)}
            })
            return None

    @staticmethod
    def safe_delete(filepath: Union[str, Path]) -> bool:
        """Safely deletes a file."""
        try:
            Path(filepath).unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.warning("File deletion failed", extra={
                "context": {"file": str(filepath), "error": str(e)}
            })
            return False


class TimeUtils:
    """Time and date utilities."""

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Formats duration in human readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    @staticmethod
    def get_timestamp() -> str:
        """Gets current timestamp in ISO format."""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    @staticmethod
    def parse_duration(duration_str: str) -> Optional[float]:
        """Parses duration string like '1h 30m 45s' to seconds."""
        if not duration_str:
            return None

        total_seconds = 0.0
        # Match patterns like 1h, 30m, 45s, 1.5m
        pattern = r'(?:(\d+(?:\.\d+)?)([smhd]))'
        matches = re.findall(pattern, duration_str.lower())

        multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}

        for value, unit in matches:
            if unit in multipliers:
                total_seconds += float(value) * multipliers[unit]

        return total_seconds if matches else None


class DataUtils:
    """Data manipulation utilities."""

    @staticmethod
    def deep_merge_dicts(base: Dict, update: Dict) -> Dict:
        """Deep merges two dictionaries."""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataUtils.deep_merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def flatten_dict(d: Dict, prefix: str = '', separator: str = '.') -> Dict:
        """Flattens nested dictionary."""
        items = []
        for key, value in d.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            if isinstance(value, dict):
                items.extend(DataUtils.flatten_dict(value, new_key, separator).items())
            else:
                items.append((new_key, value))
        return dict(items)

    @staticmethod
    def safe_get_nested_value(data: Dict, keys: List[str], default: Any = None) -> Any:
        """Safely gets nested dictionary value."""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current


class ValidationUtils:
    """Data validation utilities."""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validates URL format."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validates email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """Validates file extension."""
        if not filename or '.' not in filename:
            return False

        ext = filename.split('.')[-1].lower()
        return ext in [e.lower().lstrip('.') for e in allowed_extensions]


# Convenience functions for common operations
def sanitize_filename(filename: str) -> str:
    """Convenience function for filename sanitization."""
    return StringUtils.sanitize_filename(filename)

def ensure_dir(path: str) -> bool:
    """Convenience function for directory creation."""
    return FileUtils.ensure_directory(path)

def format_bytes(size_bytes: int) -> str:
    """Formats bytes in human readable format."""
    if size_bytes == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"