"""
GitHub Raw scraper - extracts proxies from raw GitHub files
"""

import re
from typing import List, Optional, Dict, Any
from src.models.proxy import ProxyModel, ProtocolType
from src.collectors.base_scraper import BaseScraper
from src.core.exceptions import ExtractionException
import structlog

logger = structlog.get_logger(__name__)


class GitHubRawScraper(BaseScraper):
    """Extract proxies from GitHub raw files"""
    
    def __init__(
        self,
        name: str,
        url: str,
        extraction_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, url, extraction_config)
        
        # Ensure URL points to raw GitHub content
        if 'github.com' in url and 'raw' not in url:
            url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        
        self.url = url
        self.pattern = extraction_config.get('pattern', r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)') if extraction_config else r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)'
    
    async def parse(self, content: str) -> List[ProxyModel]:
        """Parse raw text and extract proxies"""
        proxies = []
        
        try:
            # Use regex to find all IP:port combinations
            matches = re.findall(self.pattern, content)
            
            for match in matches:
                try:
                    ip = match[0]
                    port = int(match[1])
                    
                    if self._is_valid_ip(ip) and 1 <= port <= 65535:
                        proxy = ProxyModel(
                            ip=ip,
                            port=port,
                            protocol=ProtocolType.HTTP,
                            source_name=self.name
                        )
                        proxies.append(proxy)
                
                except (ValueError, IndexError):
                    continue
            
            await logger.ainfo(
                "GitHub raw parsed",
                source=self.name,
                proxies_found=len(proxies)
            )
            
            return proxies
        
        except Exception as e:
            await logger.aerror(
                "GitHub raw parsing error",
                source=self.name,
                error=str(e)
            )
            raise ExtractionException(f"Failed to parse GitHub raw from {self.name}: {str(e)}")
    
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