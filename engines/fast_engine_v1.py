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
            "error_msg": None
        }