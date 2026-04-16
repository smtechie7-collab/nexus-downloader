import re
from typing import Dict, List, Optional, Callable
from urllib.parse import urlparse
from monitoring.logger import get_logger

logger = get_logger("DomainStrategy")

class DomainStrategy:
    """
    Intelligent domain-to-engine mapping.
    Routes URLs to the most appropriate engine based on domain patterns.
    """
    
    def __init__(self):
        self._domain_rules: Dict[str, str] = {}
        self._pattern_rules: List[tuple] = []  # List of (pattern, engine_name) tuples
        self._engine_registry: Dict[str, Callable] = {}
        self._fallback_engine = "fast_engine"
        
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Sets up default domain routing strategies."""
        # Video platforms
        self.register_domain_rule("youtube.com", "media_engine")
        self.register_domain_rule("www.youtube.com", "media_engine")
        self.register_domain_rule("vimeo.com", "media_engine")
        self.register_domain_rule("dailymotion.com", "media_engine")
        
        # Social media
        self.register_domain_rule("facebook.com", "stealth_engine")
        self.register_domain_rule("instagram.com", "stealth_engine")
        self.register_domain_rule("twitter.com", "spider_engine")
        self.register_domain_rule("x.com", "spider_engine")
        
        # Streaming platforms
        self.register_domain_rule("twitch.tv", "headless_engine")
        self.register_domain_rule("netflix.com", "stealth_engine")
        self.register_domain_rule("hulu.com", "stealth_engine")
        
        # General patterns
        self.register_pattern_rule(r".*\.mp4$", "fast_engine")
        self.register_pattern_rule(r".*\.m3u8$", "media_engine")
        self.register_pattern_rule(r".*\.webm$", "fast_engine")
        self.register_pattern_rule(r".*\.mp3$", "fast_engine")
        self.register_pattern_rule(r".*\.pdf$", "fast_engine")
        self.register_pattern_rule(r".*\.docx?$", "fast_engine")
        self.register_pattern_rule(r".*\.xlsx?$", "fast_engine")
        self.register_pattern_rule(r".*\.pptx?$", "fast_engine")
        self.register_pattern_rule(r".*\.zip$", "fast_engine")
    
    def register_engine(self, engine_name: str, engine_instance: Callable):
        """Registers an engine to the strategy."""
        self._engine_registry[engine_name] = engine_instance
        logger.info("Engine registered", extra={
            "context": {"engine_name": engine_name}
        })
    
    def register_domain_rule(self, domain: str, engine_name: str):
        """Associates a domain with a specific engine."""
        self._domain_rules[domain.lower()] = engine_name
        logger.debug("Domain rule registered", extra={
            "context": {"domain": domain, "engine": engine_name}
        })
    
    def register_pattern_rule(self, pattern: str, engine_name: str):
        """Associates a URL pattern (regex) with a specific engine."""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            self._pattern_rules.append((compiled_pattern, engine_name))
            logger.debug("Pattern rule registered", extra={
                "context": {"pattern": pattern, "engine": engine_name}
            })
        except re.error as e:
            logger.error("Invalid regex pattern", extra={
                "context": {"pattern": pattern, "error": str(e)}
            })
    
    def set_fallback_engine(self, engine_name: str):
        """Sets the default fallback engine when no rules match."""
        self._fallback_engine = engine_name
        logger.info("Fallback engine set", extra={
            "context": {"engine": engine_name}
        })
    
    def get_engine_for_url(self, url: str) -> Optional[str]:
        """
        Determines the best engine for a given URL.
        Returns engine name or None if no matching rule found.
        """
        # Priority 1: Check pattern rules (most specific)
        for pattern, engine_name in self._pattern_rules:
            if pattern.search(url):
                logger.info("Engine selected by pattern", extra={
                    "context": {"url": url, "engine": engine_name}
                })
                return engine_name
        
        # Priority 2: Check domain rules
        try:
            domain = urlparse(url).netloc.lower()
            if domain in self._domain_rules:
                engine_name = self._domain_rules[domain]
                logger.info("Engine selected by domain", extra={
                    "context": {"url": url, "domain": domain, "engine": engine_name}
                })
                return engine_name
        except Exception as e:
            logger.warning("URL parsing failed", extra={
                "context": {"url": url, "error": str(e)}
            })
        
        # Priority 3: Use fallback engine
        logger.debug("Using fallback engine", extra={
            "context": {"url": url, "engine": self._fallback_engine}
        })
        return self._fallback_engine
    
    def get_engine_instance(self, url: str) -> Optional[Callable]:
        """Gets the engine instance for a URL."""
        engine_name = self.get_engine_for_url(url)
        if engine_name and engine_name in self._engine_registry:
            return self._engine_registry[engine_name]
        return None
    
    def get_engine_fallback_chain(self, url: str) -> List[str]:
        """
        Returns a fallback chain of engines to try if the primary engine fails.
        Primary -> Secondary -> Tertiary -> Fallback
        """
        primary = self.get_engine_for_url(url)
        
        # Build fallback chain
        chain = []
        if primary:
            chain.append(primary)
        
        # Add secondary engines
        if primary != "stealth_engine":
            chain.append("stealth_engine")
        if primary != "spider_engine":
            chain.append("spider_engine")
        if primary != "headless_engine":
            chain.append("headless_engine")
        if primary != "media_engine":
            chain.append("media_engine")
        if primary != "fast_engine":
            chain.append("fast_engine")
        
        logger.debug("Fallback chain built", extra={
            "context": {"url": url, "chain": chain}
        })
        return chain
    
    def get_all_rules(self) -> Dict:
        """Returns all configured rules for debugging."""
        return {
            "domain_rules": self._domain_rules,
            "pattern_rules": [p.pattern for p, _ in self._pattern_rules],
            "fallback_engine": self._fallback_engine,
            "registered_engines": list(self._engine_registry.keys())
        }
