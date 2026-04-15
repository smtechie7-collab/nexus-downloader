import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from monitoring.logger import get_logger

logger = get_logger("StateManager")

class StateManager:
    """
    Persists application state to disk for recovery and resumption.
    Enables crash recovery and task resumption across restarts.
    """
    
    def __init__(self, state_dir: str = "./state"):
        """
        Initialize state manager.
        
        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
        
        self._state: Dict[str, Any] = {
            'tasks': {},
            'metadata': {},
        }
        self._dirty = False
        self._lock = asyncio.Lock()
        
        self._load_state()
        logger.info("StateManager initialized", extra={
            "context": {"state_dir": state_dir}
        })
    
    def _get_state_file(self) -> str:
        """Gets the state file path."""
        return os.path.join(self.state_dir, "state.json")
    
    def _load_state(self):
        """Loads state from disk."""
        state_file = self._get_state_file()
        
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    self._state = json.load(f)
                logger.info("State loaded from disk", extra={
                    "context": {
                        "tasks": len(self._state.get('tasks', {}))
                    }
                })
            except Exception as e:
                logger.error("Failed to load state", extra={
                    "context": {"error": str(e)}
                })
        else:
            logger.info("No previous state found")
    
    async def save_state(self):
        """Persists state to disk."""
        async with self._lock:
            state_file = self._get_state_file()
            
            try:
                with open(state_file, 'w') as f:
                    json.dump(self._state, f, indent=2, default=str)
                self._dirty = False
                logger.debug("State saved")
            except Exception as e:
                logger.error("Failed to save state", extra={
                    "context": {"error": str(e)}
                })
    
    async def save_task(self, task_id: str, task_data: Dict):
        """Saves a task to state."""
        async with self._lock:
            self._state['tasks'][task_id] = {
                'data': task_data,
                'saved_at': datetime.now().isoformat()
            }
            self._dirty = True
            
            await self.save_state()
            logger.debug("Task saved", extra={
                "context": {"task_id": task_id}
            })
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Retrieves a task from state."""
        async with self._lock:
            task_entry = self._state['tasks'].get(task_id)
            if task_entry:
                return task_entry['data']
            return None
    
    async def delete_task(self, task_id: str):
        """Removes a task from state."""
        async with self._lock:
            if task_id in self._state['tasks']:
                del self._state['tasks'][task_id]
                self._dirty = True
                
                await self.save_state()
                logger.debug("Task deleted", extra={
                    "context": {"task_id": task_id}
                })
    
    async def get_all_pending_tasks(self) -> List[str]:
        """Gets all task IDs that haven't completed."""
        async with self._lock:
            pending = [
                task_id for task_id, entry in self._state['tasks'].items()
                if entry['data'].get('status') in ['pending', 'running', 'paused']
            ]
            return pending
    
    async def set_metadata(self, key: str, value: Any):
        """Sets metadata entry."""
        async with self._lock:
            self._state['metadata'][key] = {
                'value': value,
                'updated_at': datetime.now().isoformat()
            }
            self._dirty = True
            
            await self.save_state()
            logger.debug("Metadata set", extra={
                "context": {"key": key}
            })
    
    async def get_metadata(self, key: str) -> Optional[Any]:
        """Gets metadata entry."""
        async with self._lock:
            entry = self._state['metadata'].get(key)
            if entry:
                return entry['value']
            return None
    
    async def get_checkpoint(self, checkpoint_name: str) -> Optional[Dict]:
        """Gets a saved checkpoint."""
        checkpoint_file = os.path.join(
            self.state_dir,
            f"checkpoint_{checkpoint_name}.json"
        )
        
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to load checkpoint", extra={
                    "context": {"checkpoint": checkpoint_name, "error": str(e)}
                })
        
        return None
    
    async def save_checkpoint(self, checkpoint_name: str, data: Dict):
        """Saves a named checkpoint."""
        checkpoint_file = os.path.join(
            self.state_dir,
            f"checkpoint_{checkpoint_name}.json"
        )
        
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump({
                    'name': checkpoint_name,
                    'created_at': datetime.now().isoformat(),
                    'data': data
                }, f, indent=2, default=str)
            logger.info("Checkpoint saved", extra={
                "context": {"checkpoint": checkpoint_name}
            })
        except Exception as e:
            logger.error("Failed to save checkpoint", extra={
                "context": {"checkpoint": checkpoint_name, "error": str(e)}
            })
    
    async def clear_old_tasks(self, status_filter: List[str] = None):
        """Clears completed/failed tasks."""
        async with self._lock:
            if status_filter is None:
                status_filter = ['completed', 'failed', 'cancelled']
            
            to_delete = [
                task_id for task_id, entry in self._state['tasks'].items()
                if entry['data'].get('status') in status_filter
            ]
            
            for task_id in to_delete:
                del self._state['tasks'][task_id]
            
            if to_delete:
                self._dirty = True
                await self.save_state()
            
            logger.info("Old tasks cleared", extra={
                "context": {"cleared_count": len(to_delete)}
            })
    
    async def get_stats(self) -> Dict:
        """Gets state statistics."""
        async with self._lock:
            tasks = self._state.get('tasks', {})
            
            stats = {
                'total_tasks': len(tasks),
                'pending_tasks': len([
                    t for t in tasks.values()
                    if t['data'].get('status') in ['pending', 'running', 'paused']
                ]),
                'completed_tasks': len([
                    t for t in tasks.values()
                    if t['data'].get('status') == 'completed'
                ]),
                'failed_tasks': len([
                    t for t in tasks.values()
                    if t['data'].get('status') == 'failed'
                ]),
                'metadata_entries': len(self._state.get('metadata', {})),
            }
            
            return stats
