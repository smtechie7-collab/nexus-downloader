import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from monitoring.logger import get_logger
from downloader.bandwidth_manager import BandwidthManager
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
        os.makedirs(self.download_path, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=self.max_threads)

    def download(self, url: str, filename: str):
        self.executor.submit(self._download_task, url, filename)

    def _download_task(self, url: str, filename: str):
        filepath = os.path.join(self.download_path, filename)
        part_filepath = filepath + ".part"
        
        if os.path.exists(filepath):
            logger.info("File already exists, skipping download", extra={"context": {"file": filename}})
            return
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*'
            }
            
            if os.path.exists(part_filepath):
                file_size = os.path.getsize(part_filepath)
                headers['Range'] = f'bytes={file_size}-'
                logger.info("Resuming download", extra={"context": {"file": filename, "bytes": file_size}})
            
            with requests.get(url, headers=headers, stream=True, timeout=15) as r:
                r.raise_for_status()
                mode = 'ab' if 'Range' in headers else 'wb'
                
                with open(part_filepath, mode) as f:
                    for chunk in r.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            chunk_start_time = time.time()
                            f.write(chunk)
                            # THROTTLE BANDWIDTH HERE
                            self.bandwidth_manager.throttle(len(chunk), chunk_start_time)
                            
            os.replace(part_filepath, filepath)
            logger.info("Download complete successfully!", extra={"context": {"file": filename}})
            
        except requests.exceptions.HTTPError as e:
            logger.error("Download blocked", extra={"context": {"url": url, "status": e.response.status_code}})
        except Exception as e:
            logger.error("Download failed", extra={"context": {"url": url, "error": str(e)}})