import time
from typing import Dict, Any, Optional
from monitoring.logger import get_logger

logger = get_logger("CacheLayer")

class CacheLayer:
    """
    URL -> Response mapping to save bandwidth and engine calls.
    TTL (Time-to-Live) ensures we don't serve dead links.
    """
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        if url in self.cache:
            entry = self.cache[url]
            if time.time() - entry['timestamp'] < self.ttl:
                logger.info("Cache hit", extra={"context": {"url": url}})
                return entry['data']
            else:
                del self.cache[url] # Expired
        return None

    def set(self, url: str, data: Dict[str, Any]):
        self.cache[url] = {
            'timestamp': time.time(),
            'data': data
        }