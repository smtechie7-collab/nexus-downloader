import asyncio
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
            
            return {
                "status": Status.SUCCESS.value,
                "source": self.source_name,
                "media": [
                    {
                        # Changed to a highly reliable public test video
                        "url": "https://www.w3schools.com/html/mov_bbb.mp4",
                        "type": "video",
                        "quality": "1080p",
                        "metadata": {"title": "Big_Buck_Bunny_Test"}
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