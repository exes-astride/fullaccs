"""
Validator 4: Latency Tester - RTT response time measurement
"""

import asyncio
import time
from typing import Optional
from src.models.proxy import ProxyModel
from src.utils.http_client import HTTPClient
from src.core.constants import LATENCY_TEST_TIMEOUT
import structlog

logger = structlog.get_logger(__name__)


class LatencyTester:
    """Measure proxy response time (RTT)"""
    
    # Fast test endpoint
    TEST_URL = "http://httpbin.org/status/200"
    
    def __init__(self, timeout: float = LATENCY_TEST_TIMEOUT):
        self.timeout = timeout
    
    async def measure_latency(self, proxy: ProxyModel) -> float:
        """Measure latency in milliseconds"""
        if not proxy.is_alive:
            return 0.0
        
        try:
            start_time = time.time()
            
            async with HTTPClient(timeout=self.timeout) as client:
                await client.get(self.TEST_URL, timeout=self.timeout)
            
            latency_ms = (time.time() - start_time) * 1000
            
            proxy.latency_ms = latency_ms
            await logger.ainfo(
                "Latency measured",
                ip=proxy.ip,
                latency_ms=latency_ms
            )
            
            return latency_ms
        
        except asyncio.TimeoutError:
            proxy.latency_ms = self.timeout * 1000
            await logger.ainfo(
                "Latency timeout",
                ip=proxy.ip,
                timeout=self.timeout
            )
            return self.timeout * 1000
        
        except Exception as e:
            await logger.aerror(
                "Latency measurement error",
                ip=proxy.ip,
                error=str(e)
            )
            return self.timeout * 1000
    
    async def validate_batch(self, proxies: list[ProxyModel]) -> list[ProxyModel]:
        """Measure latency for batch of proxies"""
        tasks = [self.measure_latency(p) for p in proxies]
        await asyncio.gather(*tasks, return_exceptions=True)
        return proxies