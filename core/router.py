import asyncio
from typing import Dict, Any
from monitoring.logger import get_logger
from utils.constants import Status, ErrorType
from pipeline.schema_validator import validate
from core.rate_limiter import RateLimiter
from core.domain_strategy import DomainStrategy

logger = get_logger("Router")

class Router:
    ENGINE_TIMEOUT_SECONDS = 10

    def __init__(self):
        self.engines = {}
        self.rate_limiter = RateLimiter()  # Injected Rate Limiter
        self.domain_strategy = DomainStrategy()

    def register_engine(self, engine_name: str, engine_instance):
        """Register engine by name for DomainStrategy lookup."""
        self.engines[engine_name] = engine_instance
        self.domain_strategy.register_engine(engine_name, engine_instance)

    async def route(self, url: str) -> Dict[str, Any]:
        """
        Flow: DomainStrategy -> RateLimiter -> Engine Sandbox (with Fallback) -> SchemaValidator
        """
        # Get fallback chain from DomainStrategy
        engine_chain = self.domain_strategy.get_engine_fallback_chain(url)

        if not engine_chain:
            return self._format_error("router", ErrorType.PARSE_ERROR, "No engines available")

        # Try engines in fallback chain
        timeout_occurred = False
        for engine_name in engine_chain:
            engine = self.engines.get(engine_name)
            if not engine:
                logger.warning("Engine not registered", extra={"context": {"engine_name": engine_name}})
                continue

            try:
                # 1. RATE LIMITER (Wait if needed)
                await self.rate_limiter.wait_if_needed(url)

                # 2. SANDBOX (Engine Execution)
                logger.info("Trying engine", extra={"context": {"url": url, "engine": engine_name}})
                output = await asyncio.wait_for(engine.extract(url), timeout=self.ENGINE_TIMEOUT_SECONDS)

                # 3. SCHEMA ENFORCEMENT
                if not validate(output):
                    logger.warning("Schema validation failed, trying next engine",
                                 extra={"context": {"url": url, "engine": engine_name}})
                    continue  # Try next engine in chain

                logger.info("Engine succeeded", extra={"context": {"url": url, "engine": engine_name}})
                return output

            except asyncio.TimeoutError:
                timeout_occurred = True
                logger.warning("Engine timeout, trying next engine",
                             extra={"context": {"url": url, "engine": engine_name, "error_type": ErrorType.NETWORK_ERROR.value}})
                continue  # Try next engine
            except Exception as e:
                logger.warning("Engine failed, trying next engine",
                             extra={"context": {"url": url, "engine": engine_name, "error": str(e), "error_type": ErrorType.PARSE_ERROR.value}})
                continue  # Try next engine

        # All engines in chain failed
        if timeout_occurred:
            return self._format_error("router", ErrorType.NETWORK_ERROR, f"Timed out while processing URL: {url}")
        return self._format_error("router", ErrorType.PARSE_ERROR, f"All engines failed for URL: {url}")

    def _format_error(self, source: str, error_type: ErrorType, msg: str) -> Dict[str, Any]:
        return {"status": Status.FAIL.value, "source": source, "media": [], "error_type": error_type.value, "error_msg": msg}