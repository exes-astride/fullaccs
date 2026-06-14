"""
Spam Blacklist Checker - Check against known spam/malicious IPs
"""

from typing import Optional, List
from src.models.proxy import ProxyModel
import structlog

logger = structlog.get_logger(__name__)

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False


class SpamBlacklistChecker:
    """Check IPs against spam blacklists (DNSBL)"""
    
    # Popular DNSBL servers
    BLACKLIST_SERVERS = [
        "sbl.spamhaus.org",
        "css.spamhaus.org",
        "zen.spamhaus.org",
        "pbl.spamhaus.org",
    ]
    
    async def check_ip(self, ip: str) -> bool:
        """Check if IP is in any blacklist
        
        Returns: True if blacklisted, False if clean
        """
        if not DNS_AVAILABLE:
            await logger.awarning("DNS library not available, skipping blacklist check")
            return False
        
        try:
            # Reverse IP octets for DNSBL query
            octets = ip.split('.')
            reversed_ip = '.'.join(reversed(octets))
            
            for blacklist in self.BLACKLIST_SERVERS:
                query_domain = f"{reversed_ip}.{blacklist}"
                
                try:
                    dns.resolver.resolve(query_domain, 'A')
                    await logger.awarning(
                        "IP found in blacklist",
                        ip=ip,
                        blacklist=blacklist
                    )
                    return True
                except:
                    # Not in this blacklist, continue
                    continue
            
            return False
        
        except Exception as e:
            await logger.aerror(
                "Blacklist check error",
                ip=ip,
                error=str(e)
            )
            return False
    
    async def check_batch(self, proxies: list[ProxyModel]) -> list[ProxyModel]:
        """Check batch of proxies against blacklists"""
        import asyncio
        
        for proxy in proxies:
            is_blacklisted = await self.check_ip(proxy.ip)
            if is_blacklisted:
                proxy.quality_score = 0  # Zero out score for blacklisted IPs
        
        return proxies