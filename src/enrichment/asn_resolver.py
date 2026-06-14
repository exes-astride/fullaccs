"""
ASN Resolver - Get ISP and ASN information for proxies
"""

import socket
from typing import Optional, Tuple
from src.models.proxy import ProxyModel
import structlog

logger = structlog.get_logger(__name__)


class ASNResolver:
    """Resolve ASN and ISP information for IP addresses"""
    
    async def resolve(self, proxy: ProxyModel) -> Tuple[Optional[str], Optional[str]]:
        """Resolve ASN and ISP for proxy IP
        
        Returns: (asn, isp)
        """
        if not proxy.is_alive:
            return None, None
        
        try:
            # Try to get ISP via reverse DNS
            try:
                hostname = socket.getfqdn(proxy.ip)
                if hostname != proxy.ip:
                    proxy.isp = hostname
                    await logger.ainfo(
                        "ISP resolved via DNS",
                        ip=proxy.ip,
                        hostname=hostname
                    )
            except:
                pass
            
            # ASN resolution (would need GeoIP database - already handled in geo_locator)
            if proxy.asn:
                await logger.ainfo(
                    "ASN already set",
                    ip=proxy.ip,
                    asn=proxy.asn
                )
            
            return proxy.asn, proxy.isp
        
        except Exception as e:
            await logger.aerror(
                "ASN resolution error",
                ip=proxy.ip,
                error=str(e)
            )
            return None, None
    
    async def resolve_batch(self, proxies: list[ProxyModel]) -> list[ProxyModel]:
        """Resolve ASN for batch of proxies"""
        import asyncio
        tasks = [self.resolve(p) for p in proxies]
        await asyncio.gather(*tasks, return_exceptions=True)
        return proxies