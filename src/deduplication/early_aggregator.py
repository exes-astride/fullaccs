"""
Early aggregator - basic Set() deduplication during scraping
"""

from typing import List, Set
from src.models.proxy import ProxyModel
import structlog

logger = structlog.get_logger(__name__)


class EarlyAggregator:
    """Fast deduplication using Python sets"""
    
    def __init__(self):
        self.seen_proxies: Set[str] = set()
        self.unique_proxies: List[ProxyModel] = []
    
    def add_proxy(self, proxy: ProxyModel) -> bool:
        """Add proxy if not already seen
        
        Returns: True if added, False if duplicate
        """
        proxy_key = f"{proxy.ip}:{proxy.port}"
        
        if proxy_key in self.seen_proxies:
            logger.debug(f"Duplicate proxy detected: {proxy_key}")
            return False
        
        self.seen_proxies.add(proxy_key)
        self.unique_proxies.append(proxy)
        return True
    
    def add_batch(self, proxies: List[ProxyModel]) -> int:
        """Add batch of proxies
        
        Returns: Number of unique proxies added
        """
        added_count = 0
        
        for proxy in proxies:
            if self.add_proxy(proxy):
                added_count += 1
        
        logger.info(
            "Batch aggregated",
            total=len(proxies),
            added=added_count,
            duplicates=len(proxies) - added_count
        )
        
        return added_count
    
    def get_unique(self) -> List[ProxyModel]:
        """Get all unique proxies"""
        return self.unique_proxies.copy()
    
    def get_stats(self) -> dict:
        """Get aggregation statistics"""
        return {
            "unique_count": len(self.unique_proxies),
            "duplicate_count": len(self.seen_proxies) - len(self.unique_proxies),
            "total_seen": len(self.seen_proxies)
        }
    
    def clear(self) -> None:
        """Clear all aggregated data"""
        self.seen_proxies.clear()
        self.unique_proxies.clear()