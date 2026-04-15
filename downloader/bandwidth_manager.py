import time
import yaml
from monitoring.logger import get_logger

logger = get_logger("BandwidthManager")

class BandwidthManager:
    """
    Enforces maximum download speeds to prevent network starvation.
    """
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Convert max_kbps to bytes per second
        self.max_bps = self.config['bandwidth']['max_kbps'] * 1024

    def throttle(self, chunk_size: int, start_time: float):
        """Calculates time taken vs expected time, and sleeps to enforce limit."""
        if self.max_bps <= 0:
            return # 0 means unlimited
            
        elapsed = time.time() - start_time
        expected_time = chunk_size / self.max_bps
        
        if elapsed < expected_time:
            sleep_time = expected_time - elapsed
            time.sleep(sleep_time)