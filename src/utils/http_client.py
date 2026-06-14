"""
HTTP client with retry logic, timeout handling, and session management
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any
from src.core.constants import DEFAULT_HEADERS, DEFAULT_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF_FACTOR
from src.core.exceptions import SourceException
import structlog

logger = structlog.get_logger(__name__)


class HTTPClient:
    """Advanced HTTP client with retry and timeout handling"""
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        backoff_factor: float = RETRY_BACKOFF_FACTOR
    ):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """GET request with retry logic"""
        if not self.session:
            raise SourceException("HTTP client session not initialized")
        
        headers = headers or DEFAULT_HEADERS
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    ssl=False,
                    **kwargs
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        await logger.ainfo("HTTP GET success", url=url, status=response.status)
                        return content
                    elif response.status in [429, 503]:
                        # Rate limited or service unavailable - retry
                        await asyncio.sleep(self.backoff_factor ** attempt)
                        continue
                    else:
                        raise SourceException(f"HTTP error {response.status} for {url}")
            
            except asyncio.TimeoutError:
                await logger.ainfo(
                    "HTTP timeout",
                    url=url,
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.backoff_factor ** attempt)
                else:
                    raise SourceException(f"Timeout after {self.max_retries} retries for {url}")
            
            except aiohttp.ClientError as e:
                await logger.ainfo(
                    "HTTP client error",
                    url=url,
                    error=str(e),
                    attempt=attempt + 1
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.backoff_factor ** attempt)
                else:
                    raise SourceException(f"Connection error for {url}: {str(e)}")
        
        raise SourceException(f"Failed to fetch {url} after {self.max_retries} retries")
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        """POST request with retry logic"""
        if not self.session:
            raise SourceException("HTTP client session not initialized")
        
        headers = headers or DEFAULT_HEADERS
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    url,
                    data=data,
                    json=json,
                    headers=headers,
                    ssl=False,
                    **kwargs
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        await logger.ainfo("HTTP POST success", url=url, status=response.status)
                        return content
                    elif response.status in [429, 503]:
                        await asyncio.sleep(self.backoff_factor ** attempt)
                        continue
                    else:
                        raise SourceException(f"HTTP error {response.status} for {url}")
            
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.backoff_factor ** attempt)
                else:
                    raise SourceException(f"Timeout after {self.max_retries} retries for {url}")
            
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.backoff_factor ** attempt)
                else:
                    raise SourceException(f"Connection error for {url}: {str(e)}")
        
        raise SourceException(f"Failed to POST {url} after {self.max_retries} retries")