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

    try:
        async with aiohttp.ClientSession() as session:
            # HEAD request doesn't download the file, just gets the metadata
            async with session.head(url, headers=headers, allow_redirects=True, timeout=10) as response:
                if response.status >= 400:
                    logger.warning("Content Validator rejected URL: Bad Status", extra={"context": {"url": url, "status": response.status}})
                    return False
                
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Basic MIME type sanity check
                if expected_type == 'video' and 'video' not in content_type and 'octet-stream' not in content_type:
                     logger.warning("Content Validator rejected URL: MIME mismatch", extra={"context": {"url": url, "got": content_type, "expected": expected_type}})
                     return False
                     
                return True
                
    except Exception as e:
        logger.error("Content validation failed (Network Issue)", extra={"context": {"url": url, "error": str(e)}})
        return False