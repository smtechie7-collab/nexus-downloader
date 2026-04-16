import time
import yaml
from monitoring.logger import get_logger

logger = get_logger("BandwidthManager")

class BandwidthManager:
    """
    Enforces maximum download speeds to prevent network starvation.
    """
    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        # Convert max_kbps to bytes per second
        self.max_bps = int(self.config['bandwidth']['max_kbps']) * 1024

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

    def throttle(self, chunk_size: int, start_time: float):
        """Calculates time taken vs expected time, and sleeps to enforce limit."""
        if self.max_bps <= 0:
            return # 0 means unlimited
            
        elapsed = time.time() - start_time
        expected_time = chunk_size / self.max_bps
        
        if elapsed < expected_time:
            sleep_time = expected_time - elapsed
            time.sleep(sleep_time)