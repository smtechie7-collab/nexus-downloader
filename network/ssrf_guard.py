import ipaddress
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse
from monitoring.logger import get_logger

logger = get_logger("SSRFGuard")

class SSRFGuard:
    """
    Server-Side Request Forgery Protection Layer
    Constitution Section 5.1: Zero Trust & Advanced Security
    Blocks requests to private/internal IP ranges and localhost.
    """

    # Private IP ranges that should be blocked
    PRIVATE_RANGES = [
        ipaddress.ip_network('127.0.0.0/8'),      # localhost
        ipaddress.ip_network('10.0.0.0/8'),       # private class A
        ipaddress.ip_network('172.16.0.0/12'),    # private class B
        ipaddress.ip_network('192.168.0.0/16'),   # private class C
        ipaddress.ip_network('169.254.0.0/16'),   # link-local
        ipaddress.ip_network('fc00::/7'),         # IPv6 unique local
        ipaddress.ip_network('fe80::/10'),        # IPv6 link-local
    ]

    def __init__(self):
        self.blocked_domains = {
            'localhost',
            'localhost.localdomain',
            'broadcasthost',
            'local',
        }

    def is_safe_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if a URL is safe from SSRF attacks.
        Returns (is_safe, reason_if_blocked)
        """
        try:
            parsed = urlparse(url)

            # Check for blocked domains
            if parsed.hostname and parsed.hostname.lower() in self.blocked_domains:
                return False, f"Blocked domain: {parsed.hostname}"

            # Resolve hostname to IP
            try:
                ip = socket.gethostbyname(parsed.hostname)
                ip_addr = ipaddress.ip_address(ip)
            except (socket.gaierror, ValueError) as e:
                # If we can't resolve, allow it (fail open for DNS issues)
                logger.warning("Could not resolve hostname", extra={
                    "context": {"hostname": parsed.hostname, "error": str(e)}
                })
                return True, None

            # Check if IP is in private ranges
            for private_range in self.PRIVATE_RANGES:
                if ip_addr in private_range:
                    logger.warning("SSRF attempt blocked", extra={
                        "context": {
                            "url": url,
                            "ip": str(ip_addr),
                            "range": str(private_range)
                        }
                    })
                    return False, f"Private IP blocked: {ip_addr}"

            return True, None

        except Exception as e:
            logger.error("SSRF check failed", extra={
                "context": {"url": url, "error": str(e)}
            })
            # Fail safe: block on error
            return False, f"SSRF check error: {str(e)}"

    def validate_request(self, url: str) -> bool:
        """
        Validates a URL for SSRF protection.
        Returns True if safe, False if blocked.
        Logs warnings for blocked requests.
        """
        is_safe, reason = self.is_safe_url(url)
        if not is_safe:
            logger.warning("SSRF protection triggered", extra={
                "context": {"url": url, "reason": reason}
            })
        return is_safe

    def get_blocked_ranges(self) -> list:
        """Returns list of blocked IP ranges for documentation."""
        return [str(rng) for rng in self.PRIVATE_RANGES]