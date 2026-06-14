"""
Redis state manager - persist deduplication state across runs
"""

import json
from typing import Optional, List, Set
from src.models.proxy import ProxyModel
import structlog

logger = structlog.get_logger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisStateManager:
    """Manage deduplication state using Redis"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        enabled: bool = True
    ):
        self.host = host
        self.port = port
        self.db = db
        self.enabled = enabled and REDIS_AVAILABLE
        self.client = None
        
        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True
                )
                # Test connection
                self.client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {str(e)}")
                self.enabled = False
    
    async def add_proxy(self, proxy: ProxyModel) -> bool:
        """Add proxy to Redis set"""
        if not self.enabled:
            return False
        
        try:
            proxy_key = f"{proxy.ip}:{proxy.port}"
            return self.client.sadd("seen_proxies", proxy_key) == 1
        except Exception as e:
            logger.error(f"Redis add error: {str(e)}")
            return False
    
    async def has_proxy(self, proxy: ProxyModel) -> bool:
        """Check if proxy exists in Redis set"""
        if not self.enabled:
            return False
        
        try:
            proxy_key = f"{proxy.ip}:{proxy.port}"
            return self.client.sismember("seen_proxies", proxy_key)
        except Exception as e:
            logger.error(f"Redis check error: {str(e)}")
            return False
    
    async def add_batch(self, proxies: List[ProxyModel]) -> int:
        """Add batch of proxies to Redis"""
        if not self.enabled:
            return 0
        
        try:
            proxy_keys = [f"{p.ip}:{p.port}" for p in proxies]
            return self.client.sadd("seen_proxies", *proxy_keys)
        except Exception as e:
            logger.error(f"Redis batch add error: {str(e)}")
            return 0
    
    async def deduplicate(self, proxies: List[ProxyModel]) -> List[ProxyModel]:
        """Deduplicate proxies against Redis state"""
        if not self.enabled:
            return proxies
        
        unique_proxies = []
        duplicates = 0
        
        try:
            for proxy in proxies:
                if not await self.has_proxy(proxy):
                    unique_proxies.append(proxy)
                    await self.add_proxy(proxy)
                else:
                    duplicates += 1
            
            logger.info(
                "Redis deduplication",
                total=len(proxies),
                unique=len(unique_proxies),
                duplicates=duplicates
            )
            
            return unique_proxies
        
        except Exception as e:
            logger.error(f"Redis deduplication error: {str(e)}")
            return proxies
    
    async def get_all_seen(self) -> Set[str]:
        """Get all seen proxy keys from Redis"""
        if not self.enabled:
            return set()
        
        try:
            return self.client.smembers("seen_proxies")
        except Exception as e:
            logger.error(f"Redis get all error: {str(e)}")
            return set()
    
    async def clear(self) -> None:
        """Clear all state from Redis"""
        if not self.enabled:
            return
        
        try:
            self.client.delete("seen_proxies")
            logger.info("Redis state cleared")
        except Exception as e:
            logger.error(f"Redis clear error: {str(e)}")
    
    async def get_stats(self) -> dict:
        """Get Redis state statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            count = self.client.scard("seen_proxies")
            return {
                "enabled": True,
                "total_seen": count,
                "host": self.host,
                "port": self.port,
                "db": self.db
            }
        except Exception as e:
            logger.error(f"Redis stats error: {str(e)}")
            return {"enabled": False, "error": str(e)}