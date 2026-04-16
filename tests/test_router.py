"""
Router Tests - Fallback Chain Testing
Constitution Phase C: Router fallback chain validation
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from core.router import Router
from core.domain_strategy import DomainStrategy
from utils.constants import Status, ErrorType


class MockEngine:
    """Mock engine for testing."""

    def __init__(self, name: str, should_fail: bool = False, delay: float = 0.1):
        self.source_name = name
        self.should_fail = should_fail
        self.delay = delay

    async def extract(self, url: str):
        await asyncio.sleep(self.delay)
        if self.should_fail:
            raise Exception(f"Engine {self.source_name} failed")
        return {
            "status": Status.SUCCESS.value,
            "source": self.source_name,
            "media": [{"url": f"{url}/media1.mp4", "type": "video", "quality": "720p"}],
            "error_type": ErrorType.NONE.value,
            "error_msg": ""
        }


@pytest.fixture
def mock_domain_strategy():
    """Mock domain strategy for testing."""
    strategy = Mock(spec=DomainStrategy)

    # Mock fallback chain responses
    strategy.get_engine_fallback_chain.side_effect = lambda url: {
        "https://youtube.com/video": ["media_engine", "stealth_engine", "fast_engine"],
        "https://twitter.com/tweet": ["spider_engine", "stealth_engine", "fast_engine"],
        "https://example.com/page": ["fast_engine", "spider_engine", "headless_engine"],
        "https://fail-all.com": ["failing_engine1", "failing_engine2", "failing_engine3"]
    }.get(url, ["fast_engine"])

    strategy.register_engine = Mock()
    return strategy


@pytest.fixture
def router_with_mocks(mock_domain_strategy):
    """Router with mocked domain strategy."""
    with patch('core.router.DomainStrategy', return_value=mock_domain_strategy):
        router = Router()
        return router


@pytest.mark.asyncio
async def test_router_fallback_chain_success_first():
    """Test successful routing with first engine in chain."""
    router = Router()

    # Register engines
    engine1 = MockEngine("fast_engine", should_fail=False)
    engine2 = MockEngine("spider_engine", should_fail=False)  # Won't be used

    router.register_engine("fast_engine", engine1)
    router.register_engine("spider_engine", engine2)

    # Mock domain strategy to return chain starting with fast_engine
    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=["fast_engine", "spider_engine"]):
        result = await router.route("https://example.com/video")

        assert result["status"] == Status.SUCCESS.value
        assert result["source"] == "fast_engine"
        assert len(result["media"]) == 1


@pytest.mark.asyncio
async def test_router_fallback_chain_second_engine():
    """Test fallback to second engine when first fails."""
    router = Router()

    # Register engines - first fails, second succeeds
    engine1 = MockEngine("media_engine", should_fail=True)
    engine2 = MockEngine("stealth_engine", should_fail=False)

    router.register_engine("media_engine", engine1)
    router.register_engine("stealth_engine", engine2)

    # Mock domain strategy
    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=["media_engine", "stealth_engine"]):
        result = await router.route("https://youtube.com/video")

        assert result["status"] == Status.SUCCESS.value
        assert result["source"] == "stealth_engine"  # Should use fallback
        assert len(result["media"]) == 1


@pytest.mark.asyncio
async def test_router_fallback_chain_all_fail():
    """Test when all engines in chain fail."""
    router = Router()

    # Register failing engines
    engine1 = MockEngine("failing_engine1", should_fail=True)
    engine2 = MockEngine("failing_engine2", should_fail=True)

    router.register_engine("failing_engine1", engine1)
    router.register_engine("failing_engine2", engine2)

    # Mock domain strategy
    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=["failing_engine1", "failing_engine2"]):
        result = await router.route("https://fail-all.com")

        assert result["status"] == Status.FAIL.value
        assert result["error_type"] == ErrorType.PARSE_ERROR.value
        assert "All engines failed" in result["error_msg"]


@pytest.mark.asyncio
async def test_router_no_engines_available():
    """Test routing when no engines are registered."""
    router = Router()

    # Mock empty chain
    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=[]):
        result = await router.route("https://example.com")

        assert result["status"] == Status.FAIL.value
        assert result["error_type"] == ErrorType.PARSE_ERROR.value
        assert "No engines available" in result["error_msg"]


@pytest.mark.asyncio
async def test_router_engine_not_registered():
    """Test when engine in chain is not registered."""
    router = Router()

    # Register only one engine
    engine1 = MockEngine("fast_engine", should_fail=False)
    router.register_engine("fast_engine", engine1)

    # Mock chain with unregistered engine first
    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=["unregistered_engine", "fast_engine"]):
        result = await router.route("https://example.com")

        # Should skip unregistered and use registered engine
        assert result["status"] == Status.SUCCESS.value
        assert result["source"] == "fast_engine"


@pytest.mark.asyncio
async def test_router_timeout_handling():
    """Test timeout handling in router."""
    router = Router()

    # Mock engine that times out
    async def timeout_extract(url):
        await asyncio.sleep(30)  # Long delay to simulate timeout

    engine = Mock()
    engine.extract = timeout_extract
    engine.source_name = "timeout_engine"

    router.register_engine("timeout_engine", engine)

    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=["timeout_engine"]):
        # This should timeout and return error
        result = await router.route("https://example.com")

        assert result["status"] == Status.FAIL.value
        assert result["error_type"] == ErrorType.NETWORK_ERROR.value
        assert "timed out" in result["error_msg"].lower()


@pytest.mark.asyncio
async def test_router_different_domains_different_chains():
    """Test that different domains get different fallback chains."""
    router = Router()

    # Register multiple engines
    engines = {
        "media_engine": MockEngine("media_engine", should_fail=False),
        "spider_engine": MockEngine("spider_engine", should_fail=False),
        "fast_engine": MockEngine("fast_engine", should_fail=False),
    }

    for name, engine in engines.items():
        router.register_engine(name, engine)

    # Test YouTube URL (should prefer media_engine)
    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=["media_engine", "stealth_engine", "fast_engine"]):
        result = await router.route("https://youtube.com/video")
        assert result["source"] == "media_engine"

    # Test Twitter URL (should prefer spider_engine)
    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=["spider_engine", "stealth_engine", "fast_engine"]):
        result = await router.route("https://twitter.com/tweet")
        assert result["source"] == "spider_engine"


@pytest.mark.asyncio
async def test_router_rate_limiter_integration():
    """Test that router properly integrates with rate limiter."""
    router = Router()

    engine = MockEngine("fast_engine", should_fail=False, delay=0.01)
    router.register_engine("fast_engine", engine)

    with patch.object(router.domain_strategy, 'get_engine_fallback_chain',
                     return_value=["fast_engine"]):
        # Mock rate limiter to add delay
        with patch.object(router.rate_limiter, 'wait_if_needed', new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = None  # No actual delay

            result = await router.route("https://example.com")

            # Verify rate limiter was called
            mock_wait.assert_called_once_with("https://example.com")
            assert result["status"] == Status.SUCCESS.value