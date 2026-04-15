import psutil
import shutil
import yaml
import os
from monitoring.logger import get_logger

logger = get_logger("ResourceGuard")

class ResourceGuard:
    """
    Protects the host machine from out-of-memory (OOM) or full-disk crashes.
    (Constitution Sec 4.1)
    """
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.mem_limit = self.config['resources']['memory_limit_percent']
        self.disk_min_bytes = self.config['resources']['disk_min_gb'] * (1024 ** 3)
        self.download_path = self.config['download']['path']
        
        os.makedirs(self.download_path, exist_ok=True)

    def check_resources(self) -> bool:
        """Returns True if resources are safe, False if system is overloaded."""
        # 1. Check RAM usage
        mem = psutil.virtual_memory()
        if mem.percent > self.mem_limit:
            logger.warning("Backpressure Active: Memory limit exceeded!", extra={"context": {"ram_percent": mem.percent, "limit": self.mem_limit}})
            return False

        # 2. Check Disk Space
        total, used, free = shutil.disk_usage(self.download_path)
        if free < self.disk_min_bytes:
            free_gb = round(free / (1024 ** 3), 2)
            logger.critical("Emergency Pause: Disk space critically low!", extra={"context": {"free_gb": free_gb, "min_required_gb": self.config['resources']['disk_min_gb']}})
            return False

        return True