import queue
from dataclasses import dataclass, field
from typing import Any
from utils.constants import Priority

@dataclass(order=True)
class PrioritizedTask:
    priority: int
    item: Any = field(compare=False)

class TaskQueue:
    """Thread-safe Priority Queue."""
    def __init__(self):
        self._queue = queue.PriorityQueue()

    def add(self, task: Any, priority: Priority = Priority.MEDIUM):
        """Adds task to queue. Priority 1 (HIGH) is retrieved before Priority 3 (LOW)."""
        self._queue.put(PrioritizedTask(priority.value, task))

    def get(self, block: bool = True, timeout: int = None) -> Any:
        try:
            task = self._queue.get(block=block, timeout=timeout)
            return task.item
        except queue.Empty:
            return None
            
    def task_done(self):
        self._queue.task_done()
        
    def qsize(self):
        return self._queue.qsize()