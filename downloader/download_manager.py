import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
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
        config_file = open(config_path, 'r')
        try:
            if hasattr(config_file, '__enter__'):
                with config_file as f:
                    return yaml.safe_load(f)
            return yaml.safe_load(config_file)
        finally:
            if not hasattr(config_file, '__enter__') and hasattr(config_file, 'close'):
                try:
                    config_file.close()
                except Exception:
                    pass

    def download(self, url: str, filename: str):
        return self.executor.submit(self._download_task, url, filename)

    def shutdown(self, wait: bool = True):
        """Shutdown the executor, waiting for running downloads to complete."""
        if self.executor:
            self.executor.shutdown(wait=wait)

    def __del__(self):
        try:
            self.shutdown(wait=True)
        except Exception:
            pass

    def _download_task(self, url: str, filename: str):
        target_path = os.path.join(self.download_path, filename)
        existing_file = self.file_writer.get_file_info(target_path)

        if existing_file and existing_file.get('exists'):
            logger.info("File already exists, skipping download", extra={"context": {"file": filename}})
            return

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*'
            }

            resume_prefix = b''
            if existing_file and existing_file.get('size', 0) > 0:
                try:
                    with open(target_path, 'rb') as existing:
                        resume_prefix = existing.read()
                    headers['Range'] = f"bytes={existing_file['size']}-"
                    logger.info("Attempting resume", extra={"context": {"file": filename, "existing_size": existing_file['size']}})
                except Exception:
                    logger.warning("Failed to read existing partial file", extra={"context": {"file": filename}})

            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()

            chunks = [resume_prefix] if resume_prefix else []
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    chunk_start_time = time.time()
                    chunks.append(chunk)
                    self.bandwidth_manager.throttle(len(chunk), chunk_start_time)

            content = b''.join(chunks)
            success, final_path, error = self.file_writer.write_atomic(content, filename, url)

            if success:
                logger.info("Download complete successfully!", extra={
                    "context": {"file": os.path.basename(final_path), "path": final_path, "size": len(content)}
                })
            else:
                logger.error("Download failed during write", extra={
                    "context": {"url": url, "filename": filename, "error": error}
                })

        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            logger.error("Download blocked", extra={"context": {"url": url, "status": status}})
        except Exception as e:
            logger.error("Download failed", extra={"context": {"url": url, "error": str(e)}})