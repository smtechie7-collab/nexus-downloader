import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Callable
from monitoring.logger import get_logger
from downloader.bandwidth_manager import BandwidthManager
from downloader.file_writer import SafeFileWriter
import yaml

logger = get_logger("DownloadManager")

class DownloadManager:
    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)

        self.download_path = self.config['download']['path']
        self.chunk_size = self.config['download']['chunk_size']
        self.max_threads = self.config['resources']['max_threads']

        self.bandwidth_manager = BandwidthManager(config_path)
        self.file_writer = SafeFileWriter(self.download_path)
        os.makedirs(self.download_path, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=self.max_threads)

    def _load_config(self, config_path: str):
        """Load YAML config with support for mocked open() objects."""
        resolved_config_path = Path(config_path)
        if not resolved_config_path.is_absolute():
            resolved_config_path = Path(__file__).resolve().parents[1] / resolved_config_path

        with open(resolved_config_path, 'r') as config_file:
            return yaml.safe_load(config_file)

    def download(self,
                 url: str,
                 filename: str,
                 output_path: Optional[str] = None,
                 task_id: Optional[str] = None,
                 progress_callback: Optional[Callable[[int, int], None]] = None):
        return self.executor.submit(
            self._download_task,
            url,
            filename,
            output_path,
            task_id,
            progress_callback
        )

    def shutdown(self, wait: bool = True):
        """Shutdown the executor, waiting for running downloads to complete."""
        if self.executor:
            self.executor.shutdown(wait=wait)

    def __del__(self):
        try:
            self.shutdown(wait=True)
        except Exception:
            pass

    def _download_task(self,
                       url: str,
                       filename: str,
                       output_path: Optional[str] = None,
                       task_id: Optional[str] = None,
                       progress_callback: Optional[Callable[[int, int], None]] = None):
        base_path = output_path or self.download_path
        os.makedirs(base_path, exist_ok=True)
        writer = SafeFileWriter(base_path)
        target_path = os.path.join(base_path, filename)
        existing_file = writer.get_file_info(target_path)

        if existing_file and existing_file.get('exists'):
            logger.info("File already exists, skipping download", extra={"context": {"file": filename, "task_id": task_id}})
            return True

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*'
            }

            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()

            total_bytes = int(response.headers.get('content-length') or 0)
            downloaded_bytes = 0

            def chunk_generator():
                nonlocal downloaded_bytes
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if not chunk:
                        continue
                    downloaded_bytes += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded_bytes, total_bytes)
                    yield chunk

            success, final_path, error = writer.write_stream_atomic(
                chunk_generator(),
                filename,
                url,
                chunk_size=self.chunk_size
            )

            if success:
                logger.info("Download complete successfully!", extra={
                    "context": {
                        "task_id": task_id,
                        "file": os.path.basename(final_path),
                        "path": final_path,
                        "size": os.path.getsize(final_path)
                    }
                })
                return True
            else:
                logger.error("Download failed during write", extra={
                    "context": {"task_id": task_id, "url": url, "filename": filename, "error": error}
                })
                return False

        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            logger.error("Download blocked", extra={"context": {"task_id": task_id, "url": url, "status": status}})
            return False
        except Exception as e:
            logger.error("Download failed", extra={"context": {"task_id": task_id, "url": url, "error": str(e)}})
            return False