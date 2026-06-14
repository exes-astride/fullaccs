"""
Validator 1: TCP Liveliness Check - Zero-dead proxy detection
Direct socket handshake to verify proxy is actually alive
"""

import asyncio
import socket
from typing import Tuple
from src.models.proxy import ProxyModel
from src.core.constants import SOCKET_TIMEOUT, LATENCY_TEST_TIMEOUT
from src.core.exceptions import ValidationException
import structlog
import time

logger = structlog.get_logger(__name__)


class TCPLivelinessValidator:
    """Check if proxy is alive via TCP handshake"""
    
    def __init__(self, timeout: float = SOCKET_TIMEOUT):
        self.timeout = timeout
    
    async def check_liveliness(self, proxy: ProxyModel) -> Tuple[bool, float]:
        """Check proxy liveliness and measure latency
        
        Returns: (is_alive, latency_ms)
        """
        try:
            start_time = time.time()
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            try:
                # Attempt connection
                await asyncio.wait_for(
                    asyncio.get_event_loop().sock_connect(sock, (proxy.ip, proxy.port)),
                    timeout=self.timeout
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                await logger.ainfo(
                    "Proxy alive",
                    ip=proxy.ip,
                    port=proxy.port,
                    latency_ms=latency_ms
                )
                
                return True, latency_ms
            
            finally:
                sock.close()
        
        except (asyncio.TimeoutError, socket.timeout, ConnectionRefusedError, OSError) as e:
            await logger.ainfo(
                "Proxy dead",
                ip=proxy.ip,
                port=proxy.port,
                reason=type(e).__name__
            )
            return False, 0.0
        
        except Exception as e:
            await logger.aerror(
                "Liveliness check error",
                ip=proxy.ip,
                port=proxy.port,
                error=str(e)
            )
            return False, 0.0
    
    async def validate_batch(self, proxies: list[ProxyModel]) -> list[ProxyModel]:
        """Validate batch of proxies"""
        tasks = [self.check_liveliness(p) for p in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        validated = []
        for proxy, result in zip(proxies, results):
            if isinstance(result, Exception):
                continue
            
            is_alive, latency = result
            proxy.is_alive = is_alive
            proxy.latency_ms = latency
            validated.append(proxy)
        
        return validated