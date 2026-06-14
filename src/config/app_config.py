"""
Configuration management - load from YAML, environment, or defaults
"""

import os
import yaml
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
import structlog

logger = structlog.get_logger(__name__)


class ProxySourceConfig(BaseSettings):
    """Configuration for a single proxy source"""
    
    name: str
    url: str
    type: str  # html_table, json_api, github_raw, regex_text
    enabled: bool = True
    priority: int = 1
    extraction_config: Optional[Dict[str, Any]] = None
    requests_per_minute: int = 60


class ValidatorConfig(BaseSettings):
    """Configuration for validators"""
    
    enable_liveliness: bool = True
    enable_protocol_detection: bool = True
    enable_anonymity_check: bool = True
    enable_latency_testing: bool = True
    enable_geolocation: bool = True
    min_quality_score: int = Field(default=50, ge=0, le=100)


class DeduplicationConfig(BaseSettings):
    """Configuration for deduplication"""
    
    use_early_aggregator: bool = True
    use_bloom_filter: bool = True
    use_redis: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0


class ExportConfig(BaseSettings):
    """Configuration for export formats"""
    
    output_dir: str = "outputs"
    export_formats: list[str] = ["txt", "json", "csv", "grouped"]
    enable_grouped_export: bool = True


class AppConfig(BaseSettings):
    """Main application configuration"""
    
    # Basic settings
    app_name: str = "Ultimate Proxy Collector"
    app_version: str = "1.0.0"
    
    # Proxy sources
    sources: list[ProxySourceConfig] = []
    
    # Components
    validators: ValidatorConfig = Field(default_factory=ValidatorConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    
    # Performance
    max_concurrent_tasks: int = 100
    timeout_seconds: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "AppConfig":
        """Load configuration from YAML file"""
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {yaml_path}")
            return cls(**data)
        
        except FileNotFoundError:
            logger.warning(f"Config file not found: {yaml_path}, using defaults")
            return cls()
        
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables"""
        logger.info("Loading configuration from environment variables")
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return self.model_dump()
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.sources:
            logger.warning("No proxy sources configured")
        
        if self.max_concurrent_tasks > 5000:
            logger.warning(f"Max concurrent tasks ({self.max_concurrent_tasks}) exceeds 5000, clamping to 5000")
            self.max_concurrent_tasks = 5000
        
        return True