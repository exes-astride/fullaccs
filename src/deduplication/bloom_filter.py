"""
Bloom filter - memory-efficient ultra-fast deduplication
"""

import hashlib
from typing import List
from src.models.proxy import ProxyModel
from src.core.constants import BLOOM_FILTER_SIZE, BLOOM_FILTER_HASH_FUNCTIONS
import structlog

logger = structlog.get_logger(__name__)


class BloomFilter:
    """Probabilistic Bloom filter for deduplication"""
    
    def __init__(
        self,
        size: int = BLOOM_FILTER_SIZE,
        hash_functions: int = BLOOM_FILTER_HASH_FUNCTIONS
    ):
        self.size = size
        self.hash_functions = hash_functions
        self.bit_array = [False] * size
        self.items_added = 0
    
    def _hash(self, item: str, seed: int) -> int:
        """Generate hash value using seed"""
        hash_obj = hashlib.md5((item + str(seed)).encode())
        return int(hash_obj.hexdigest(), 16) % self.size
    
    def add(self, item: str) -> None:
        """Add item to Bloom filter"""
        for seed in range(self.hash_functions):
            hash_index = self._hash(item, seed)
            self.bit_array[hash_index] = True
        
        self.items_added += 1
    
    def contains(self, item: str) -> bool:
        """Check if item might be in Bloom filter (can have false positives)"""
        for seed in range(self.hash_functions):
            hash_index = self._hash(item, seed)
            if not self.bit_array[hash_index]:
                return False
        
        return True
    
    def add_proxy(self, proxy: ProxyModel) -> None:
        """Add proxy to Bloom filter"""
        proxy_key = f"{proxy.ip}:{proxy.port}"
        self.add(proxy_key)
    
    def has_proxy(self, proxy: ProxyModel) -> bool:
        """Check if proxy exists in Bloom filter"""
        proxy_key = f"{proxy.ip}:{proxy.port}"
        return self.contains(proxy_key)
    
    def deduplicate_proxies(self, proxies: List[ProxyModel]) -> List[ProxyModel]:
        """Deduplicate proxies using Bloom filter"""
        unique_proxies = []
        duplicates = 0
        
        for proxy in proxies:
            if not self.has_proxy(proxy):
                unique_proxies.append(proxy)
                self.add_proxy(proxy)
            else:
                duplicates += 1
        
        logger.info(
            "Bloom filter deduplication",
            total=len(proxies),
            unique=len(unique_proxies),
            duplicates=duplicates,
            false_positive_rate=f"{(duplicates / len(proxies) * 100):.2f}%" if proxies else "0%"
        )
        
        return unique_proxies
    
    def get_stats(self) -> dict:
        """Get Bloom filter statistics"""
        set_bits = sum(self.bit_array)
        return {
            "size": self.size,
            "hash_functions": self.hash_functions,
            "items_added": self.items_added,
            "set_bits": set_bits,
            "load_factor": set_bits / self.size if self.size > 0 else 0,
            "memory_usage_bytes": self.size // 8
        }
    
    def clear(self) -> None:
        """Clear Bloom filter"""
        self.bit_array = [False] * self.size
        self.items_added = 0