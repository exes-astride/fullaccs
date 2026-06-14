"""
Validator 3: Anonymity Check - Elite, Anonymous, Transparent scoring
"""

from typing import Optional
from src.models.proxy import ProxyModel, AnonymityLevel
from src.utils.http_client import HTTPClient
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class AnonymityChecker:
    """Check proxy anonymity level"""
    
    # Test URLs to check headers
    TEST_URLS = [
        "http://httpbin.org/ip",
        "http://api.ipify.org?format=json",
        "http://checkip.amazonaws.com"
    ]
    
    REVEALING_HEADERS = [
        "x-forwarded-for",
        "x-real-ip",
        "cf-connecting-ip",
        "x-client-ip"
    ]
    
    async def check_anonymity(self, proxy: ProxyModel) -> Optional[AnonymityLevel]:
        """Check proxy anonymity level"""
        if not proxy.is_alive:
            return AnonymityLevel.TRANSPARENT
        
        try:
            async with HTTPClient() as client:
                # Try to detect if proxy sends identifying headers
                for test_url in self.TEST_URLS:
                    try:
                        response = await client.get(test_url, timeout=5)
                        
                        # Check for revealing headers
                        revealing_headers_found = sum(
                            1 for header in self.REVEALING_HEADERS 
                            if header.lower() in response.lower()
                        )
                        
                        if revealing_headers_found > 0:
                            # Found identifying info = Transparent
                            proxy.anonymity_level = AnonymityLevel.TRANSPARENT
                            await logger.ainfo(
                                "Anonymity detected",
                                ip=proxy.ip,
                                level="transparent"
                            )
                            return AnonymityLevel.TRANSPARENT
                        else:
                            # No identifying headers = could be elite or anonymous
                            proxy.anonymity_level = AnonymityLevel.ELITE
                            await logger.ainfo(
                                "Anonymity detected",
                                ip=proxy.ip,
                                level="elite"
                            )
                            return AnonymityLevel.ELITE
                    except:
                        continue
                
                # Default to anonymous if can't determine
                proxy.anonymity_level = AnonymityLevel.ANONYMOUS
                return AnonymityLevel.ANONYMOUS
        
        except Exception as e:
            await logger.aerror(
                "Anonymity check error",
                ip=proxy.ip,
                error=str(e)
            )
            proxy.anonymity_level = AnonymityLevel.ANONYMOUS
            return AnonymityLevel.ANONYMOUS
    
    async def validate_batch(self, proxies: list[ProxyModel]) -> list[ProxyModel]:
        """Check anonymity for batch of proxies"""
        tasks = [self.check_anonymity(p) for p in proxies]
        await asyncio.gather(*tasks, return_exceptions=True)
        return proxies