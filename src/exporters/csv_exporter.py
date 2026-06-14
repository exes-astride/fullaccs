"""
CSV exporter - spreadsheet-friendly format
"""

import csv
import os
from typing import List
from src.models.proxy import ProxyModel
from src.models.validation_stats import ValidationStats
from src.exporters.base_exporter import BaseExporter
from src.core.constants import ATOMIC_WRITE_TEMP_SUFFIX
import structlog

logger = structlog.get_logger(__name__)


class CSVExporter(BaseExporter):
    """Export proxies as CSV"""
    
    async def export(self, proxies: List[ProxyModel], stats: ValidationStats) -> dict:
        """Export to CSV format"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        csv_file = os.path.join(self.output_dir, "proxies.csv")
        temp_file = csv_file + ATOMIC_WRITE_TEMP_SUFFIX
        
        try:
            with open(temp_file, 'w', newline='') as f:
                fieldnames = [
                    'ip', 'port', 'protocol', 'latency_ms', 'anonymity_level',
                    'country_code', 'asn', 'isp', 'quality_score', 'is_alive', 'source_name'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for proxy in proxies:
                    writer.writerow({
                        'ip': proxy.ip,
                        'port': proxy.port,
                        'protocol': proxy.protocol,
                        'latency_ms': proxy.latency_ms,
                        'anonymity_level': proxy.anonymity_level,
                        'country_code': proxy.country_code,
                        'asn': proxy.asn,
                        'isp': proxy.isp,
                        'quality_score': proxy.quality_score,
                        'is_alive': proxy.is_alive,
                        'source_name': proxy.source_name
                    })
            
            # Atomic move
            if os.path.exists(csv_file):
                os.remove(csv_file)
            os.rename(temp_file, csv_file)
            
            await logger.ainfo(
                "CSV export complete",
                file=csv_file,
                proxies=len(proxies)
            )
            
            return {
                "success": True,
                "files": [csv_file],
                "proxies": len(proxies)
            }
        
        except Exception as e:
            await logger.aerror(
                "CSV export failed",
                error=str(e)
            )
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return {
                "success": False,
                "error": str(e)
            }