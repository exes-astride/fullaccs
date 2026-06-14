"""
Master deduplicator - multi-layer duplicate removal
"""

from typing import List
from src.models.proxy import ProxyModel
from src.deduplication.early_aggregator import EarlyAggregator
from src.deduplication.bloom_filter import BloomFilter
from src.deduplication.redis_state_manager import RedisStateManager
import structlog

logger = structlog.get_logger(__name__)


class MasterDeduplicator:
    """Multi-layer deduplication using Sets, Bloom filters, and Redis"""
    
    def __init__(
        self,
        use_bloom_filter: bool = True,
        use_redis: bool = False,
        redis_config: dict = None
    ):
        self.early_aggregator = EarlyAggregator()
        
        self.use_bloom_filter = use_bloom_filter
        self.bloom_filter = BloomFilter() if use_bloom_filter else None
        
        self.use_redis = use_redis
        if use_redis and redis_config:
            self.redis_manager = RedisStateManager(**redis_config)
        else:
            self.redis_manager = None
    
    async def deduplicate(self, proxies: List[ProxyModel]) -> List[ProxyModel]:
        """Multi-layer deduplication pipeline"""
        await logger.ainfo(
            "Starting deduplication",
            total_proxies=len(proxies),
            use_bloom_filter=self.use_bloom_filter,
            use_redis=self.use_redis
        )
        
        # Layer 1: Early aggregation (Set-based)
        unique_after_early = []
        for proxy in proxies:
            if self.early_aggregator.add_proxy(proxy):
                unique_after_early.append(proxy)
        
        await logger.ainfo(
            "Layer 1: Early aggregation complete",
            input=len(proxies),
            output=len(unique_after_early)
        )
        
        # Layer 2: Bloom filter (if enabled)
        if self.use_bloom_filter and self.bloom_filter:
            unique_after_bloom = self.bloom_filter.deduplicate_proxies(unique_after_early)
            await logger.ainfo(
                "Layer 2: Bloom filter complete",
                input=len(unique_after_early),
                output=len(unique_after_bloom)
            )
        else:
            unique_after_bloom = unique_after_early
        
        # Layer 3: Redis state manager (if enabled)
        if self.use_redis and self.redis_manager:
            unique_after_redis = await self.redis_manager.deduplicate(unique_after_bloom)
            await logger.ainfo(
                "Layer 3: Redis deduplication complete",
                input=len(unique_after_bloom),
                output=len(unique_after_redis)
            )
        else:
            unique_after_redis = unique_after_bloom
        
        await logger.ainfo(
            "Deduplication complete",
            original=len(proxies),
            deduplicated=len(unique_after_redis),
            removed=len(proxies) - len(unique_after_redis)
        )
        
        return unique_after_redis
    
    def get_stats(self) -> dict:
        """Get deduplication statistics"""
        stats = {
            "early_aggregator": self.early_aggregator.get_stats()
        }
        
        if self.use_bloom_filter and self.bloom_filter:
            stats["bloom_filter"] = self.bloom_filter.get_stats()
        
        if self.use_redis and self.redis_manager:
            import asyncio
            stats["redis"] = asyncio.run(self.redis_manager.get_stats())
        
        return stats