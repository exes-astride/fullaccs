"""
Scraper factory - dynamically loads scrapers based on source configuration
"""

from typing import Optional, Dict, Any
from src.collectors.base_scraper import BaseScraper
from src.collectors.extractors.html_table_scraper import HTMLTableScraper
from src.collectors.extractors.json_api_scraper import JSONAPIScraper
from src.collectors.extractors.github_raw_scraper import GitHubRawScraper
from src.collectors.extractors.regex_text_scraper import RegexTextScraper
from src.core.exceptions import ConfigurationException
import structlog

logger = structlog.get_logger(__name__)


class ScraperFactory:
    """Factory for creating scrapers based on source type"""
    
    SCRAPER_TYPES = {
        'html_table': HTMLTableScraper,
        'json_api': JSONAPIScraper,
        'github_raw': GitHubRawScraper,
        'regex_text': RegexTextScraper
    }
    
    @classmethod
    def create_scraper(
        cls,
        source_type: str,
        name: str,
        url: str,
        extraction_config: Optional[Dict[str, Any]] = None
    ) -> BaseScraper:
        """Create scraper instance based on source type"""
        
        if source_type not in cls.SCRAPER_TYPES:
            raise ConfigurationException(
                f"Unknown source type: {source_type}. "
                f"Supported types: {', '.join(cls.SCRAPER_TYPES.keys())}"
            )
        
        scraper_class = cls.SCRAPER_TYPES[source_type]
        
        logger.info(
            "Creating scraper",
            source_type=source_type,
            name=name,
            url=url
        )
        
        return scraper_class(
            name=name,
            url=url,
            extraction_config=extraction_config
        )