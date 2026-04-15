import asyncio
import re
from typing import Dict, Any, List
import aiohttp
from engines.base_engine import BaseEngine
from utils.constants import Status, ErrorType
from monitoring.logger import get_logger

logger = get_logger("SpiderEngine")

class SpiderEngineV1(BaseEngine):
    """
    Web scraping engine using HTML parsing and regex extraction.
    Best for: Static HTML content, articles, metadata
    """
    def __init__(self):
        super().__init__()
        self.name = "spider_engine"
        self.version = "v1"
        self.timeout = 15

    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Extracts content using web scraping techniques.
        Fetches HTML and parses for media elements.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout, ssl=False) as resp:
                    if resp.status >= 400:
                        return self._format_error(
                            ErrorType.NETWORK_ERROR,
                            f"HTTP {resp.status}"
                        )
                    
                    html = await resp.text()
                    media = await self._parse_html(html, url)
                    
                    if not media:
                        return self._format_error(
                            ErrorType.PARSE_ERROR,
                            "No media found in page"
                        )
                    
                    logger.info("Spider extraction successful", extra={
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
            logger.error("Spider extraction failed", extra={
                "context": {"url": url, "error": str(e)}
            })
            return self._format_error(ErrorType.PARSE_ERROR, str(e))
    
    async def _parse_html(self, html: str, base_url: str) -> List[Dict]:
        """Extracts media URLs from HTML content."""
        media_list = []
        
        # Extract video URLs
        video_pattern = r'(?:src|href)\s*=\s*["\']([^"\']*\.(?:mp4|webm|mkv|avi))["\']'
        for match in re.finditer(video_pattern, html, re.IGNORECASE):
            url = match.group(1)
            media_list.append({
                "url": url,
                "type": "video",
                "quality": "unknown",
                "metadata": {"source": "html_video_tag"}
            })
        
        # Extract image URLs
        img_pattern = r'<img[^>]*src\s*=\s*["\']([^"\']*)["\']'
        for match in re.finditer(img_pattern, html, re.IGNORECASE):
            url = match.group(1)
            if any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                media_list.append({
                    "url": url,
                    "type": "image",
                    "quality": "unknown",
                    "metadata": {"source": "img_tag"}
                })
        
        # Extract audio URLs
        audio_pattern = r'(?:src|href)\s*=\s*["\']([^"\']*\.(?:mp3|wav|flac|aac))["\']'
        for match in re.finditer(audio_pattern, html, re.IGNORECASE):
            url = match.group(1)
            media_list.append({
                "url": url,
                "type": "audio",
                "quality": "unknown",
                "metadata": {"source": "html_audio_tag"}
            })
        
        # Remove duplicates
        unique_media = {item['url']: item for item in media_list}.values()
        return list(unique_media)
    
    def _format_error(self, error_type: ErrorType, msg: str) -> Dict[str, Any]:
        return {
            "status": Status.FAIL.value,
            "source": self.source_name,
            "media": [],
            "error_type": error_type.value,
            "error_msg": msg
        }
