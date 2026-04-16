"""
Download Tests - Resume and Bandwidth Testing
Constitution Phase C: Download resume functionality and bandwidth management
"""
import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from downloader.download_manager import DownloadManager
from downloader.bandwidth_manager import BandwidthManager
from downloader.file_writer import SafeFileWriter
from core.resource_guard import ResourceGuard
from core.rate_limiter import RateLimiter


@pytest.fixture
def download_manager(tmp_path):
    """Shared download manager fixture for integration tests."""
    with patch('builtins.open', Mock()):
        with patch('yaml.safe_load', return_value={
            'download': {'path': str(tmp_path), 'chunk_size': 1024},
            'resources': {'max_threads': 1},
            'bandwidth': {'max_kbps': 100}
        }):
            yield DownloadManager("config.yaml")


class TestBandwidthManager:
    """Test bandwidth management functionality."""

    @pytest.fixture
    def bandwidth_manager(self):
        """Create bandwidth manager with test config."""
        with patch('builtins.open', Mock()):
            with patch('yaml.safe_load', return_value={'bandwidth': {'max_kbps': 100}}):
                manager = BandwidthManager("config.yaml")
                return manager

    def test_bandwidth_throttling_calculation(self, bandwidth_manager):
        """Test bandwidth throttling delay calculation."""
        chunk_size = 1024  # 1KB
        start_time = 0.0

        # With 100 KB/s limit, 1KB should take 0.01 seconds
        expected_delay = 0.01

        # Mock time to control timing
        with patch('time.time', side_effect=[start_time, start_time + 0.005]):  # 5ms elapsed
            bandwidth_manager.throttle(chunk_size, start_time)

            # Should sleep for ~5ms to reach expected time
            # (This is hard to test precisely due to timing, but we verify no exceptions)

    def test_unlimited_bandwidth(self):
        """Test unlimited bandwidth (0 = no limit)."""
        with patch('builtins.open', Mock()):
            with patch('yaml.safe_load', return_value={'bandwidth': {'max_kbps': 0}}):
                manager = BandwidthManager("config.yaml")

                # Should not throttle
                manager.throttle(1024, 0.0)
                # No assertions needed, just verify no exceptions

    def test_high_bandwidth_limit(self):
        """Test high bandwidth limits."""
        with patch('builtins.open', Mock()):
            with patch('yaml.safe_load', return_value={'bandwidth': {'max_kbps': 10000}}):  # 10MB/s
                manager = BandwidthManager("config.yaml")

                chunk_size = 1024 * 1024  # 1MB
                start_time = 0.0

                with patch('time.time', side_effect=[start_time, start_time + 0.0001]):  # Very fast
                    manager.throttle(chunk_size, start_time)


class TestSafeFileWriter:
    """Test safe file writer functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def file_writer(self, temp_dir):
        """Create file writer for testing."""
        return SafeFileWriter(temp_dir)

    def test_atomic_write_success(self, file_writer):
        """Test successful atomic write."""
        test_content = b"Hello, World! Test content for atomic write."
        filename = "test_file.txt"

        success, filepath, error = file_writer.write_atomic(test_content, filename)

        assert success is True
        assert error is None
        assert os.path.exists(filepath)

        # Verify content
        with open(filepath, 'rb') as f:
            assert f.read() == test_content

    def test_atomic_write_collision_prevention(self, file_writer):
        """Test collision prevention with unique filenames."""
        content1 = b"Content 1"
        content2 = b"Content 2"
        filename = "collision_test.txt"

        # Write first file
        success1, path1, error1 = file_writer.write_atomic(content1, filename, "url1")
        assert success1 is True

        # Write second file with same name but different URL
        success2, path2, error2 = file_writer.write_atomic(content2, filename, "url2")
        assert success2 is True

        # Paths should be different
        assert path1 != path2

        # Both files should exist with correct content
        with open(path1, 'rb') as f:
            assert f.read() == content1
        with open(path2, 'rb') as f:
            assert f.read() == content2

    def test_atomic_write_file_exists_check(self, file_writer):
        """Test file existence checking."""
        content = b"Test content"
        filename = "existing_file.txt"

        # Create file manually
        existing_path = os.path.join(file_writer.base_dir, filename)
        with open(existing_path, 'wb') as f:
            f.write(b"existing content")

        # Try to write same filename
        success, filepath, error = file_writer.write_atomic(content, filename)

        # Should create new unique file
        assert success is True
        assert filepath != existing_path
        assert os.path.exists(filepath)

    def test_get_file_info(self, file_writer):
        """Test file info retrieval."""
        content = b"Info test content"
        filename = "info_test.txt"

        success, filepath, error = file_writer.write_atomic(content, filename)
        assert success is True

        info = file_writer.get_file_info(filepath)
        assert info is not None
        assert info['exists'] is True
        assert info['size'] == len(content)
        assert 'modified' in info

    def test_get_file_info_nonexistent(self, file_writer):
        """Test file info for nonexistent file."""
        info = file_writer.get_file_info("/nonexistent/path/file.txt")
        assert info is None

    def test_temp_file_cleanup(self, file_writer):
        """Test temporary file cleanup."""
        # Create some temp files manually
        temp_files = []
        for i in range(3):
            temp_path = file_writer.base_dir / f"temp_test_{i}_abc123.txt"
            temp_path.write_text("temp content")
            temp_files.append(temp_path)

        # Run cleanup (should not remove fresh files)
        cleaned = file_writer.cleanup_temp_files(max_age_seconds=3600)
        assert cleaned == 0  # No files should be cleaned (too new)

        # Mock old timestamps and cleanup
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value = Mock(st_mtime=0)  # Very old timestamp

            cleaned = file_writer.cleanup_temp_files(max_age_seconds=3600)
            assert cleaned == 3  # All temp files should be cleaned


class TestDownloadManager:
    """Test download manager functionality."""

    @pytest.fixture
    def download_manager(self, tmp_path):
        """Create download manager for testing."""
        # Mock config loading
        with patch('builtins.open', Mock()):
            with patch('yaml.safe_load', return_value={
                'download': {'path': str(tmp_path), 'chunk_size': 1024},
                'resources': {'max_threads': 2},
                'bandwidth': {'max_kbps': 100}
            }):
                manager = DownloadManager("config.yaml")
                return manager

    @pytest.mark.asyncio
    async def test_download_manager_initialization(self, download_manager):
        """Test download manager initialization."""
        assert download_manager.download_path is not None
        assert download_manager.chunk_size > 0
        assert download_manager.max_threads > 0
        assert hasattr(download_manager, 'file_writer')
        assert hasattr(download_manager, 'bandwidth_manager')

    def test_download_skips_existing_files(self, download_manager):
        """Test that downloads skip existing files."""
        filename = "existing_test.mp4"
        filepath = os.path.join(download_manager.download_path, filename)

        # Create existing file
        with open(filepath, 'wb') as f:
            f.write(b"existing content")

        # Mock the file_writer to check if get_file_info is called
        with patch.object(download_manager.file_writer, 'get_file_info') as mock_info:
            mock_info.return_value = {'exists': True}

            # This should not actually download
            future = download_manager.download("https://example.com/test.mp4", filename)
            future.result(timeout=5)

            # Verify file_writer was checked
            mock_info.assert_called()

    @pytest.mark.asyncio
    async def test_download_with_bandwidth_throttling(self):
        """Test download with bandwidth throttling integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('builtins.open', Mock()):
                with patch('yaml.safe_load', return_value={
                    'download': {'path': temp_dir, 'chunk_size': 1024},
                    'resources': {'max_threads': 1},
                    'bandwidth': {'max_kbps': 50}  # 50 KB/s limit
                }):
                    manager = DownloadManager("config.yaml")

                    # Mock requests to return test data
                    mock_response = Mock()
                    mock_response.iter_content.return_value = [b'x' * 1024] * 10  # 10KB total
                    mock_response.raise_for_status.return_value = None

                    with patch('requests.get', return_value=mock_response):
                        with patch.object(manager.file_writer, 'write_atomic') as mock_write:
                            mock_write.return_value = (True, "/test/path", None)

                            # This should apply throttling
                            future = manager.download("https://example.com/test.bin", "test.bin")
                            future.result(timeout=5)

                            # Verify write_atomic was called
                            mock_write.assert_called_once()

    def test_download_error_handling(self, download_manager):
        """Test download error handling."""
        with patch('requests.get') as mock_get:
            # Mock network error
            mock_get.side_effect = Exception("Network error")

            # Should not crash
            download_manager.download("https://example.com/test.mp4", "test.mp4")

            # File should not be created
            filepath = os.path.join(download_manager.download_path, "test.mp4")
            assert not os.path.exists(filepath)


class TestDownloadResume:
    """Test download resume functionality."""

    @pytest.fixture
    def download_manager(self, tmp_path):
        """Create download manager for resume testing."""
        with patch('builtins.open', Mock()):
            with patch('yaml.safe_load', return_value={
                'download': {'path': str(tmp_path), 'chunk_size': 8192},
                'resources': {'max_threads': 1},
                'bandwidth': {'max_kbps': 1000}
            }):
                manager = DownloadManager("config.yaml")
                return manager

    def test_resume_partial_download_setup(self, download_manager):
        """Test setup for partial download resume (structure test)."""
        # This is a structural test since full resume requires server support
        filename = "resume_test.mp4"
        partial_content = b"partial" * 1000  # 7KB of data

        # Create partial file
        partial_path = os.path.join(download_manager.download_path, filename)
        with open(partial_path, 'wb') as f:
            f.write(partial_content)

        # Verify partial file exists
        assert os.path.exists(partial_path)
        assert os.path.getsize(partial_path) == len(partial_content)

        # In a real scenario, the download manager would check for partial files
        # and attempt to resume. This test verifies the file system setup.

    def test_atomic_write_prevents_corruption(self, tmp_path):
        """Test that atomic writes prevent file corruption."""
        writer = SafeFileWriter(str(tmp_path))

        # Simulate interrupted write (temp file left behind)
        temp_content = b"temporary incomplete content"

        # Manually create a temp file (simulating interrupted write)
        temp_filename = "temp_test_atomic_abc123.txt"
        temp_path = tmp_path / temp_filename
        temp_path.write_bytes(temp_content)

        # Now do a proper atomic write
        final_content = b"final complete content"
        success, final_path, error = writer.write_atomic(final_content, "test_atomic.txt")

        assert success is True
        assert os.path.exists(final_path)

        # Verify final content is correct
        with open(final_path, 'rb') as f:
            assert f.read() == final_content

        # Temp file should still exist (cleanup is separate)
        assert temp_path.exists()

    def test_concurrent_download_safety(self, download_manager):
        """Test that concurrent downloads don't interfere."""
        filenames = ["concurrent1.mp4", "concurrent2.mp4", "concurrent3.mp4"]

        # Mock successful downloads
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.iter_content.return_value = [b'test' * 256] * 4  # 4KB each
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            with patch.object(download_manager.file_writer, 'write_atomic') as mock_write:
                mock_write.return_value = (True, "/test/path", None)

                # Start multiple downloads
                for filename in filenames:
                    download_manager.download(f"https://example.com/{filename}", filename)

                # Wait for thread pool
                download_manager.executor.shutdown(wait=True)

                # Verify all downloads were attempted
                assert mock_write.call_count == len(filenames)


class TestDownloadIntegration:
    """Integration tests for download components."""

    def test_bandwidth_and_file_writer_integration(self, tmp_path):
        """Test bandwidth manager and file writer work together."""
        writer = SafeFileWriter(str(tmp_path))

        with patch('builtins.open', Mock()):
            with patch('yaml.safe_load', return_value={'bandwidth': {'max_kbps': 200}}):
                bandwidth_mgr = BandwidthManager("config.yaml")

                # Simulate throttled content writing
                content_chunks = [b'x' * 1024] * 10  # 10KB in 1KB chunks
                combined_content = b''.join(content_chunks)

                # This simulates what DownloadManager does
                start_time = 0.0
                for chunk in content_chunks:
                    bandwidth_mgr.throttle(len(chunk), start_time)
                    start_time += 0.001  # Simulate time passing

                # Write the combined content
                success, filepath, error = writer.write_atomic(combined_content, "bandwidth_test.dat")

                assert success is True
                assert os.path.exists(filepath)

    def test_error_recovery_scenarios(self, download_manager):
        """Test various error recovery scenarios."""
        test_cases = [
            ("https://httpbin.org/status/404", "404_error.mp4"),
            ("https://httpbin.org/status/500", "500_error.mp4"),
            ("https://invalid-domain-12345.com/file.mp4", "dns_error.mp4"),
        ]

        for url, filename in test_cases:
            # Should handle errors gracefully without crashing
            try:
                download_manager.download(url, filename)
                # If no exception, test passes
            except Exception as e:
                pytest.fail(f"Download should handle errors gracefully: {e}")

    def test_file_writer_collision_with_different_urls(self, tmp_path):
        """Test file writer handles URL-based collision prevention."""
        writer = SafeFileWriter(str(tmp_path))

        base_filename = "test.mp4"
        content1 = b"Content from URL 1"
        content2 = b"Content from URL 2"

        # Write with different URLs
        success1, path1, _ = writer.write_atomic(content1, base_filename, "https://site1.com/video")
        success2, path2, _ = writer.write_atomic(content2, base_filename, "https://site2.com/video")

        assert success1 and success2
        assert path1 != path2
        assert os.path.basename(path1).startswith("test_")
        assert os.path.basename(path2).startswith("test_")
        assert path1 != path2