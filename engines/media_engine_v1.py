import asyncio
import re
import json
import urllib.parse
from typing import Dict, Any, List, Optional
import aiohttp
from engines.base_engine import BaseEngine
from utils.constants import Status, ErrorType
from monitoring.logger import get_logger

logger = get_logger("MediaEngine")

class MediaEngineV1(BaseEngine):
    """
    Specialized media extraction engine for popular platforms.
    Handles: YouTube, Vimeo, Dailymotion, Twitter, etc.
    Best for: Direct API extraction from known sources
    """
    def __init__(self):
        super().__init__()
        self.name = "media_engine"
        self.version = "v1"
        self.timeout = 25
        self._platform_handlers = {
            'youtube.com': self._extract_youtube,
            'youtu.be': self._extract_youtube,
            'vimeo.com': self._extract_vimeo,
            'dailymotion.com': self._extract_dailymotion,
            'twitter.com': self._extract_twitter,
            'x.com': self._extract_twitter,
        }

    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Extracts media using platform-specific handlers.
        Falls back to generic extraction if no handler found.
        """
        try:
            logger.info("Media extraction started", extra={
                "context": {"url": url}
            })
            
            # If the URL already points to a known media file, use it directly.
            platform = self._get_platform(url)
            direct_media = self._extract_direct_media(url)
            if direct_media:
                media = direct_media
                platform = 'direct'
            else:
                # Try platform-specific handler
                if platform and platform in self._platform_handlers:
                    handler = self._platform_handlers[platform]
                    media = await handler(url)
                else:
                    # Generic media extraction
                    media = await self._extract_generic(url)
            
            if not media:
                return self._format_error(
                    ErrorType.PARSE_ERROR,
                    f"No media found for platform: {platform}"
                )
            
            logger.info("Media extraction successful", extra={
                "context": {"url": url, "platform": platform, "media_count": len(media)}
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
            logger.error("Media extraction failed", extra={
                "context": {"url": url, "error": str(e)}
            })
            return self._format_error(ErrorType.PARSE_ERROR, str(e))
    
    def _get_platform(self, url: str) -> Optional[str]:
        """Identifies the platform from URL."""
        for platform in self._platform_handlers.keys():
            if platform in url:
                return platform
        return None
    
    async def _extract_youtube(self, url: str) -> List[Dict]:
        """Extracts video info from YouTube page."""
        headers = self._get_headers()
        media_list = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout, ssl=False) as resp:
                    html = await resp.text()
                    
                    # Look for video ID
                    video_id_patterns = [
                        r'videoDetails["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{11})',
                        r'v=([a-zA-Z0-9_-]{11})',
                    ]
                    
                    video_id = None
                    for pattern in video_id_patterns:
                        match = re.search(pattern, html)
                        if match:
                            video_id = match.group(1)
                            break
                    
                    if video_id:
                        # Use standard YouTube formats
                        media_list.append({
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "type": "video",
                            "quality": "adaptive",
                            "metadata": {
                                "platform": "youtube",
                                "video_id": video_id,
                                "note": "Use yt-dlp or similar for actual download"
                            }
                        })
        except Exception as e:
            logger.error("YouTube extraction error", extra={"context": {"error": str(e)}})
        
        return media_list
    
    def _extract_direct_media(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """Return a direct media record if the URL points to a known file type."""
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or ''
        if '.' not in path:
            return None

        extension = path.rsplit('.', 1)[-1].lower()
        video_exts = {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v'}
        audio_exts = {'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma'}
        document_exts = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv'}

        if extension in video_exts:
            media_type = 'video'
        elif extension in audio_exts:
            media_type = 'audio'
        elif extension in document_exts:
            media_type = 'document'
        else:
            return None

        return [{
            "url": url,
            "type": media_type,
            "quality": "original",
            "metadata": {"platform": "direct", "extension": extension}
        }]

    async def _extract_vimeo(self, url: str) -> List[Dict]:
        """Extracts video info from Vimeo."""
        headers = self._get_headers()
        media_list = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout, ssl=False) as resp:
                    html = await resp.text()
                    
                    # Look for config in HTML
                    config_pattern = r'"config"\s*:\s*(\{[^}]*"files"[^}]*\})'
                    match = re.search(config_pattern, html)
                    
                    if match:
                        try:
                            config = json.loads(match.group(1))
                            if 'files' in config:
                                for quality, file_data in config['files'].items():
                                    if isinstance(file_data, dict) and 'url' in file_data:
                                        media_list.append({
                                            "url": file_data['url'],
                                            "type": "video",
                                            "quality": quality,
                                            "metadata": {"platform": "vimeo"}
                                        })
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.error("Vimeo extraction error", extra={"context": {"error": str(e)}})
        
        return media_list
    
    async def _extract_dailymotion(self, url: str) -> List[Dict]:
        """Extracts video info from Dailymotion."""
        headers = self._get_headers()
        media_list = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout, ssl=False) as resp:
                    html = await resp.text()
                    
                    # Look for qualities info
                    qualities_pattern = r'"qualities"\s*:\s*(\{[^}]+\})'
                    match = re.search(qualities_pattern, html)
                    
                    if match:
                        try:
                            qualities = json.loads(match.group(1))
                            for quality, items in qualities.items():
                                if isinstance(items, list) and len(items) > 0:
                                    media_list.append({
                                        "url": items[0].get('url', ''),
                                        "type": "video",
                                        "quality": quality,
                                        "metadata": {"platform": "dailymotion"}
                                    })
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass
        except Exception as e:
            logger.error("Dailymotion extraction error", extra={"context": {"error": str(e)}})
        
        return media_list
    
    async def _extract_twitter(self, url: str) -> List[Dict]:
        """Extracts media from Twitter/X posts."""
        headers = self._get_headers()
        media_list = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout, ssl=False) as resp:
                    html = await resp.text()
                    
                    # Look for video URLs in various formats
                    video_patterns = [
                        r'https://pbs\.twimg\.com/[^"\s]+\.mp4',
                        r'https://video\.twimg\.com/[^"\s]+',
                    ]
                    
                    for pattern in video_patterns:
                        for match in re.finditer(pattern, html):
                            url = match.group(0)
                            media_list.append({
                                "url": url,
                                "type": "video",
                                "quality": "unknown",
                                "metadata": {"platform": "twitter"}
                            })
        except Exception as e:
            logger.error("Twitter extraction error", extra={"context": {"error": str(e)}})
        
        return media_list
    
    async def _extract_generic(self, url: str) -> List[Dict]:
        """Generic media extraction for unknown platforms."""
        headers = self._get_headers()
        media_list = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout, ssl=False) as resp:
                    html = await resp.text()
                    
                    # Look for any direct media file URLs
                    file_patterns = [
                        r'https?://[^"\s]*\.mp4',
                        r'https?://[^"\s]*\.webm',
                        r'https?://[^"\s]*\.m3u8',
                        r'https?://[^"\s]*\.mp3',
                        r'https?://[^"\s]*\.pdf',
                        r'https?://[^"\s]*\.docx?',
                        r'https?://[^"\s]*\.xlsx?',
                        r'https?://[^"\s]*\.pptx?',
                    ]
                    
                    for pattern in file_patterns:
                        for match in re.finditer(pattern, html):
                            url = match.group(0)
                            media_list.append({
                                "url": url,
                                "type": "video",
                                "quality": "unknown",
                                "metadata": {"platform": "generic"}
                            })
        except Exception as e:
            logger.error("Generic extraction error", extra={"context": {"error": str(e)}})
        
        return media_list
    
    def _get_headers(self) -> Dict[str, str]:
        """Returns media-optimized headers."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def _format_error(self, error_type: ErrorType, msg: str) -> Dict[str, Any]:
        return {
            "status": Status.FAIL.value,
            "source": self.source_name,
            "media": [],
            "error_type": error_type.value,
            "error_msg": msg
        }
