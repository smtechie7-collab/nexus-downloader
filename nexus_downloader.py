
import sys
import os
import asyncio
import threading
import urllib.parse

# VS IntelliSense aur Runtime dono ke liye absolute path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.router import Router
from core.priority_queue import TaskQueue
from core.resource_guard import ResourceGuard
from downloader.download_manager import DownloadManager
from engines.fast_engine_v1 import FastEngineV1
from engines.headless_engine_v1 import HeadlessEngineV1
from engines.media_engine_v1 import MediaEngineV1
from engines.spider_engine_v1 import SpiderEngineV1
from engines.stealth_engine_v1 import StealthEngineV1
from storage.deduplicator import Deduplicator
from storage.cache import CacheLayer
from pipeline.validator import validate_media
from pipeline.parser import URLParser
from network.ssrf_guard import SSRFGuard
from utils.constants import Priority
from monitoring.logger import get_logger

logger = get_logger("MainPipeline")

async def orchestration_pipeline(urls: list, router: Router, queue: TaskQueue, dedup: Deduplicator, cache: CacheLayer, guard: ResourceGuard, ssrf_guard: SSRFGuard, url_parser: URLParser):
    for url in urls:
        # SSRF PROTECTION CHECK (Constitution Sec 5.1)
        if not ssrf_guard.validate_request(url):
            logger.warning("URL blocked by SSRF protection", extra={"context": {"url": url}})
            continue

        # URL NORMALIZATION & PARSING (Phase B)
        parsed_info = url_parser.extract_media_info(url)
        normalized_url = parsed_info['normalized_url']
        logger.debug("URL parsed and normalized", extra={"context": {"original": url, "normalized": normalized_url}})

        # RESOURCE GUARD CHECK (Constitution Sec 4.1)
        if not guard.check_resources():
            logger.warning("Intake throttled by ResourceGuard", extra={"context": {"url": normalized_url}})
            await asyncio.sleep(5) # Backpressure slowdown
            continue

        if dedup.is_duplicate(normalized_url):
            continue
            
        result = cache.get(normalized_url)
        if not result:
            logger.info("Routing to engine", extra={"context": {"url": normalized_url}})
            result = await router.route(normalized_url)
            if result["status"] == "success":
                cache.set(normalized_url, result)
        else:
             logger.info("Retrieved from Cache", extra={"context": {"url": normalized_url}})
             
        if result["status"] == "success":
            for media in result["media"]:
                logger.info("Validating media headers...", extra={"context": {"media_url": media['url']}})
                is_valid = await validate_media(media)
                if is_valid:
                    # Add parsed metadata to the task
                    task_data = media.copy()
                    task_data['metadata'] = parsed_info
                    queue.add(task_data, Priority.HIGH)
                    logger.info("Media queued", extra={"context": {"url": media['url']}})
        else:
            logger.error("Extraction failed", extra={"context": {"url": url, "reason": result["error_msg"]}})

def download_worker(queue: TaskQueue, download_manager: DownloadManager):
    while True:
        task = queue.get(timeout=3)
        if task is None:
            break

        url = str(task['url'])
        title = task['metadata'].get('title', 'download')
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or '.bin'
        filename = title + ext

        future = download_manager.download(url, filename)

        try:
            future.result()
        except Exception as e:
            logger.error("Download task failed", extra={"context": {"url": url, "error": str(e)}})
        finally:
            queue.task_done()

async def main():
    logger.info("Nexus Zenith Pipeline v5.0 (VS Studio Optimized)")
    
    guard = ResourceGuard()
    router = Router()
    queue = TaskQueue()
    dedup = Deduplicator()
    cache = CacheLayer()
    download_manager = DownloadManager()
    ssrf_guard = SSRFGuard()
    url_parser = URLParser()
    
    # Register all engines with the router
    router.register_engine("fast_engine", FastEngineV1())
    router.register_engine("headless_engine", HeadlessEngineV1())
    router.register_engine("media_engine", MediaEngineV1())
    router.register_engine("spider_engine", SpiderEngineV1())
    router.register_engine("stealth_engine", StealthEngineV1())
    
    urls_to_process = [
        "https://example.com/video1",
        "https://example.com/error-test"
    ]
    
    await orchestration_pipeline(urls_to_process, router, queue, dedup, cache, guard, ssrf_guard, url_parser)
    
    logger.info("Starting Download Plane")
    # Run download worker in separate thread to avoid blocking async event loop
    download_thread = threading.Thread(target=download_worker, args=(queue, download_manager))
    download_thread.start()

    # Wait for queue to be processed and downloads to complete
    queue._queue.join()  # Wait for all tasks to be done
    download_thread.join(timeout=10)
