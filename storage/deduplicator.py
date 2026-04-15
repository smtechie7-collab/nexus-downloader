import hashlib
from monitoring.logger import get_logger

logger = get_logger("Deduplicator")

class Deduplicator:
    """
    Prevents redundant processing of the same URL.
    Ready for Redis integration in future distributed phases.
    """
    def __init__(self):
        self._seen_hashes = set()

    def _hash(self, url: str) -> str:
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def is_duplicate(self, url: str) -> bool:
        url_hash = self._hash(url)
        if url_hash in self._seen_hashes:
            logger.warning("Duplicate URL detected, skipping", extra={"context": {"url": url}})
            return True
        
        self._seen_hashes.add(url_hash)
        return False