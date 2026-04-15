import asyncio
import time
from urllib.parse import urlparse
import yaml
from monitoring.logger import get_logger

logger = get_logger("RateLimiter")

class RateLimiter:
    """
    Enforces per-domain and global request limits dynamically.
    Reads directly from config.yaml.
    """
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.per_domain_limit = self.config['rate_limit']['per_domain'] # Req per second
        self.domain_locks = {}
        self.last_called = {}
        
        # Calculate minimum delay between requests for a domain
        self.delay_seconds = 1.0 / self.per_domain_limit if self.per_domain_limit > 0 else 0

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    async def wait_if_needed(self, url: str):
        domain = self._get_domain(url)
        
        if domain not in self.domain_locks:
            self.domain_locks[domain] = asyncio.Lock()
            self.last_called[domain] = 0.0

        async with self.domain_locks[domain]:
            now = time.time()
            elapsed = now - self.last_called[domain]
            
            if elapsed < self.delay_seconds:
                sleep_time = self.delay_seconds - elapsed
                logger.debug("Rate limiting triggered", extra={"context": {"domain": domain, "sleep": round(sleep_time, 2)}})
                await asyncio.sleep(sleep_time)
                
            self.last_called[domain] = time.time()