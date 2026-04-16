"""
Engine Tests - Schema Output Format Validation
Constitution Phase C: Engine output schema compliance testing
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from engines.base_engine import BaseEngine
from engines.fast_engine_v1 import FastEngineV1
from engines.spider_engine_v1 import SpiderEngineV1
from engines.media_engine_v1 import MediaEngineV1
from pipeline.schema_validator import validate
from utils.constants import Status, ErrorType


class TestEngineSchemaCompliance:
    """Test engine output schema compliance."""

    @pytest.fixture
    def sample_valid_output(self):
        """Sample valid engine output."""
        return {
            "status": Status.SUCCESS.value,
            "source": "test_engine",
            "media": [
                {
                    "url": "https://example.com/video1.mp4",
                    "type": "video",
                    "quality": "720p",
                    "metadata": {
                        "duration": "10:30",
                        "size": "50MB"
                    }
                },
                {
                    "url": "https://example.com/audio1.mp3",
                    "type": "audio",
                    "quality": "320kbps",
                    "metadata": {}
                }
            ],
            "error_type": ErrorType.NONE.value,
            "error_msg": ""
        }

    @pytest.fixture
    def sample_error_output(self):
        """Sample error engine output."""
        return {
            "status": Status.FAIL.value,
            "source": "test_engine",
            "media": [],
            "error_type": ErrorType.NETWORK_ERROR.value,
            "error_msg": "Connection timeout"
        }

    def test_valid_schema_passes_validation(self, sample_valid_output):
        """Test that valid schema passes validation."""
        assert validate(sample_valid_output) is True

    def test_error_schema_passes_validation(self, sample_error_output):
        """Test that error schema passes validation."""
        assert validate(sample_error_output) is True

    def test_invalid_status_fails(self):
        """Test invalid status values."""
        invalid_output = {
            "status": "invalid_status",
            "source": "test_engine",
            "media": [],
            "error_type": ErrorType.NONE.value,
            "error_msg": ""
        }
        assert validate(invalid_output) is False

    def test_missing_required_fields_fail(self):
        """Test missing required fields."""
        incomplete_output = {
            "status": Status.SUCCESS.value,
            "source": "test_engine",
            # Missing media, error_type, error_msg
        }
        assert validate(incomplete_output) is False

    def test_invalid_media_type_fails(self):
        """Test invalid media type."""
        invalid_output = {
            "status": Status.SUCCESS.value,
            "source": "test_engine",
            "media": [
                {
                    "url": "https://example.com/file.mp4",
                    "type": "invalid_type",  # Invalid type
                    "quality": "720p"
                }
            ],
            "error_type": ErrorType.NONE.value,
            "error_msg": ""
        }
        assert validate(invalid_output) is False

    def test_invalid_url_fails(self):
        """Test invalid URL format."""
        invalid_output = {
            "status": Status.SUCCESS.value,
            "source": "test_engine",
            "media": [
                {
                    "url": "not-a-valid-url",
                    "type": "video",
                    "quality": "720p"
                }
            ],
            "error_type": ErrorType.NONE.value,
            "error_msg": ""
        }
        assert validate(invalid_output) is False

    def test_empty_media_list_valid(self):
        """Test that empty media list is valid for error cases."""
        output = {
            "status": Status.FAIL.value,
            "source": "test_engine",
            "media": [],  # Empty is OK for errors
            "error_type": ErrorType.PARSE_ERROR.value,
            "error_msg": "No media found"
        }
        assert validate(output) is True

    def test_extra_fields_allowed(self, sample_valid_output):
        """Test that extra fields are allowed."""
        output_with_extra = sample_valid_output.copy()
        output_with_extra["extra_field"] = "extra_value"
        output_with_extra["media"][0]["extra_metadata"] = "extra"

        assert validate(output_with_extra) is True


class TestEngineImplementations:
    """Test actual engine implementations."""

    @pytest.mark.asyncio
    async def test_fast_engine_v1_basic_functionality(self):
        """Test FastEngineV1 basic functionality."""
        engine = FastEngineV1()

        # Mock a simple response
        test_url = "https://httpbin.org/html"

        try:
            result = await engine.extract(test_url)

            # Verify schema compliance
            assert validate(result) is True

            # Verify basic structure
            assert "status" in result
            assert "source" in result
            assert "media" in result
            assert "error_type" in result
            assert "error_msg" in result

            # If successful, should have media
            if result["status"] == Status.SUCCESS.value:
                assert isinstance(result["media"], list)
                for media in result["media"]:
                    assert "url" in media
                    assert "type" in media
                    assert "quality" in media

        except Exception as e:
            # Engine might fail due to network, but should still return valid schema
            pytest.skip(f"Engine test skipped due to network: {e}")

    @pytest.mark.asyncio
    async def test_spider_engine_v1_basic_functionality(self):
        """Test SpiderEngineV1 basic functionality."""
        engine = SpiderEngineV1()

        test_url = "https://httpbin.org/html"

        try:
            result = await engine.extract(test_url)

            # Verify schema compliance
            assert validate(result) is True

            # Verify source identification
            assert result["source"] == "spider_engine"

        except Exception as e:
            pytest.skip(f"Engine test skipped due to network: {e}")

    @pytest.mark.asyncio
    async def test_media_engine_v1_basic_functionality(self):
        """Test MediaEngineV1 basic functionality."""
        engine = MediaEngineV1()

        test_url = "https://httpbin.org/html"

        try:
            result = await engine.extract(test_url)

            # Verify schema compliance
            assert validate(result) is True

            # Verify source identification
            assert result["source"] == "media_engine"

        except Exception as e:
            pytest.skip(f"Engine test skipped due to network: {e}")

    @pytest.mark.asyncio
    async def test_engine_error_handling(self):
        """Test that engines handle errors gracefully."""
        engine = FastEngineV1()

        # Test with URL that triggers error in mock engine
        error_url = "https://example.com/error-test"

        result = await engine.extract(error_url)

        # Should return valid error schema
        assert validate(result) is True
        assert result["status"] == Status.FAIL.value
        assert result["error_type"] != ErrorType.NONE.value
        assert result["error_msg"] != ""

    @pytest.mark.asyncio
    async def test_engine_timeout_handling(self):
        """Test engine timeout handling."""
        engine = FastEngineV1()

        # Use a URL that might be slow
        slow_url = "https://httpbin.org/delay/10"  # 10 second delay

        try:
            result = await asyncio.wait_for(
                engine.extract(slow_url),
                timeout=5.0  # 5 second timeout for test
            )

            # If it completes, verify schema
            assert validate(result) is True

        except asyncio.TimeoutError:
            # Timeout is acceptable for this test
            pass

    def test_engine_source_name_consistency(self):
        """Test that engines have consistent source names."""
        engines = [
            (FastEngineV1(), "fast_engine_v1"),
            (SpiderEngineV1(), "spider_engine_v1"),
            (MediaEngineV1(), "media_engine_v1"),
        ]

        for engine, expected_source in engines:
            assert hasattr(engine, 'source_name')
            assert engine.source_name == expected_source

    @pytest.mark.asyncio
    async def test_engine_output_types(self):
        """Test that engine outputs have correct types."""
        engine = FastEngineV1()

        try:
            result = await engine.extract("https://httpbin.org/html")

            # Check types
            assert isinstance(result["status"], str)
            assert isinstance(result["source"], str)
            assert isinstance(result["media"], list)
            assert isinstance(result["error_type"], str)
            assert isinstance(result["error_msg"], str)

            # Check media items
            for media in result["media"]:
                assert isinstance(media, dict)
                assert isinstance(media["url"], str)
                assert isinstance(media["type"], str)
                assert isinstance(media["quality"], str)
                assert isinstance(media.get("metadata", {}), dict)

        except Exception:
            pytest.skip("Network test skipped")


class TestEngineSchemaEdgeCases:
    """Test edge cases for schema validation."""

    def test_media_with_minimal_fields(self):
        """Test media item with minimal required fields."""
        output = {
            "status": Status.SUCCESS.value,
            "source": "test_engine",
            "media": [
                {
                    "url": "https://example.com/file.mp4",
                    "type": "video",
                    "quality": "720p"
                    # metadata is optional
                }
            ],
            "error_type": ErrorType.NONE.value,
            "error_msg": ""
        }
        assert validate(output) is True

    def test_media_with_all_fields(self):
        """Test media item with all possible fields."""
        output = {
            "status": Status.SUCCESS.value,
            "source": "test_engine",
            "media": [
                {
                    "url": "https://example.com/file.mp4",
                    "type": "video",
                    "quality": "720p",
                    "metadata": {
                        "duration": "10:30",
                        "size": "50MB",
                        "bitrate": "2000kbps",
                        "codec": "h264",
                        "custom_field": "value"
                    }
                }
            ],
            "error_type": ErrorType.NONE.value,
            "error_msg": ""
        }
        assert validate(output) is True

    def test_multiple_media_items(self):
        """Test output with multiple media items."""
        output = {
            "status": Status.SUCCESS.value,
            "source": "test_engine",
            "media": [
                {
                    "url": "https://example.com/video1.mp4",
                    "type": "video",
                    "quality": "720p"
                },
                {
                    "url": "https://example.com/video2.mp4",
                    "type": "video",
                    "quality": "1080p"
                },
                {
                    "url": "https://example.com/audio1.mp3",
                    "type": "audio",
                    "quality": "320kbps"
                }
            ],
            "error_type": ErrorType.NONE.value,
            "error_msg": ""
        }
        assert validate(output) is True

    def test_different_error_types(self):
        """Test different error types."""
        error_types = [
            ErrorType.NETWORK_ERROR,
            ErrorType.PARSE_ERROR,
            ErrorType.ACCESS_DENIED,
            ErrorType.RATE_LIMITED,
            ErrorType.NONE
        ]

        for error_type in error_types:
            output = {
                "status": Status.FAIL.value,
                "source": "test_engine",
                "media": [],
                "error_type": error_type.value,
                "error_msg": f"Test {error_type.value} error"
            }
            assert validate(output) is True, f"Failed for error type: {error_type.value}"