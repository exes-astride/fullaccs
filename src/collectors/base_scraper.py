"""
Base abstract scraper class with fetch and parse methods
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.models.proxy import ProxyModel, ProxyBatch
from src.utils.http_client import HTTPClient
from src.core.exceptions import ExtractionException
import structlog

logger = structlog.get_logger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all proxy scrapers"""
    
    def __init__(
        self,
        name: str,
        url: str,
        extraction_config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.url = url
        self.extraction_config = extraction_config or {}
        self.http_client = None
    
    async def __aenter__(self):
        """Context manager entry"""
        self.http_client = HTTPClient()
        await self.http_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.http_client:
            await self.http_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def fetch(self) -> str:
        """Fetch content from URL"""
        if not self.http_client:
            raise ExtractionException("HTTP client not initialized")
        
        try:
            content = await self.http_client.get(self.url)
            await logger.ainfo(
                "Content fetched",
                source=self.name,
                url=self.url,
                size=len(content)
            )
            return content
        except Exception as e:
            await logger.aerror(
                "Fetch error",
                source=self.name,
                error=str(e)
            )
            raise ExtractionException(f"Failed to fetch {self.url}: {str(e)}")
    
    @abstractmethod
    async def parse(self, content: str) -> List[ProxyModel]:
        """Parse content and extract proxies - must be implemented by subclasses"""
        pass
    
    async def collect(self) -> ProxyBatch:
        """Collect proxies from source"""
        try:
            content = await self.fetch()
            proxies = await self.parse(content)
            
            batch = ProxyBatch(
                proxies=proxies,
                source_name=self.name,
                batch_id=f"{self.name}_{id(self)}",
                total_count=len(proxies)
            )
            
            await logger.ainfo(
                "Batch created",
                source=self.name,
                count=len(proxies)
            )
            
            return batch
        
        except Exception as e:
            await logger.aerror(
                "Collection failed",
                source=self.name,
                error=str(e)
            )
            raise ExtractionException(f"Collection from {self.name} failed: {str(e)}")