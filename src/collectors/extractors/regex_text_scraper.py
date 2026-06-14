"""
Regex Text scraper - extracts proxies using custom regex patterns
"""

import re
from typing import List, Optional, Dict, Any
from src.models.proxy import ProxyModel, ProtocolType
from src.collectors.base_scraper import BaseScraper
from src.core.exceptions import ExtractionException
import structlog

logger = structlog.get_logger(__name__)


class RegexTextScraper(BaseScraper):
    """Extract proxies using custom regex patterns"""
    
    def __init__(
        self,
        name: str,
        url: str,
        extraction_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, url, extraction_config)
        
        self.pattern = extraction_config.get('pattern', r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)') if extraction_config else r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)'
        self.protocol = extraction_config.get('protocol', 'http').lower() if extraction_config else 'http'
    
    async def parse(self, content: str) -> List[ProxyModel]:
        """Parse content using regex pattern"""
        proxies = []
        
        try:
            # Find all matches using the pattern
            matches = re.findall(self.pattern, content, re.MULTILINE)
            
            # Map protocol string to ProtocolType
            protocol_map = {
                'http': ProtocolType.HTTP,
                'https': ProtocolType.HTTPS,
                'socks4': ProtocolType.SOCKS4,
                'socks5': ProtocolType.SOCKS5
            }
            protocol = protocol_map.get(self.protocol, ProtocolType.HTTP)
            
            for match in matches:
                try:
                    # Handle different match types (tuple or single match)
                    if isinstance(match, tuple):
                        ip = match[0]
                        port = int(match[1]) if len(match) > 1 else 80
                    else:
                        # If single match, try to parse as IP:port
                        parts = match.split(':')
                        if len(parts) != 2:
                            continue
                        ip, port = parts[0], int(parts[1])
                    
                    if self._is_valid_ip(ip) and 1 <= port <= 65535:
                        proxy = ProxyModel(
                            ip=ip,
                            port=port,
                            protocol=protocol,
                            source_name=self.name
                        )
                        proxies.append(proxy)
                
                except (ValueError, IndexError, TypeError):
                    continue
            
            await logger.ainfo(
                "Regex text parsed",
                source=self.name,
                proxies_found=len(proxies)
            )
            
            return proxies
        
        except Exception as e:
            await logger.aerror(
                "Regex text parsing error",
                source=self.name,
                error=str(e)
            )
            raise ExtractionException(f"Failed to parse text from {self.name}: {str(e)}")
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Validate IP address format"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except ValueError:
            return False