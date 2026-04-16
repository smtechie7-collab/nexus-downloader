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
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.download_path = self.config['download']['path']
        self.chunk_size = self.config['download']['chunk_size']
        self.max_threads = self.config['resources']['max_threads']
        
        self.bandwidth_manager = BandwidthManager(config_path)
        self.file_writer = SafeFileWriter(self.download_path)
        os.makedirs(self.download_path, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=self.max_threads)

    def download(self, url: str, filename: str):
        self.executor.submit(self._download_task, url, filename)

    def _download_task(self, url: str, filename: str):
        # Check if file already exists
        existing_file = self.file_writer.get_file_info(os.path.join(self.download_path, filename))
        if existing_file and existing_file.get('exists'):
            logger.info("File already exists, skipping download", extra={"context": {"file": filename}})
            return

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*'
            }

            # For now, we'll implement basic download without resume
            # TODO: Add resume functionality with SafeFileWriter
            with requests.get(url, headers=headers, stream=True, timeout=15) as r:
                r.raise_for_status()

                # Collect all chunks with bandwidth throttling
                chunks = []
                for chunk in r.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        chunk_start_time = time.time()
                        chunks.append(chunk)
                        # THROTTLE BANDWIDTH HERE
                        self.bandwidth_manager.throttle(len(chunk), chunk_start_time)

                # Combine chunks into bytes for atomic write
                content = b''.join(chunks)

                # Use SafeFileWriter for atomic write
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
            logger.error("Download blocked", extra={"context": {"url": url, "status": e.response.status_code}})
        except Exception as e:
            logger.error("Download failed", extra={"context": {"url": url, "error": str(e)}})