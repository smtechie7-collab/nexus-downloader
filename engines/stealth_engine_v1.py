import asyncio
from typing import Dict, Any, List
import aiohttp
from engines.base_engine import BaseEngine
from utils.constants import Status, ErrorType
from monitoring.logger import get_logger

logger = get_logger("StealthEngine")

class StealthEngineV1(BaseEngine):
    """
    Anti-detection engine using browser-like headers and request patterns.
    Best for: Websites with bot detection, anti-scraping protection
    """
    def __init__(self):
        super().__init__()
        self.name = "stealth_engine"
        self.version = "v1"
        self.timeout = 20

    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Extracts content using stealth headers and intelligent rate limiting.
        Mimics real browser behavior to bypass detection.
        """
        try:
            # Stealth headers
            headers = self._get_stealth_headers()
            
            async with aiohttp.ClientSession() as session:
                # Small delay to avoid suspicious rapid requests
                await asyncio.sleep(0.5)
                
                async with session.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    ssl=False,
                    allow_redirects=True
                ) as resp:
                    if resp.status >= 400:
                        return self._format_error(
                            ErrorType.ACCESS_DENIED,
                            f"HTTP {resp.status} - Access Denied"
                        )
                    
                    content = await resp.text()
                    media = self._extract_from_json_and_html(content, url)
                    
                    if not media:
                        return self._format_error(
                            ErrorType.PARSE_ERROR,
                            "No media found"
                        )
                    
                    logger.info("Stealth extraction successful", extra={
                        "context": {"url": url, "media_count": len(media)}
                    })
                    
                    return {
                        "status": Status.SUCCESS.value,
                        "source": self.source_name,
                        "media": media,
                        "error_type": ErrorType.NONE.value,
                        "error_msg": None
                    }
                    
        except asyncio.TimeoutError:
            return self._format_error(ErrorType.NETWORK_ERROR, "Request timeout")
        except Exception as e:
            logger.error("Stealth extraction failed", extra={
                "context": {"url": url, "error": str(e)}
            })
            return self._format_error(ErrorType.PARSE_ERROR, str(e))
    
    def _get_stealth_headers(self) -> Dict[str, str]:
        """Returns headers that mimic a real browser."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    
    def _extract_from_json_and_html(self, content: str, base_url: str) -> List[Dict]:
        """Extracts media from JSON-embedded data and HTML."""
        media_list = []
        
        import json
        import re
        
        # Try to find JSON data in script tags
        json_pattern = r'<script[^>]*>[\s\n]*(\{.*?\})[\s\n]*</script>'
        for match in re.finditer(json_pattern, content, re.DOTALL):
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                urls = self._extract_urls_from_dict(data)
                media_list.extend(urls)
            except json.JSONDecodeError:
                pass
        
        # Also look for data attributes
        data_pattern = r'data-["\'](src|url|video)["\']="([^"\']*)"'
        for match in re.finditer(data_pattern, content, re.IGNORECASE):
            url = match.group(2)
            if any(url.endswith(ext) for ext in ['.mp4', '.webm', '.m3u8']):
                media_list.append({
                    "url": url,
                    "type": "video",
                    "quality": "unknown",
                    "metadata": {"source": "data_attribute"}
                })
        
        # Remove duplicates
        unique_media = {item['url']: item for item in media_list}.values()
        return list(unique_media)
    
    def _extract_urls_from_dict(self, obj: any, max_depth: int = 3) -> List[Dict]:
        """Recursively extracts media URLs from nested JSON structures."""
        media_list = []
        if max_depth == 0:
            return media_list
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check if value is a URL-like string
                if isinstance(value, str) and any(value.startswith(p) for p in ['http://', 'https://', '/']):
                    if any(value.endswith(ext) for ext in ['.mp4', '.webm', '.m3u8', '.ts']):
                        media_list.append({
                            "url": value,
                            "type": "video",
                            "quality": self._extract_quality(key),
                            "metadata": {"source": "json_field", "field": key}
                        })
                elif isinstance(value, (dict, list)):
                    media_list.extend(self._extract_urls_from_dict(value, max_depth - 1))
        elif isinstance(obj, list):
            for item in obj:
                media_list.extend(self._extract_urls_from_dict(item, max_depth - 1))
        
        return media_list
    
    def _extract_quality(self, key: str) -> str:
        """Extracts quality info from key names."""
        quality_map = {
            '1080': '1080p', '720': '720p', '480': '480p', '360': '360p',
            'hd': 'HD', 'sd': 'SD', 'full': '1080p', 'high': 'HD', 'low': 'SD'
        }
        key_lower = key.lower()
        for pattern, quality in quality_map.items():
            if pattern in key_lower:
                return quality
        return 'unknown'
    
    def _format_error(self, error_type: ErrorType, msg: str) -> Dict[str, Any]:
        return {
            "status": Status.FAIL.value,
            "source": self.source_name,
            "media": [],
            "error_type": error_type.value,
            "error_msg": msg
        }
