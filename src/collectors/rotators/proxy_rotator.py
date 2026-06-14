"""
Proxy rotator - use own proxies for scraping to bypass IP blocks
"""

import random
from typing import List, Optional
from src.models.proxy import ProxyModel
import structlog

logger = structlog.get_logger(__name__)


class ProxyRotator:
    """Rotate through available proxies for scraping"""
    
    def __init__(self, available_proxies: List[ProxyModel]):
        self.available_proxies = available_proxies
        self.current_index = 0
    
    def get_next(self) -> Optional[ProxyModel]:
        """Get next proxy in rotation"""
        if not self.available_proxies:
            return None
        
        proxy = self.available_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.available_proxies)
        
        logger.info(
            "Proxy rotated",
            ip=proxy.ip,
            port=proxy.port,
            index=self.current_index
        )
        
        return proxy
    
    def get_random(self) -> Optional[ProxyModel]:
        """Get random proxy"""
        if not self.available_proxies:
            return None
        
        proxy = random.choice(self.available_proxies)
        
        logger.info(
            "Random proxy selected",
            ip=proxy.ip,
            port=proxy.port
        )
        
        return proxy
    
    def get_healthiest(self) -> Optional[ProxyModel]:
        """Get proxy with highest quality score"""
        if not self.available_proxies:
            return None
        
        proxy = max(self.available_proxies, key=lambda p: p.quality_score or 0)
        
        logger.info(
            "Healthiest proxy selected",
            ip=proxy.ip,
            port=proxy.port,
            quality_score=proxy.quality_score
        )
        
        return proxy
    
    def add_proxy(self, proxy: ProxyModel) -> None:
        """Add new proxy to rotation pool"""
        self.available_proxies.append(proxy)
        logger.info("Proxy added to rotation", ip=proxy.ip, port=proxy.port)
    
    def remove_proxy(self, proxy: ProxyModel) -> None:
        """Remove proxy from rotation pool"""
        try:
            self.available_proxies.remove(proxy)
            logger.info("Proxy removed from rotation", ip=proxy.ip, port=proxy.port)
        except ValueError:
            pass