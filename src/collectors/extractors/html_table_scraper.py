"""
HTML Table scraper - extracts proxies from HTML tables
"""

import re
from typing import List, Optional, Dict, Any
from src.models.proxy import ProxyModel, ProtocolType
from src.collectors.base_scraper import BaseScraper
from src.core.exceptions import ExtractionException
import structlog

logger = structlog.get_logger(__name__)

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class HTMLTableScraper(BaseScraper):
    """Extract proxies from HTML tables"""
    
    def __init__(
        self,
        name: str,
        url: str,
        extraction_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, url, extraction_config)
        
        self.table_selector = extraction_config.get('table_selector', 'table') if extraction_config else 'table'
        self.ip_column = extraction_config.get('ip_column', 0) if extraction_config else 0
        self.port_column = extraction_config.get('port_column', 1) if extraction_config else 1
        self.protocol_column = extraction_config.get('protocol_column', 2) if extraction_config else 2
    
    async def parse(self, content: str) -> List[ProxyModel]:
        """Parse HTML table and extract proxies"""
        if not BS4_AVAILABLE:
            raise ExtractionException("BeautifulSoup4 not installed. Install with: pip install beautifulsoup4")
        
        proxies = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            tables = soup.select(self.table_selector)
            
            if not tables:
                await logger.awarning(
                    "No tables found",
                    source=self.name,
                    selector=self.table_selector
                )
                return proxies
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) <= max(self.ip_column, self.port_column):
                        continue
                    
                    try:
                        ip = cells[self.ip_column].get_text(strip=True)
                        port_str = cells[self.port_column].get_text(strip=True)
                        
                        # Extract port number
                        port_match = re.search(r'\d+', port_str)
                        if not port_match:
                            continue
                        
                        port = int(port_match.group())
                        
                        # Get protocol if column exists
                        protocol = ProtocolType.HTTP
                        if len(cells) > self.protocol_column:
                            protocol_str = cells[self.protocol_column].get_text(strip=True).lower()
                            if 'https' in protocol_str:
                                protocol = ProtocolType.HTTPS
                            elif 'socks5' in protocol_str:
                                protocol = ProtocolType.SOCKS5
                            elif 'socks4' in protocol_str:
                                protocol = ProtocolType.SOCKS4
                        
                        # Validate IP format
                        if self._is_valid_ip(ip):
                            proxy = ProxyModel(
                                ip=ip,
                                port=port,
                                protocol=protocol,
                                source_name=self.name
                            )
                            proxies.append(proxy)
                    
                    except (ValueError, IndexError) as e:
                        continue
            
            await logger.ainfo(
                "HTML table parsed",
                source=self.name,
                proxies_found=len(proxies)
            )
            
            return proxies
        
        except Exception as e:
            await logger.aerror(
                "HTML parsing error",
                source=self.name,
                error=str(e)
            )
            raise ExtractionException(f"Failed to parse HTML from {self.name}: {str(e)}")
    
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