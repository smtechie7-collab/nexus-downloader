from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from utils.constants import ErrorType, Status

class MediaItem(BaseModel):
    url: HttpUrl
    type: str = Field(..., pattern="^(video|audio|image|document|other)$")
    quality: str
    metadata: Dict[str, Any] = {}

class StandardDataFormat(BaseModel):
    status: Status
    source: str
    media: List[MediaItem]
    error_type: ErrorType
    error_msg: Optional[str] = None

def validate(data: dict) -> bool:
    """Strictly validates engine output against the constitution schema."""
    try:
        StandardDataFormat(**data)
        return True
    except Exception as e:
        from monitoring.logger import get_logger
        logger = get_logger("SchemaValidator")
        logger.error("Schema validation failed", extra={"context": {"error": str(e)}})
        return False