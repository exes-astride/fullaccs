"""
Token bucket rate limiter to prevent IP bans and respect source limits
"""

import asyncio
import time
from typing import Optional
from src.core.constants import TOKEN_BUCKET_CAPACITY, TOKEN_BUCKET_REFILL_RATE
import structlog

logger = structlog.get_logger(__name__)


class TokenBucketRateLimiter:
    """Token bucket algorithm implementation for rate limiting"""
    
    def __init__(
        self,
        capacity: int = TOKEN_BUCKET_CAPACITY,
        refill_rate: float = TOKEN_BUCKET_REFILL_RATE
    ):
        """Initialize rate limiter
        
        capacity: Max tokens in bucket
        refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill_time = time.time()
        self.lock = asyncio.Lock()
    
    async def _refill(self) -> None:
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill_time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = now
    
    async def acquire(
        self,
        tokens: int = 1,
        timeout: Optional[float] = None
    ) -> bool:
        """Acquire tokens, waiting if necessary
        
        tokens: Number of tokens to acquire
        timeout: Max time to wait (None = wait forever)
        """
        start_time = time.time()
        
        while True:
            async with self.lock:
                await self._refill()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    await logger.ainfo(
                        "Tokens acquired",
                        requested=tokens,
                        remaining=self.tokens
                    )
                    return True
            
            if timeout and (time.time() - start_time) > timeout:
                await logger.awarning(
                    "Rate limiter timeout",
                    requested=tokens,
                    timeout=timeout
                )
                return False
            
            # Wait a bit before retrying
            await asyncio.sleep(0.1)
    
    async def wait_until_ready(self, tokens: int = 1) -> None:
        """Wait until tokens are available"""
        await self.acquire(tokens, timeout=None)
    
    def get_available_tokens(self) -> float:
        """Get current available tokens (non-blocking peek)"""
        elapsed = time.time() - self.last_refill_time
        return min(self.capacity, self.tokens + (elapsed * self.refill_rate))
    
    async def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        async with self.lock:
            await self._refill()
            return {
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
                "current_tokens": self.tokens,
                "available_tokens": self.get_available_tokens()
            }


class PerSourceRateLimiter:
    """Per-source rate limiter (requests per minute)"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.limiter = TokenBucketRateLimiter(
            capacity=requests_per_minute,
            refill_rate=requests_per_minute / 60.0  # Per second
        )
    
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire one request slot"""
        return await self.limiter.acquire(1, timeout)
    
    async def wait_until_ready(self) -> None:
        """Wait until ready to make request"""
        await self.limiter.wait_until_ready(1)