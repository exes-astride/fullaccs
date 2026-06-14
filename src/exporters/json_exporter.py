"""
JSON exporter - detailed proxy metadata in JSON format
"""

import json
import os
from typing import List
from src.models.proxy import ProxyModel
from src.models.validation_stats import ValidationStats
from src.exporters.base_exporter import BaseExporter
from src.core.constants import ATOMIC_WRITE_TEMP_SUFFIX
import structlog

logger = structlog.get_logger(__name__)


class JSONExporter(BaseExporter):
    """Export proxies as JSON with full metadata"""
    
    async def export(self, proxies: List[ProxyModel], stats: ValidationStats) -> dict:
        """Export to JSON format with metadata"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        json_file = os.path.join(self.output_dir, "proxies.json")
        temp_file = json_file + ATOMIC_WRITE_TEMP_SUFFIX
        
        try:
            data = {
                "metadata": {
                    "total_proxies": len(proxies),
                    "stats": stats.model_dump(),
                    "generation_timestamp": stats.end_time.isoformat() if stats.end_time else None
                },
                "proxies": [proxy.model_dump() for proxy in proxies]
            }
            
            # Write to temp file
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Atomic move
            if os.path.exists(json_file):
                os.remove(json_file)
            os.rename(temp_file, json_file)
            
            await logger.ainfo(
                "JSON export complete",
                file=json_file,
                proxies=len(proxies)
            )
            
            return {
                "success": True,
                "files": [json_file],
                "proxies": len(proxies)
            }
        
        except Exception as e:
            await logger.aerror(
                "JSON export failed",
                error=str(e)
            )
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return {
                "success": False,
                "error": str(e)
            }