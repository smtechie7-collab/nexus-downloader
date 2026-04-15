import aiohttp
from typing import Optional, Dict, List
import asyncio
from monitoring.logger import get_logger

logger = get_logger("SessionManager")

class SessionManager:
    """
    Manages HTTP sessions with connection pooling and resource reuse.
    Ensures efficient network utilization across multiple requests.
    """
    
    def __init__(self, 
                 max_connections: int = 100,
                 max_connections_per_host: int = 30,
                 timeout_seconds: int = 30,
                 ssl_verify: bool = False):
        """
        Initialize session manager.
        
        Args:
            max_connections: Maximum concurrent connections
            max_connections_per_host: Max connections per domain
            timeout_seconds: Request timeout in seconds
            ssl_verify: Whether to verify SSL certificates
        """
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout_seconds = timeout_seconds
        self.ssl_verify = ssl_verify
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
        
        logger.info("SessionManager initialized", extra={
            "context": {
                "max_connections": max_connections,
                "max_connections_per_host": max_connections_per_host,
                "timeout": timeout_seconds
            }
        })
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Gets or creates a reusable connection session."""
        if self._session is None:
            async with self._lock:
                if self._session is None:
                    connector = aiohttp.TCPConnector(
                        limit=self.max_connections,
                        limit_per_host=self.max_connections_per_host,
                        ssl=self.ssl_verify
                    )
                    
                    timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
                    
                    self._session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout
                    )
                    
                    logger.info("Session created", extra={
                        "context": {"session_id": id(self._session)}
                    })
        
        return self._session
    
    async def close(self):
        """Closes the session and releases resources."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("Session closed")
    
    async def __aenter__(self):
        return await self.get_session()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def get_connection_stats(self) -> Dict:
        """Returns session connection statistics."""
        if not self._session:
            return {"status": "inactive"}
        
        connector = self._session.connector
        stats = {
            "status": "active",
            "max_connections": connector.limit,
            "max_per_host": connector.limit_per_host,
        }
        
        return stats
