"""
Plain Text exporter - simple IP:port format
"""

import os
from typing import List
from src.models.proxy import ProxyModel
from src.models.validation_stats import ValidationStats
from src.exporters.base_exporter import BaseExporter
from src.core.constants import ATOMIC_WRITE_TEMP_SUFFIX
import structlog

logger = structlog.get_logger(__name__)


class PlainTextExporter(BaseExporter):
    """Export proxies as plain text (IP:port)"""
    
    async def export(self, proxies: List[ProxyModel], stats: ValidationStats) -> dict:
        """Export to plain text format"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Main file
        main_file = os.path.join(self.output_dir, "proxies.txt")
        temp_file = main_file + ATOMIC_WRITE_TEMP_SUFFIX
        
        try:
            # Write to temp file first (atomic write)
            with open(temp_file, 'w') as f:
                for proxy in proxies:
                    f.write(f"{proxy.to_simple_format()}\n")
            
            # Atomic move
            if os.path.exists(main_file):
                os.remove(main_file)
            os.rename(temp_file, main_file)
            
            await logger.ainfo(
                "Plain text export complete",
                file=main_file,
                proxies=len(proxies)
            )
            
            return {
                "success": True,
                "files": [main_file],
                "proxies": len(proxies)
            }
        
        except Exception as e:
            await logger.aerror(
                "Plain text export failed",
                error=str(e)
            )
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return {
                "success": False,
                "error": str(e)
            }