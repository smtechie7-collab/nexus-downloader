import asyncio
import urllib.parse
from typing import Dict, Any
from engines.base_engine import BaseEngine
from utils.constants import Status, ErrorType

class FastEngineV1(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "fast_engine"
        self.version = "v1"

    async def extract(self, url: str) -> Dict[str, Any]:
        """Mock extraction simulating a fast API/Regex scrape."""
        await asyncio.sleep(0.5)  # Simulate network call
        
        try:
            # Simulating basic parsing logic (Sandbox Test)
            if "error" in url:
                raise ValueError("Simulated parsing error")

            parsed = urllib.parse.urlparse(url)
            path = parsed.path or ''
            extension = path.rsplit('.', 1)[-1].lower() if '.' in path else ''
            media_type = 'video' if extension in {'mp4', 'webm', 'mkv', 'mov', 'avi', 'flv'} else 'audio' if extension in {'mp3', 'wav', 'flac', 'aac', 'ogg'} else 'document' if extension in {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv'} else 'other'
            media_url = url if extension else "https://www.w3schools.com/html/mov_bbb.mp4"

            return {
                "status": Status.SUCCESS.value,
                "source": self.source_name,
                "media": [
                    {
                        "url": media_url,
                        "type": media_type,
                        "quality": "original" if extension else "1080p",
                        "metadata": {"title": path.rsplit('/', 1)[-1] or "download"}
                    }
                ],
                "error_type": ErrorType.NONE.value,
                "error_msg": ""
            }
        except Exception as e:
            # Handle errors gracefully and return error response
            return {
                "status": Status.FAIL.value,
                "source": self.source_name,
                "media": [],
                "error_type": ErrorType.PARSE_ERROR.value,
                "error_msg": str(e)
            }