"""
Comprehensive test suite for Nexus Downloader
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Core component tests
from core.task_controller import TaskController, TaskStatus
from core.domain_strategy import DomainStrategy
from core.priority_queue import TaskQueue
from core.rate_limiter import RateLimiter
from core.resource_guard import ResourceGuard

from engines.base_engine import BaseEngine
from engines.fast_engine_v1 import FastEngineV1
from engines.spider_engine_v1 import SpiderEngineV1

from storage.cache import CacheLayer
from storage.deduplicator import Deduplicator
from storage.state_manager import StateManager

from network.proxy_manager import ProxyManager
from network.session_manager import SessionManager

from monitoring.metrics import MetricsCollector
from utils.retry import RetryConfig, retry_async, RetryError
from pipeline.schema_validator import validate


# ==================== TASK CONTROLLER TESTS ====================

@pytest.mark.asyncio
async def test_task_controller_create():
    """Test creating a new task."""
    controller = TaskController()
    task_id = await controller.create_task("https://example.com")
    
    assert task_id is not None
    task = await controller.get_task(task_id)
    assert task.status == TaskStatus.PENDING
    assert task.url == "https://example.com"

@pytest.mark.asyncio
async def test_task_controller_lifecycle():
    """Test complete task lifecycle."""
    controller = TaskController()
    task_id = await controller.create_task("https://example.com")
    
    # Start task
    await controller.start_task(task_id)
    task = await controller.get_task(task_id)
    assert task.status == TaskStatus.RUNNING
    
    # Complete task
    await controller.complete_task(task_id)
    task = await controller.get_task(task_id)
    assert task.status == TaskStatus.COMPLETED

@pytest.mark.asyncio
async def test_task_controller_pause_resume():
    """Test pausing and resuming tasks."""
    controller = TaskController()
    task_id = await controller.create_task("https://example.com")
    
    await controller.start_task(task_id)
    await controller.pause_task(task_id)
    
    task = await controller.get_task(task_id)
    assert task.status == TaskStatus.PAUSED
    
    await controller.resume_task(task_id)
    task = await controller.get_task(task_id)
    assert task.status == TaskStatus.RUNNING

@pytest.mark.asyncio
async def test_task_controller_cancel():
    """Test cancelling a task."""
    controller = TaskController()
    task_id = await controller.create_task("https://example.com")
    
    await controller.cancel_task(task_id)
    task = await controller.get_task(task_id)
    assert task.status == TaskStatus.CANCELLED

@pytest.mark.asyncio
async def test_task_controller_stats():
    """Test task statistics."""
    controller = TaskController()
    
    for i in range(3):
        await controller.create_task(f"https://example.com/{i}")
    
    stats = await controller.get_stats()
    assert stats['total'] == 3
    assert stats['pending'] == 3


# ==================== DOMAIN STRATEGY TESTS ====================

def test_domain_strategy_registration():
    """Test domain strategy registration."""
    strategy = DomainStrategy()
    
    strategy.register_domain_rule("youtube.com", "media_engine")
    assert strategy.get_engine_for_url("https://youtube.com/watch?v=123") == "media_engine"

def test_domain_strategy_pattern_matching():
    """Test pattern-based engine selection."""
    strategy = DomainStrategy()
    
    strategy.register_pattern_rule(r".*\.mp4$", "fast_engine")
    assert strategy.get_engine_for_url("https://example.com/video.mp4") == "fast_engine"

def test_domain_strategy_fallback():
    """Test fallback engine."""
    strategy = DomainStrategy()
    strategy.set_fallback_engine("spider_engine")
    
    # URLs that don't match any rule should use fallback
    result = strategy.get_engine_for_url("https://unknown.com/page")
    assert result == "spider_engine"


# ==================== CACHE LAYER TESTS ====================

def test_cache_layer_set_get():
    """Test cache set and get operations."""
    cache = CacheLayer(ttl_seconds=3600)
    
    data = {"status": "success", "media": []}
    cache.set("https://example.com", data)
    
    retrieved = cache.get("https://example.com")
    assert retrieved == data

def test_cache_layer_ttl_expiration():
    """Test cache TTL expiration."""
    cache = CacheLayer(ttl_seconds=1)
    
    cache.set("https://example.com", {"data": "test"})
    asyncio.run(asyncio.sleep(1.1))
    
    retrieved = cache.get("https://example.com")
    assert retrieved is None


# ==================== DEDUPLICATOR TESTS ====================

def test_deduplicator_basic():
    """Test basic deduplication."""
    dedup = Deduplicator()
    
    assert not dedup.is_duplicate("https://example.com/video1")
    assert dedup.is_duplicate("https://example.com/video1")

def test_deduplicator_different_urls():
    """Test deduplicator with different URLs."""
    dedup = Deduplicator()
    
    assert not dedup.is_duplicate("https://example.com/video1")
    assert not dedup.is_duplicate("https://example.com/video2")


# ==================== PRIORITY QUEUE TESTS ====================

def test_priority_queue_fifo():
    """Test priority queue FIFO ordering."""
    queue = TaskQueue()
    
    from utils.constants import Priority
    
    queue.add({"url": "test1"}, Priority.LOW)
    queue.add({"url": "test2"}, Priority.HIGH)
    
    item1 = queue.get()
    assert item1["url"] == "test2"  # HIGH priority first

def test_priority_queue_empty():
    """Test empty queue."""
    queue = TaskQueue()
    
    item = queue.get(block=False, timeout=1)
    assert item is None


# ==================== METRICS TESTS ====================

def test_metrics_collection():
    """Test metrics recording."""
    metrics = MetricsCollector()
    
    metrics.record_request(
        domain="example.com",
        engine="fast_engine",
        success=True,
        latency_ms=100,
        bytes_downloaded=1024
    )
    
    assert metrics.total_requests == 1
    assert metrics.total_successes == 1
    assert metrics.total_bytes_downloaded == 1024

def test_metrics_summary():
    """Test metrics summary generation."""
    metrics = MetricsCollector()
    
    metrics.record_request("example.com", "fast_engine", True, 100)
    metrics.record_request("example.com", "fast_engine", False, 150)
    
    summary = metrics.get_summary()
    assert summary['total_requests'] == 2
    assert summary['total_successes'] == 1


# ==================== SCHEMA VALIDATION TESTS ====================

def test_schema_validation_success():
    """Test successful schema validation."""
    data = {
        "status": "success",
        "source": "fast_engine_v1",
        "media": [
            {
                "url": "https://example.com/video.mp4",
                "type": "video",
                "quality": "1080p",
                "metadata": {}
            }
        ],
        "error_type": "None",
        "error_msg": None
    }
    
    assert validate(data) == True

def test_schema_validation_failure():
    """Test schema validation failure."""
    data = {
        "status": "invalid_status",
        "source": "engine",
        "media": [],
        "error_type": "None",
        "error_msg": None
    }
    
    assert validate(data) == False


# ==================== RETRY STRATEGY TESTS ====================

@pytest.mark.asyncio
async def test_retry_async_success():
    """Test successful retry with async function."""
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    config = RetryConfig(max_attempts=5, initial_delay_ms=10)
    result = await retry_async(failing_func, config=config)
    
    assert result == "success"
    assert call_count == 3

@pytest.mark.asyncio
async def test_retry_async_exhausted():
    """Test retry exhaustion."""
    async def always_fails():
        raise ValueError("Always fails")
    
    config = RetryConfig(max_attempts=2, initial_delay_ms=10)
    
    with pytest.raises(RetryError):
        await retry_async(always_fails, config=config)


# ==================== PROXY MANAGER TESTS ====================

def test_proxy_manager_initialization():
    """Test proxy manager initialization."""
    manager = ProxyManager()
    stats = manager.get_stats()
    
    assert 'total_proxies' in stats
    assert 'strategy' in stats

def test_proxy_manager_round_robin():
    """Test round-robin proxy selection."""
    manager = ProxyManager()
    manager.proxies = [
        {'url': 'http://proxy1.com', 'weight': 1, 'active': True},
        {'url': 'http://proxy2.com', 'weight': 1, 'active': True},
    ]
    manager.strategy = 'round-robin'
    
    proxy1 = manager.get_next_proxy()
    proxy2 = manager.get_next_proxy()
    
    assert proxy1 != proxy2


# ==================== FAST ENGINE TESTS ====================

@pytest.mark.asyncio
async def test_fast_engine_extraction():
    """Test fast engine extraction."""
    engine = FastEngineV1()
    
    result = await engine.extract("https://example.com")
    
    assert result['status'] == 'success'
    assert result['source'] == 'fast_engine_v1'
    assert isinstance(result['media'], list)

@pytest.mark.asyncio
async def test_fast_engine_error_handling():
    """Test fast engine error handling."""
    engine = FastEngineV1()
    
    result = await engine.extract("https://example.com/error-test")
    
    assert result['status'] == 'fail'
    assert 'error_msg' in result


# ==================== STATE MANAGER TESTS ====================

@pytest.mark.asyncio
async def test_state_manager_save_load():
    """Test state manager save and load."""
    manager = StateManager(state_dir="/tmp/nexus_test_state")
    
    task_data = {"task_id": "123", "status": "pending", "url": "https://example.com"}
    await manager.save_task("123", task_data)
    
    retrieved = await manager.get_task("123")
    assert retrieved == task_data

@pytest.mark.asyncio
async def test_state_manager_metadata():
    """Test state manager metadata."""
    manager = StateManager(state_dir="/tmp/nexus_test_state2")
    
    await manager.set_metadata("last_checkpoint", "2024-01-01T00:00:00")
    value = await manager.get_metadata("last_checkpoint")
    
    assert value == "2024-01-01T00:00:00"


# ==================== INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_full_pipeline_integration():
    """Test full pipeline integration."""
    # Initialize components
    cache = CacheLayer()
    dedup = Deduplicator()
    queue = TaskQueue()
    metrics = MetricsCollector()
    
    url = "https://example.com/test"
    
    # Check dedup
    assert not dedup.is_duplicate(url)
    
    # Check cache
    cache_result = cache.get(url)
    assert cache_result is None
    
    # Record metrics
    metrics.record_request("example.com", "fast_engine", True, 100)
    
    # Check summary
    summary = metrics.get_summary()
    assert summary['total_requests'] == 1
    assert summary['total_successes'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
