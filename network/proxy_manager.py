import asyncio
import random
from typing import Optional, List, Dict
import yaml
from monitoring.logger import get_logger

logger = get_logger("ProxyManager")

class ProxyManager:
    """
    Manages proxy rotation for distributed requests.
    Supports rotation strategies: round-robin, random, weighted.
    Handles proxy health checking and rotation on failure.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize proxy manager from config."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.proxy_config = config.get('proxy', {})
        except Exception as e:
            logger.warning("Could not load proxy config", extra={
                "context": {"error": str(e)}
            })
            self.proxy_config = {}
        
        self.proxies: List[Dict] = self._load_proxies()
        self.current_index = 0
        self.failed_proxies: set = set()
        self.strategy = self.proxy_config.get('strategy', 'round-robin')
        
        logger.info("ProxyManager initialized", extra={
            "context": {
                "proxy_count": len(self.proxies),
                "strategy": self.strategy
            }
        })
    
    def _load_proxies(self) -> List[Dict]:
        """Loads proxies from configuration."""
        proxies = []
        
        proxy_list = self.proxy_config.get('list', [])
        if isinstance(proxy_list, list):
            for proxy_url in proxy_list:
                if isinstance(proxy_url, str):
                    proxies.append({
                        'url': proxy_url,
                        'weight': 1,
                        'active': True
                    })
                elif isinstance(proxy_url, dict):
                    proxies.append(proxy_url)
        
        return proxies
    
    def get_next_proxy(self) -> Optional[str]:
        """
        Gets the next proxy based on configured strategy.
        Returns proxy URL or None if no proxies available.
        """
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        active_proxies = [p for p in self.proxies if p['active']]
        
        if not active_proxies:
            logger.warning("All proxies failed, attempting reset")
            # Reset and try again
            self._reset_failed_proxies()
            active_proxies = [p for p in self.proxies if p['active']]
        
        if not active_proxies:
            return None
        
        if self.strategy == 'random':
            proxy = random.choice(active_proxies)
        elif self.strategy == 'weighted':
            proxy = self._get_weighted_proxy(active_proxies)
        else:  # round-robin
            proxy = self._get_round_robin_proxy(active_proxies)
        
        logger.debug("Proxy selected", extra={
            "context": {"proxy": proxy['url'][:30] + "...", "strategy": self.strategy}
        })
        
        return proxy['url']
    
    def _get_round_robin_proxy(self, proxies: List[Dict]) -> Dict:
        """Gets proxy using round-robin strategy."""
        proxy = proxies[self.current_index % len(proxies)]
        self.current_index += 1
        return proxy
    
    def _get_weighted_proxy(self, proxies: List[Dict]) -> Dict:
        """Gets proxy based on weight (success rate)."""
        total_weight = sum(p.get('weight', 1) for p in proxies)
        target = random.uniform(0, total_weight)
        current = 0
        
        for proxy in proxies:
            current += proxy.get('weight', 1)
            if current >= target:
                return proxy
        
        return proxies[0]
    
    def mark_proxy_failed(self, proxy_url: str):
        """Marks a proxy as failed."""
        for proxy in self.proxies:
            if proxy['url'] == proxy_url:
                proxy['active'] = False
                self.failed_proxies.add(proxy_url)
                logger.warning("Proxy marked as failed", extra={
                    "context": {
                        "proxy": proxy_url[:30] + "...",
                        "failed_count": len(self.failed_proxies)
                    }
                })
                break
    
    def mark_proxy_success(self, proxy_url: str):
        """Marks a proxy as successful, increasing its weight."""
        for proxy in self.proxies:
            if proxy['url'] == proxy_url:
                weight = proxy.get('weight', 1)
                proxy['weight'] = min(weight + 0.1, 5.0)  # Cap at 5.0
                if proxy_url in self.failed_proxies:
                    self.failed_proxies.remove(proxy_url)
                    proxy['active'] = True
                logger.debug("Proxy marked as success", extra={
                    "context": {"proxy": proxy_url[:30] + "...", "weight": proxy['weight']}
                })
                break
    
    def _reset_failed_proxies(self):
        """Resets all proxies after timeout period."""
        logger.info("Resetting all proxies", extra={
            "context": {"failed_count": len(self.failed_proxies)}
        })
        
        for proxy in self.proxies:
            proxy['active'] = True
            proxy['weight'] = 1
        
        self.failed_proxies.clear()
    
    def add_proxy(self, proxy_url: str, weight: float = 1.0):
        """Adds a new proxy to the rotation."""
        proxy = {
            'url': proxy_url,
            'weight': weight,
            'active': True
        }
        self.proxies.append(proxy)
        logger.info("Proxy added", extra={
            "context": {"proxy": proxy_url[:30] + "...", "total": len(self.proxies)}
        })
    
    def remove_proxy(self, proxy_url: str):
        """Removes a proxy from rotation."""
        self.proxies = [p for p in self.proxies if p['url'] != proxy_url]
        self.failed_proxies.discard(proxy_url)
        logger.info("Proxy removed", extra={
            "context": {"proxy": proxy_url[:30] + "...", "total": len(self.proxies)}
        })
    
    def get_stats(self) -> Dict:
        """Returns proxy manager statistics."""
        stats = {
            "total_proxies": len(self.proxies),
            "active_proxies": len([p for p in self.proxies if p['active']]),
            "failed_proxies": len(self.failed_proxies),
            "strategy": self.strategy,
        }
        return stats
