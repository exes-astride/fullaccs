"""
Grouped exporter - organize proxies by country, protocol, anonymity
"""

import json
import os
from typing import List, Dict
from src.models.proxy import ProxyModel
from src.models.validation_stats import ValidationStats
from src.exporters.base_exporter import BaseExporter
from src.core.constants import ATOMIC_WRITE_TEMP_SUFFIX
import structlog

logger = structlog.get_logger(__name__)


class GroupedExporter(BaseExporter):
    """Export proxies grouped by various attributes"""
    
    async def export(self, proxies: List[ProxyModel], stats: ValidationStats) -> dict:
        """Export grouped proxies"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        exported_files = []
        
        try:
            # Group by country
            by_country = self._group_by_country(proxies)
            country_dir = os.path.join(self.output_dir, "by_country")
            os.makedirs(country_dir, exist_ok=True)
            for country, country_proxies in by_country.items():
                file_path = os.path.join(country_dir, f"{country}.txt")
                self._write_proxies(file_path, country_proxies)
                exported_files.append(file_path)
            
            # Group by protocol
            by_protocol = self._group_by_protocol(proxies)
            protocol_dir = os.path.join(self.output_dir, "by_protocol")
            os.makedirs(protocol_dir, exist_ok=True)
            for protocol, protocol_proxies in by_protocol.items():
                file_path = os.path.join(protocol_dir, f"{protocol}.txt")
                self._write_proxies(file_path, protocol_proxies)
                exported_files.append(file_path)
            
            # Group by anonymity
            by_anonymity = self._group_by_anonymity(proxies)
            anonymity_dir = os.path.join(self.output_dir, "by_anonymity")
            os.makedirs(anonymity_dir, exist_ok=True)
            for anonymity, anon_proxies in by_anonymity.items():
                file_path = os.path.join(anonymity_dir, f"{anonymity}.txt")
                self._write_proxies(file_path, anon_proxies)
                exported_files.append(file_path)
            
            await logger.ainfo(
                "Grouped export complete",
                files_created=len(exported_files),
                proxies=len(proxies)
            )
            
            return {
                "success": True,
                "files": exported_files,
                "proxies": len(proxies)
            }
        
        except Exception as e:
            await logger.aerror(
                "Grouped export failed",
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _group_by_country(proxies: List[ProxyModel]) -> Dict[str, List[ProxyModel]]:
        """Group proxies by country code"""
        grouped = {}
        for proxy in proxies:
            country = proxy.country_code or "UNKNOWN"
            if country not in grouped:
                grouped[country] = []
            grouped[country].append(proxy)
        return grouped
    
    @staticmethod
    def _group_by_protocol(proxies: List[ProxyModel]) -> Dict[str, List[ProxyModel]]:
        """Group proxies by protocol"""
        grouped = {}
        for proxy in proxies:
            protocol = proxy.protocol or "unknown"
            if protocol not in grouped:
                grouped[protocol] = []
            grouped[protocol].append(proxy)
        return grouped
    
    @staticmethod
    def _group_by_anonymity(proxies: List[ProxyModel]) -> Dict[str, List[ProxyModel]]:
        """Group proxies by anonymity level"""
        grouped = {}
        for proxy in proxies:
            anonymity = proxy.anonymity_level or "unknown"
            if anonymity not in grouped:
                grouped[anonymity] = []
            grouped[anonymity].append(proxy)
        return grouped
    
    @staticmethod
    def _write_proxies(file_path: str, proxies: List[ProxyModel]) -> None:
        """Write proxies to file"""
        with open(file_path, 'w') as f:
            for proxy in proxies:
                f.write(f"{proxy.to_simple_format()}\n")