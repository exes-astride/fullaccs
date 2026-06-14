"""
JSON API scraper - extracts proxies from JSON API responses
"""

import json
from typing import List, Optional, Dict, Any
from src.models.proxy import ProxyModel, ProtocolType
from src.collectors.base_scraper import BaseScraper
from src.core.exceptions import ExtractionException
import structlog

logger = structlog.get_logger(__name__)


class JSONAPIScraper(BaseScraper):
    """Extract proxies from JSON API responses"""
    
    def __init__(
        self,
        name: str,
        url: str,
        extraction_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, url, extraction_config)
        
        self.data_path = extraction_config.get('data_path', 'data') if extraction_config else 'data'
        self.ip_field = extraction_config.get('ip_field', 'ip') if extraction_config else 'ip'
        self.port_field = extraction_config.get('port_field', 'port') if extraction_config else 'port'
        self.protocol_field = extraction_config.get('protocol_field', 'protocol') if extraction_config else 'protocol'
    
    async def parse(self, content: str) -> List[ProxyModel]:
        """Parse JSON and extract proxies"""
        proxies = []
        
        try:
            data = json.loads(content)
            
            # Navigate to data path if specified
            if self.data_path:
                for key in self.data_path.split('.'):
                    if isinstance(data, dict):
                        data = data.get(key, [])
                    elif isinstance(data, list):
                        break
            
            # Ensure data is iterable
            if not isinstance(data, list):
                data = [data] if data else []
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                try:
                    ip = item.get(self.ip_field)
                    port = item.get(self.port_field)
                    
                    if not ip or not port:
                        continue
                    
                    # Convert port to int
                    try:
                        port = int(port)
                    except (ValueError, TypeError):
                        continue
                    
                    # Get protocol
                    protocol = ProtocolType.HTTP
                    if self.protocol_field in item:
                        protocol_str = str(item.get(self.protocol_field)).lower()
                        if 'https' in protocol_str:
                            protocol = ProtocolType.HTTPS
                        elif 'socks5' in protocol_str:
                            protocol = ProtocolType.SOCKS5
                        elif 'socks4' in protocol_str:
                            protocol = ProtocolType.SOCKS4
                    
                    # Validate IP
                    if self._is_valid_ip(str(ip)):
                        proxy = ProxyModel(
                            ip=str(ip),
                            port=port,
                            protocol=protocol,
                            source_name=self.name
                        )
                        proxies.append(proxy)
                
                except (ValueError, TypeError, KeyError):
                    continue
            
            await logger.ainfo(
                "JSON API parsed",
                source=self.name,
                proxies_found=len(proxies)
            )
            
            return proxies
        
        except json.JSONDecodeError as e:
            await logger.aerror(
                "JSON parsing error",
                source=self.name,
                error=str(e)
            )
            raise ExtractionException(f"Failed to parse JSON from {self.name}: {str(e)}")
        
        except Exception as e:
            await logger.aerror(
                "JSON extraction error",
                source=self.name,
                error=str(e)
            )
            raise ExtractionException(f"Failed to extract proxies from {self.name}: {str(e)}")
    
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