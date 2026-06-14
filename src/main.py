"""
Main entry point - orchestrate the complete proxy collection pipeline
"""

import asyncio
import sys
from datetime import datetime
from src.config.app_config import AppConfig
from src.utils.structured_logger import setup_logger
from src.core.pipeline_manager import PipelineManager
from src.collectors.factory import ScraperFactory
from src.deduplication.master_deduplicator import MasterDeduplicator
from src.validators.master_validator import MasterValidator
from src.exporters.master_exporter import MasterExporter
import structlog

logger = structlog.get_logger(__name__)


async def main():
    """Main entry point for proxy collector"""
    
    # Setup logging
    setup_logger()
    
    await logger.ainfo("Ultimate Proxy Collector - Starting")
    
    try:
        # Load configuration
        config = AppConfig.from_yaml("config.yaml")
        config.validate()
        
        await logger.ainfo(
            "Configuration loaded",
            app_name=config.app_name,
            version=config.app_version,
            sources_count=len(config.sources)
        )
        
        # Initialize components
        pipeline = PipelineManager()
        deduplicator = MasterDeduplicator(
            use_bloom_filter=config.deduplication.use_bloom_filter,
            use_redis=config.deduplication.use_redis,
            redis_config={
                'host': config.deduplication.redis_host,
                'port': config.deduplication.redis_port,
                'db': config.deduplication.redis_db
            } if config.deduplication.use_redis else None
        )
        validator = MasterValidator()
        exporter = MasterExporter(config.export.output_dir)
        
        # Create scrapers from configuration
        collectors = []
        for source_config in config.sources:
            if not source_config.enabled:
                await logger.ainfo(f"Skipping disabled source: {source_config.name}")
                continue
            
            try:
                scraper = ScraperFactory.create_scraper(
                    source_type=source_config.type,
                    name=source_config.name,
                    url=source_config.url,
                    extraction_config=source_config.extraction_config
                )
                collectors.append(scraper)
                await logger.ainfo(f"Scraper created: {source_config.name}")
            
            except Exception as e:
                await logger.aerror(
                    f"Failed to create scraper for {source_config.name}: {str(e)}"
                )
                continue
        
        if not collectors:
            await logger.awarning("No collectors available")
            return {"success": False, "error": "No collectors configured"}
        
        # Run complete pipeline
        result = await pipeline.run_full_pipeline(
            collectors=collectors,
            deduplicator=deduplicator,
            validator=validator,
            exporter=exporter
        )
        
        await logger.ainfo(
            "Pipeline execution complete",
            success=result.get("success"),
            stats=result.get("stats")
        )
        
        return result
    
    except Exception as e:
        await logger.aerror(
            "Fatal error",
            error=str(e),
            exc_info=True
        )
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Run async main
    result = asyncio.run(main())
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)