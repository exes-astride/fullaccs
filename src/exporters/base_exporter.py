"""
Base exporter class - abstract export interface
"""

from abc import ABC, abstractmethod
from typing import List
from src.models.proxy import ProxyModel
from src.models.validation_stats import ValidationStats
import structlog

logger = structlog.get_logger(__name__)


class BaseExporter(ABC):
    """Abstract base class for proxy exporters"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
    
    @abstractmethod
    async def export(self, proxies: List[ProxyModel], stats: ValidationStats) -> dict:
        """Export proxies - must be implemented by subclasses"""
        pass