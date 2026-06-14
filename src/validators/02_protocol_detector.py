"""
Validator 2: Protocol Detector - HTTP, HTTPS, SOCKS4, SOCKS5 detection
"""

import asyncio
from typing import Optional
from src.models.proxy import ProxyModel, ProtocolType
from src.utils.http_client import HTTPClient
import structlog

logger = structlog.get_logger(__name__)


class ProtocolDetector:
    """Detect which protocols a proxy supports"""
    
    async def detect_protocol(self, proxy: ProxyModel) -> Optional[ProtocolType]:
        """Detect proxy protocol type"""
        if not proxy.is_alive:
            return proxy.protocol
        
        try:
            # Try HTTP first
            if await self._test_http_protocol(proxy):
                proxy.protocol = ProtocolType.HTTP
                await logger.ainfo(
                    "Protocol detected",
                    ip=proxy.ip,
                    port=proxy.port,
                    protocol="http"
                )
                return ProtocolType.HTTP
            
            # Try HTTPS
            if await self._test_https_protocol(proxy):
                proxy.protocol = ProtocolType.HTTPS
                await logger.ainfo(
                    "Protocol detected",
                    ip=proxy.ip,
                    port=proxy.port,
                    protocol="https"
                )
                return ProtocolType.HTTPS
            
            # Try SOCKS5
            if await self._test_socks5_protocol(proxy):
                proxy.protocol = ProtocolType.SOCKS5
                await logger.ainfo(
                    "Protocol detected",
                    ip=proxy.ip,
                    port=proxy.port,
                    protocol="socks5"
                )
                return ProtocolType.SOCKS5
            
            # Try SOCKS4
            if await self._test_socks4_protocol(proxy):
                proxy.protocol = ProtocolType.SOCKS4
                await logger.ainfo(
                    "Protocol detected",
                    ip=proxy.ip,
                    port=proxy.port,
                    protocol="socks4"
                )
                return ProtocolType.SOCKS4
            
            return proxy.protocol
        
        except Exception as e:
            await logger.aerror(
                "Protocol detection error",
                ip=proxy.ip,
                error=str(e)
            )
            return proxy.protocol
    
    async def _test_http_protocol(self, proxy: ProxyModel) -> bool:
        """Test HTTP protocol support"""
        try:
            async with HTTPClient() as client:
                url = f"http://{proxy.ip}:{proxy.port}"
                response = await client.get(url, timeout=5)
                return len(response) > 0
        except:
            return False
    
    async def _test_https_protocol(self, proxy: ProxyModel) -> bool:
        """Test HTTPS protocol support"""
        try:
            async with HTTPClient() as client:
                url = f"https://{proxy.ip}:{proxy.port}"
                response = await client.get(url, timeout=5)
                return len(response) > 0
        except:
            return False
    
    async def _test_socks5_protocol(self, proxy: ProxyModel) -> bool:
        """Test SOCKS5 protocol support"""
        # SOCKS5 handshake: Send greeting and check response
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(proxy.ip, proxy.port),
                timeout=5
            )
            
            # Send SOCKS5 greeting
            writer.write(b'\x05\x01\x00')
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(2), timeout=5)
            writer.close()
            
            return response[0] == 0x05
        except:
            return False
    
    async def _test_socks4_protocol(self, proxy: ProxyModel) -> bool:
        """Test SOCKS4 protocol support"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(proxy.ip, proxy.port),
                timeout=5
            )
            
            # Send SOCKS4 request
            writer.write(b'\x04\x01\x00\x50\x00\x00\x00\x01')
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(8), timeout=5)
            writer.close()
            
            return response[0] == 0x00 and response[1] in [0x5a, 0x5b]
        except:
            return False
    
    async def validate_batch(self, proxies: list[ProxyModel]) -> list[ProxyModel]:
        """Detect protocols for batch of proxies"""
        tasks = [self.detect_protocol(p) for p in proxies]
        await asyncio.gather(*tasks, return_exceptions=True)
        return proxies