from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseEngine(ABC):
    def __init__(self):
        self.name = "base_engine"
        self.version = "v0"

    @property
    def source_name(self):
        return f"{self.name}_{self.version}"

    @abstractmethod
    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Must return standard data format only.
        Async for highly concurrent engine calls.
        """
        pass