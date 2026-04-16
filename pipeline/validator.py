import aiohttp
from typing import Dict, Any
from monitoring.logger import get_logger

logger = get_logger("ContentValidator")

async def validate_media(media_item: Dict[str, Any]) -> bool:
    """
    Makes a lightweight async HEAD request to verify file existence.
    """
    url = str(media_item['url'])
    expected_type = media_item.get('type', 'other')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    def _mime_allowed(content_type: str, expected: str) -> bool:
        if not content_type:
            return True

        if expected == 'video':
            return 'video' in content_type or 'octet-stream' in content_type
        if expected == 'audio':
            return 'audio' in content_type or 'mpeg' in content_type or 'ogg' in content_type
        if expected == 'image':
            return 'image' in content_type
        if expected == 'document':
            return any(token in content_type for token in [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument',
                'text/plain',
                'application/octet-stream'
            ])
        return True

    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url, headers=headers, allow_redirects=True, timeout=10) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '').lower()
            except Exception:
                # Some servers reject HEAD requests; fallback to GET to validate availability.
                async with session.get(url, headers=headers, allow_redirects=True, timeout=10) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '').lower()
                    await response.content.read(1)

            if status >= 400:
                logger.warning("Content Validator rejected URL: Bad Status", extra={"context": {"url": url, "status": status}})
                return False

            if not _mime_allowed(content_type, expected_type):
                logger.warning("Content Validator rejected URL: MIME mismatch", extra={"context": {"url": url, "got": content_type, "expected": expected_type}})
                return False

            return True
    except Exception as e:
        logger.error("Content validation failed (Network Issue)", extra={"context": {"url": url, "error": str(e)}})
        return False