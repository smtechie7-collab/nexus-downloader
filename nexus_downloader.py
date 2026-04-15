
import sys
import os
import asyncio

# VS IntelliSense aur Runtime dono ke liye absolute path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.router import Router
from core.priority_queue import TaskQueue
from core.resource_guard import ResourceGuard
from downloader.download_manager import DownloadManager
from engines.fast_engine_v1 import FastEngineV1
from storage.deduplicator import Deduplicator
from storage.cache import CacheLayer
from pipeline.validator import validate_media
from utils.constants import Priority
from monitoring.logger import get_logger

logger = get_logger("MainPipeline")

async def orchestration_pipeline(urls: list, router: Router, queue: TaskQueue, dedup: Deduplicator, cache: CacheLayer, guard: ResourceGuard):
    for url in urls:
        # RESOURCE GUARD CHECK (Constitution Sec 4.1)
        if not guard.check_resources():
            logger.warning("Intake throttled by ResourceGuard", extra={"context": {"url": url}})
            await asyncio.sleep(5) # Backpressure slowdown
            continue

        if dedup.is_duplicate(url):
            continue
            
        result = cache.get(url)
        if not result:
            logger.info("Routing to engine", extra={"context": {"url": url}})
            result = await router.route(url)
            if result["status"] == "success":
                cache.set(url, result)
        else:
             logger.info("Retrieved from Cache", extra={"context": {"url": url}})
             
        if result["status"] == "success":
            for media in result["media"]:
                logger.info("Validating media headers...", extra={"context": {"media_url": media['url']}})
                is_valid = await validate_media(media)
                if is_valid:
                    queue.add(media, Priority.HIGH)
                    logger.info("Media queued", extra={"context": {"url": media['url']}})
        else:
            logger.error("Extraction failed", extra={"context": {"url": url, "reason": result["error_msg"]}})

def download_worker(queue: TaskQueue, download_manager: DownloadManager):
    while True:
        task = queue.get(timeout=3)
        if task is None:
            break 
            
        url = str(task['url'])
        filename = task['metadata'].get('title', 'download') + ".mp4"
        download_manager.download(url, filename)
        queue.task_done()

async def main():
    logger.info("Nexus Zenith Pipeline v5.0 (VS Studio Optimized)")
    
    guard = ResourceGuard()
    router = Router()
    queue = TaskQueue()
    dedup = Deduplicator()
    cache = CacheLayer()
    download_manager = DownloadManager()
    
    router.register_engine("default", FastEngineV1())
    
    urls_to_process = [
        "https://example.com/video1",
        "https://example.com/error-test"
    ]
    
    await orchestration_pipeline(urls_to_process, router, queue, dedup, cache, guard)
    
    logger.info("Starting Download Plane")
    download_worker(queue, download_manager)

if __name__ == "__main__":
    asyncio.run(main())
