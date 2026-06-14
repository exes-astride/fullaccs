"""
Quick start script - example usage of the proxy collector
"""

import asyncio
from src.config.app_config import AppConfig, ProxySourceConfig
from src.collectors.factory import ScraperFactory
from src.deduplication.master_deduplicator import MasterDeduplicator
from src.validators.master_validator import MasterValidator
from src.exporters.master_exporter import MasterExporter
from src.core.pipeline_manager import PipelineManager
import structlog

logger = structlog.get_logger(__name__)


async def quick_start():
    """Quick start example"""
    
    # Define sources
    sources = [
        ProxySourceConfig(
            name="github_raw_example",
            url="https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            type="regex_text",
            enabled=True,
            priority=5,
            extraction_config={
                "pattern": r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)"
            }
        )
    ]
    
    # Create config
    config = AppConfig(
        sources=sources,
        max_concurrent_tasks=50,
        export={
            "output_dir": "outputs",
            "export_formats": ["txt", "json"]
        }
    )
    
    await logger.ainfo("Quick start initialized", sources_count=len(sources))
    
    # Create collectors
    collectors = [
        ScraperFactory.create_scraper(
            source_type=s.type,
            name=s.name,
            url=s.url,
            extraction_config=s.extraction_config
        )
        for s in sources
    ]
    
    # Create components
    pipeline = PipelineManager()
    deduplicator = MasterDeduplicator()
    validator = MasterValidator()
    exporter = MasterExporter()
    
    # Run pipeline
    result = await pipeline.run_full_pipeline(
        collectors=collectors,
        deduplicator=deduplicator,
        validator=validator,
        exporter=exporter
    )
    
    await logger.ainfo("Quick start complete", result=result)
    return result


if __name__ == "__main__":
    result = asyncio.run(quick_start())
    print(result)