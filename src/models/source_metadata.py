"""
Source metadata models
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SourceMetadata(BaseModel):
    """Metadata for proxy sources"""
    
    name: str = Field(min_length=1)
    url: str
    type: str = Field(description="html_table, json_api, github_raw, regex_text")
    enabled: bool = Field(default=True)
    priority: int = Field(default=1, ge=1, le=10)
    
    # Extraction configuration
    extraction_method: str
    extraction_config: Optional[dict] = Field(default=None)
    
    # Rate limiting
    requests_per_minute: int = Field(default=60)
    
    # Health metrics
    last_fetch_at: Optional[datetime] = Field(default=None)
    last_success_at: Optional[datetime] = Field(default=None)
    success_rate: float = Field(default=0, ge=0, le=100)
    total_proxies_collected: int = Field(default=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "example_source",
                "url": "https://example.com/proxies",
                "type": "html_table",
                "enabled": True,
                "priority": 5,
                "extraction_method": "table",
                "requests_per_minute": 60,
                "total_proxies_collected": 150
            }
        }