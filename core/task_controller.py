import uuid
from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from monitoring.logger import get_logger

logger = get_logger("TaskController")

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

class TaskController:
    """
    Manages task lifecycle: creation, pause, resume, cancel, completion.
    Maintains global task state and coordinates with queue.
    """
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._paused_tasks: set = set()
        self._cancelled_tasks: set = set()
        self._global_pause = False
        self._lock = asyncio.Lock()
        
    async def create_task(self, url: str, metadata: Dict = None) -> str:
        """Creates a new task and returns task_id."""
        task = Task(url=url, metadata=metadata or {})
        self._tasks[task.id] = task
        logger.info("Task created", extra={
            "context": {
                "task_id": task.id,
                "url": url
            }
        })
        return task.id
    
    async def start_task(self, task_id: str) -> bool:
        """Marks task as running."""
        async with self._lock:
            if task_id not in self._tasks:
                logger.warning("Start task: Task not found", extra={"context": {"task_id": task_id}})
                return False
            
            task = self._tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            logger.info("Task started", extra={"context": {"task_id": task_id}})
            return True
    
    async def complete_task(self, task_id: str) -> bool:
        """Marks task as completed."""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            logger.info("Task completed", extra={"context": {"task_id": task_id}})
            return True
    
    async def fail_task(self, task_id: str, error: str) -> bool:
        """Marks task as failed."""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.retry_count += 1
            
            logger.error("Task failed", extra={
                "context": {
                    "task_id": task_id,
                    "error": error,
                    "retry_count": task.retry_count
                }
            })
            return True
    
    async def pause_task(self, task_id: str) -> bool:
        """Pauses a specific task."""
        async with self._lock:
            if task_id not in self._tasks:
                logger.warning("Pause task: Task not found", extra={"context": {"task_id": task_id}})
                return False
            
            task = self._tasks[task_id]
            if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                logger.warning("Cannot pause task in this state", extra={
                    "context": {"task_id": task_id, "status": task.status}
                })
                return False
            
            task.status = TaskStatus.PAUSED
            self._paused_tasks.add(task_id)
            logger.info("Task paused", extra={"context": {"task_id": task_id}})
            return True
    
    async def resume_task(self, task_id: str) -> bool:
        """Resumes a paused task."""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            if task.status != TaskStatus.PAUSED:
                logger.warning("Resume task: Task not paused", extra={
                    "context": {"task_id": task_id, "status": task.status}
                })
                return False
            
            task.status = TaskStatus.RUNNING
            self._paused_tasks.discard(task_id)
            logger.info("Task resumed", extra={"context": {"task_id": task_id}})
            return True
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancels a task."""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            if task.status == TaskStatus.COMPLETED:
                logger.warning("Cannot cancel completed task", extra={"context": {"task_id": task_id}})
                return False
            
            task.status = TaskStatus.CANCELLED
            self._cancelled_tasks.add(task_id)
            self._paused_tasks.discard(task_id)
            logger.info("Task cancelled", extra={"context": {"task_id": task_id}})
            return True
    
    async def pause_all(self) -> int:
        """Pauses all running tasks globally."""
        async with self._lock:
            self._global_pause = True
            paused_count = 0
            
            for task_id, task in self._tasks.items():
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.PAUSED
                    self._paused_tasks.add(task_id)
                    paused_count += 1
            
            logger.info("Global pause activated", extra={
                "context": {"paused_count": paused_count}
            })
            return paused_count
    
    async def resume_all(self) -> int:
        """Resumes all paused tasks globally."""
        async with self._lock:
            self._global_pause = False
            resumed_count = 0
            
            for task_id in list(self._paused_tasks):
                if task_id in self._tasks:
                    task = self._tasks[task_id]
                    if task.status == TaskStatus.PAUSED:
                        task.status = TaskStatus.RUNNING
                        self._paused_tasks.discard(task_id)
                        resumed_count += 1
            
            logger.info("Global resume activated", extra={
                "context": {"resumed_count": resumed_count}
            })
            return resumed_count
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieves task details."""
        return self._tasks.get(task_id)
    
    async def is_paused(self, task_id: str) -> bool:
        """Checks if a task is paused."""
        return task_id in self._paused_tasks or self._global_pause
    
    async def is_cancelled(self, task_id: str) -> bool:
        """Checks if a task is cancelled."""
        return task_id in self._cancelled_tasks
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Retrieves all tasks with a given status."""
        return [task for task in self._tasks.values() if task.status == status]
    
    async def get_stats(self) -> Dict:
        """Returns task statistics."""
        stats = {
            "total": len(self._tasks),
            "pending": len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING]),
            "running": len([t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]),
            "paused": len([t for t in self._tasks.values() if t.status == TaskStatus.PAUSED]),
            "completed": len([t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in self._tasks.values() if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in self._tasks.values() if t.status == TaskStatus.CANCELLED]),
            "global_pause": self._global_pause
        }
        return stats
    
    async def cleanup_old_tasks(self, hours: int = 24) -> int:
        """Removes completed/cancelled/failed tasks older than specified hours."""
        from datetime import timedelta
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)
        
        async with self._lock:
            to_remove = [
                task_id for task_id, task in self._tasks.items()
                if task.completed_at and task.completed_at < cutoff
                and task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]
            ]
            
            for task_id in to_remove:
                del self._tasks[task_id]
                self._paused_tasks.discard(task_id)
                self._cancelled_tasks.discard(task_id)
            
            logger.info("Task cleanup completed", extra={
                "context": {"removed_count": len(to_remove)}
            })
            return len(to_remove)
