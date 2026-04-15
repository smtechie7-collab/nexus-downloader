import asyncio
from typing import Dict, Any
from monitoring.logger import get_logger
from utils.constants import Status, ErrorType
from pipeline.schema_validator import validate
from core.rate_limiter import RateLimiter

logger = get_logger("Router")

class Router:
    def __init__(self):
        self.engines = {}
        self.rate_limiter = RateLimiter() # Injected Rate Limiter
        
    def register_engine(self, domain_pattern: str, engine_instance):
        self.engines[domain_pattern] = engine_instance

    async def route(self, url: str) -> Dict[str, Any]:
        """
        Flow: RateLimiter -> Engine Sandbox -> SchemaValidator
        """
        engine = self.engines.get("default")
        if not engine:
            return self._format_error("router", ErrorType.PARSE_ERROR, "No engine found")

        try:
            # 1. RATE LIMITER (Wait if needed)
            await self.rate_limiter.wait_if_needed(url)
            
            # 2. SANDBOX (Engine Execution)
            output = await engine.extract(url)
            
            # 3. SCHEMA ENFORCEMENT
            if not validate(output):
                return self._format_error(engine.source_name, ErrorType.PARSE_ERROR, "Schema validation failed")
                
            return output
            
        except asyncio.TimeoutError:
            logger.error("Engine timeout", extra={"context": {"url": url}, "error_type": ErrorType.NETWORK_ERROR.value})
            return self._format_error(engine.source_name, ErrorType.NETWORK_ERROR, "Engine timed out")
        except Exception as e:
            logger.critical("Engine crashed in sandbox", extra={"context": {"url": url, "error": str(e)}, "error_type": ErrorType.PARSE_ERROR.value})
            return self._format_error(engine.source_name, ErrorType.PARSE_ERROR, f"Exception: {str(e)}")

    def _format_error(self, source: str, error_type: ErrorType, msg: str) -> Dict[str, Any]:
        return {"status": Status.FAIL.value, "source": source, "media": [], "error_type": error_type.value, "error_msg": msg}