"""
Master exporter - orchestrates all export formats
"""

from typing import List
from src.models.proxy import ProxyModel
from src.models.validation_stats import ValidationStats
from src.exporters.plain_text_exporter import PlainTextExporter
from src.exporters.json_exporter import JSONExporter
from src.exporters.csv_exporter import CSVExporter
from src.exporters.grouped_exporter import GroupedExporter
import structlog

logger = structlog.get_logger(__name__)


class MasterExporter:
    """Master exporter - exports to all formats"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        self.text_exporter = PlainTextExporter(output_dir)
        self.json_exporter = JSONExporter(output_dir)
        self.csv_exporter = CSVExporter(output_dir)
        self.grouped_exporter = GroupedExporter(output_dir)
    
    async def export(
        self,
        proxies: List[ProxyModel],
        stats: ValidationStats,
        formats: List[str] = None
    ) -> dict:
        """Export proxies to specified formats
        
        formats: List of export formats ['txt', 'json', 'csv', 'grouped']
        Default: all formats
        """
        if formats is None:
            formats = ['txt', 'json', 'csv', 'grouped']
        
        await logger.ainfo(
            "Starting master export",
            proxies=len(proxies),
            formats=formats
        )
        
        results = {}
        all_files = []
        
        try:
            # Export as plain text
            if 'txt' in formats:
                result = await self.text_exporter.export(proxies, stats)
                results['txt'] = result
                all_files.extend(result.get('files', []))
            
            # Export as JSON
            if 'json' in formats:
                result = await self.json_exporter.export(proxies, stats)
                results['json'] = result
                all_files.extend(result.get('files', []))
            
            # Export as CSV
            if 'csv' in formats:
                result = await self.csv_exporter.export(proxies, stats)
                results['csv'] = result
                all_files.extend(result.get('files', []))
            
            # Export grouped
            if 'grouped' in formats:
                result = await self.grouped_exporter.export(proxies, stats)
                results['grouped'] = result
                all_files.extend(result.get('files', []))
            
            await logger.ainfo(
                "Master export complete",
                formats_completed=len(results),
                total_files=len(all_files)
            )
            
            return {
                "success": True,
                "formats": results,
                "total_files": len(all_files),
                "all_files": all_files,
                "proxies_exported": len(proxies)
            }
        
        except Exception as e:
            await logger.aerror(
                "Master export failed",
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "partial_files": all_files
            }