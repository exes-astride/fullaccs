"""
Main pipeline orchestrator: Collect -> Dedup -> Verify -> Export
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from src.models.proxy import ProxyModel, ProxyBatch
from src.models.validation_stats import ValidationStats
from src.core.exceptions import ProxyCollectorException
from src.utils.structured_logger import get_logger
import structlog

logger = structlog.get_logger(__name__)


class PipelineManager:
    """Orchestrates the complete proxy collection pipeline"""
    
    def __init__(self):
        self.collected_proxies: List[ProxyModel] = []
        self.deduplicated_proxies: List[ProxyModel] = []
        self.validated_proxies: List[ProxyModel] = []
        self.stats = ValidationStats(
            start_time=datetime.now()
        )
    
    async def collect_phase(
        self,
        collectors: List
    ) -> int:
        """Phase 1: Collect proxies from multiple sources"""
        await logger.ainfo("Starting collection phase", num_collectors=len(collectors))
        
        try:
            for collector in collectors:
                try:
                    batch = await collector.collect()
                    self.collected_proxies.extend(batch.proxies)
                    await logger.ainfo(
                        "Batch collected",
                        source=batch.source_name,
                        count=len(batch.proxies)
                    )
                except Exception as e:
                    await logger.aerror(
                        "Collection error",
                        source=getattr(collector, 'name', 'unknown'),
                        error=str(e)
                    )
                    continue
            
            self.stats.total_collected = len(self.collected_proxies)
            await logger.ainfo(
                "Collection phase complete",
                total_collected=self.stats.total_collected
            )
            return self.stats.total_collected
        
        except Exception as e:
            await logger.aerror("Collection phase failed", error=str(e))
            raise ProxyCollectorException(f"Collection failed: {str(e)}")
    
    async def deduplication_phase(
        self,
        deduplicator
    ) -> int:
        """Phase 2: Remove duplicates"""
        await logger.ainfo(
            "Starting deduplication phase",
            input_count=len(self.collected_proxies)
        )
        
        try:
            self.deduplicated_proxies = await deduplicator.deduplicate(
                self.collected_proxies
            )
            
            duplicates_removed = len(self.collected_proxies) - len(self.deduplicated_proxies)
            await logger.ainfo(
                "Deduplication complete",
                duplicates_removed=duplicates_removed,
                remaining=len(self.deduplicated_proxies)
            )
            
            return len(self.deduplicated_proxies)
        
        except Exception as e:
            await logger.aerror("Deduplication failed", error=str(e))
            raise ProxyCollectorException(f"Deduplication failed: {str(e)}")
    
    async def validation_phase(
        self,
        validator
    ) -> int:
        """Phase 3: 5-dimensional validation (liveliness, protocol, anonymity, latency, geo)"""
        await logger.ainfo(
            "Starting validation phase",
            input_count=len(self.deduplicated_proxies)
        )
        
        try:
            self.validated_proxies = await validator.validate_batch(
                self.deduplicated_proxies
            )
            
            alive_count = sum(1 for p in self.validated_proxies if p.is_alive)
            dead_count = len(self.validated_proxies) - alive_count
            
            self.stats.total_validated = len(self.validated_proxies)
            self.stats.total_alive = alive_count
            self.stats.total_dead = dead_count
            
            # Calculate average latency
            latencies = [p.latency_ms for p in self.validated_proxies if p.latency_ms]
            if latencies:
                self.stats.avg_latency_ms = sum(latencies) / len(latencies)
                self.stats.min_latency_ms = min(latencies)
                self.stats.max_latency_ms = max(latencies)
            
            await logger.ainfo(
                "Validation complete",
                total_validated=self.stats.total_validated,
                alive=self.stats.total_alive,
                dead=self.stats.total_dead,
                avg_latency=self.stats.avg_latency_ms
            )
            
            return alive_count
        
        except Exception as e:
            await logger.aerror("Validation failed", error=str(e))
            raise ProxyCollectorException(f"Validation failed: {str(e)}")
    
    async def export_phase(
        self,
        exporter
    ) -> dict:
        """Phase 4: Export results to various formats"""
        await logger.ainfo(
            "Starting export phase",
            total_proxies=len(self.validated_proxies)
        )
        
        try:
            self.stats.end_time = datetime.now()
            self.stats.duration_seconds = (
                self.stats.end_time - self.stats.start_time
            ).total_seconds()
            
            export_result = await exporter.export(
                self.validated_proxies,
                self.stats
            )
            
            await logger.ainfo(
                "Export complete",
                files_created=len(export_result.get('files', [])),
                duration=self.stats.duration_seconds
            )
            
            return export_result
        
        except Exception as e:
            await logger.aerror("Export failed", error=str(e))
            raise ProxyCollectorException(f"Export failed: {str(e)}")
    
    async def run_full_pipeline(
        self,
        collectors: List,
        deduplicator,
        validator,
        exporter
    ) -> dict:
        """Run complete pipeline: Collect -> Dedup -> Validate -> Export"""
        await logger.ainfo("Pipeline execution started")
        
        try:
            # Phase 1: Collection
            collected = await self.collect_phase(collectors)
            
            # Phase 2: Deduplication
            deduplicated = await self.deduplication_phase(deduplicator)
            
            # Phase 3: Validation
            validated = await self.validation_phase(validator)
            
            # Phase 4: Export
            export_result = await self.export_phase(exporter)
            
            await logger.ainfo(
                "Pipeline execution complete",
                collected=collected,
                deduplicated=deduplicated,
                validated=validated,
                duration=self.stats.duration_seconds
            )
            
            return {
                "success": True,
                "stats": self.stats.model_dump(),
                "export_result": export_result
            }
        
        except Exception as e:
            await logger.aerror("Pipeline execution failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "stats": self.stats.model_dump()
            }
    
    def get_stats(self) -> ValidationStats:
        """Get current pipeline statistics"""
        return self.stats