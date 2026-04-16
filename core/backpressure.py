import asyncio
import time
from typing import Optional
from monitoring.logger import get_logger
from core.priority_queue import TaskQueue

logger = get_logger("BackpressureController")

class BackpressureController:
    """
    Monitors queue size and throttles intake to prevent memory exhaustion.
    Constitution Sec 4.1: Backpressure & Fail-Safe Execution
    """

    def __init__(self, queue: TaskQueue, max_queue_size: int = 100, throttle_delay: float = 2.0):
        self.queue = queue
        self.max_queue_size = max_queue_size
        self.throttle_delay = throttle_delay
        self.last_throttle_time = 0
        self.throttle_count = 0

    def should_throttle_intake(self) -> bool:
        """
        Returns True if intake should be throttled due to queue pressure.
        """
        current_size = self.queue.qsize()

        if current_size > self.max_queue_size:
            self.throttle_count += 1
            logger.warning("Backpressure Active: Queue size exceeded threshold",
                         extra={"context": {
                             "queue_size": current_size,
                             "max_threshold": self.max_queue_size,
                             "throttle_count": self.throttle_count
                         }})
            return True

        return False

    async def throttle_if_needed(self) -> bool:
        """
        Throttles intake if queue pressure is high.
        Returns True if throttled, False otherwise.
        """
        if self.should_throttle_intake():
            # Prevent rapid throttling cycles
            now = time.time()
            if now - self.last_throttle_time < 1.0:  # Minimum 1 second between throttles
                return False

            self.last_throttle_time = now

            logger.info("Applying backpressure throttle",
                       extra={"context": {"delay": self.throttle_delay}})
            await asyncio.sleep(self.throttle_delay)
            return True

        return False

    def get_queue_pressure_ratio(self) -> float:
        """
        Returns queue pressure as a ratio (0.0 to 1.0+).
        1.0 = at threshold, >1.0 = over threshold.
        """
        return self.queue.qsize() / self.max_queue_size

    def is_under_pressure(self) -> bool:
        """
        Returns True if queue is under significant pressure (>80% of max).
        """
        return self.get_queue_pressure_ratio() > 0.8