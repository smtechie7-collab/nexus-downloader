import asyncio
from typing import Dict, Any, List
import aiohttp
from engines.base_engine import BaseEngine
from utils.constants import Status, ErrorType
from monitoring.logger import get_logger

logger = get_logger("HeadlessEngine")

class HeadlessEngineV1(BaseEngine):
    """
    Browser automation-like engine using JavaScript execution simulation.
    Best for: JavaScript-heavy sites, dynamic content, AJAX-loaded media
    
    Note: In production, integrate Pyppeteer or Playwright for real browser automation.
    This version uses heuristics to simulate the behavior.
    """
    def __init__(self):
        super().__init__()
        self.name = "headless_engine"
        self.version = "v1"
        self.timeout = 30  # Longer timeout for JS execution

    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Simulates browser automation approach.
        In production, this would use Pyppeteer/Playwright for real JavaScript execution.
        """
        try:
            logger.info("Headless extraction started", extra={
                "context": {"url": url}
            })
            
            # Step 1: Fetch with JS execution simulation
            headers = self._get_browser_headers()
            
            async with aiohttp.ClientSession() as session:
                # Simulate page load with delay (JS execution time)
                await asyncio.sleep(2)
                
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
                            f"HTTP {resp.status}"
                        )
                    
                    html = await resp.text()
                    
                    # Step 2: Extract media using multiple strategies
                    media = await self._extract_media_advanced(html, url)
                    
                    if not media:
                        return self._format_error(
                            ErrorType.PARSE_ERROR,
                            "No media found after JS execution simulation"
                        )
                    
                    logger.info("Headless extraction successful", extra={
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
            return self._format_error(ErrorType.NETWORK_ERROR, "Headless timeout")
        except Exception as e:
            logger.error("Headless extraction failed", extra={
                "context": {"url": url, "error": str(e)}
            })
            return self._format_error(ErrorType.PARSE_ERROR, str(e))
    
    def _get_browser_headers(self) -> Dict[str, str]:
        """Returns headers matching a real browser."""
        return {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def _extract_media_advanced(self, html: str, base_url: str) -> List[Dict]:
        """
        Advanced extraction for JS-rendered content.
        Uses multiple patterns and heuristics.
        """
        media_list = []
        
        import json
        import re
        
        # Pattern 1: window.config or window.__data__ patterns
        window_data_pattern = r'window\.__?(?:config|data|STATE|INITIAL_STATE)\s*=\s*(\{.*?\});'
        for match in re.finditer(window_data_pattern, html, re.DOTALL):
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                urls = self._extract_urls_deep(data)
                media_list.extend(urls)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Pattern 2: <!--__NEXT_DATA__ or similar React hydration
        hydration_pattern = r'<script[^>]*id="__(?:NEXT_DATA|APOLLO_STATE)"[^>]*>(.*?)</script>'
        for match in re.finditer(hydration_pattern, html, re.DOTALL | re.IGNORECASE):
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                urls = self._extract_urls_deep(data)
                media_list.extend(urls)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Pattern 3: src attributes in video/source/iframe
        video_pattern = r'<(?:video|source|iframe)[^>]*src\s*=\s*["\']([^"\']*)["\']'
        for match in re.finditer(video_pattern, html, re.IGNORECASE):
            url = match.group(1)
            if any(url.endswith(ext) for ext in ['.mp4', '.webm', '.m3u8', '.ts']):
                media_list.append({
                    "url": url,
                    "type": "video",
                    "quality": "unknown",
                    "metadata": {"source": "html_tag"}
                })
        
        # Pattern 4: HLS/DASH playlist URLs
        playlist_pattern = r'(?:src|href|url)\s*[:=]\s*["\']([^"\']*\.(?:m3u8|mpd))["\']'
        for match in re.finditer(playlist_pattern, html, re.IGNORECASE):
            url = match.group(1)
            media_list.append({
                "url": url,
                "type": "video",
                "quality": "adaptive",
                "metadata": {"source": "playlist"}
            })
        
        # Remove duplicates while preserving order
        seen = set()
        unique_media = []
        for item in media_list:
            if item['url'] not in seen:
                seen.add(item['url'])
                unique_media.append(item)
        
        return unique_media
    
    def _extract_urls_deep(self, obj: any, max_depth: int = 5) -> List[Dict]:
        """Recursively extracts all media URLs from nested structures."""
        media_list = []
        if max_depth == 0:
            return media_list
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check if this looks like a URL
                if isinstance(value, str):
                    if (value.startswith('http') or value.startswith('/')) and any(
                        ext in value for ext in ['.mp4', '.webm', '.m3u8', '.ts', '.mpd']
                    ):
                        media_list.append({
                            "url": value,
                            "type": "video",
                            "quality": self._infer_quality(key),
                            "metadata": {"source": "json", "field": key}
                        })
                elif isinstance(value, (dict, list)):
                    media_list.extend(self._extract_urls_deep(value, max_depth - 1))
        elif isinstance(obj, list):
            for item in obj:
                media_list.extend(self._extract_urls_deep(item, max_depth - 1))
        
        return media_list
    
    def _infer_quality(self, text: str) -> str:
        """Infers video quality from text."""
        text_lower = text.lower()
        if '1080' in text_lower or 'full' in text_lower:
            return '1080p'
        elif '720' in text_lower or 'hd' in text_lower:
            return '720p'
        elif '480' in text_lower:
            return '480p'
        elif '360' in text_lower or 'sd' in text_lower:
            return '360p'
        return 'unknown'
    
    def _format_error(self, error_type: ErrorType, msg: str) -> Dict[str, Any]:
        return {
            "status": Status.FAIL.value,
            "source": self.source_name,
            "media": [],
            "error_type": error_type.value,
            "error_msg": msg
        }
