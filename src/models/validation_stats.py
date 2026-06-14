"""
Validation statistics and reporting models
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ValidationStats(BaseModel):
    """Statistics for validation run"""
    
    total_collected: int = Field(default=0)
    total_validated: int = Field(default=0)
    total_alive: int = Field(default=0)
    total_dead: int = Field(default=0)
    
    avg_latency_ms: float = Field(default=0)
    min_latency_ms: float = Field(default=0)
    max_latency_ms: float = Field(default=0)
    
    by_protocol: dict[str, int] = Field(default_factory=dict)
    by_anonymity: dict[str, int] = Field(default_factory=dict)
    by_country: dict[str, int] = Field(default_factory=dict)
    
    duration_seconds: float = Field(default=0)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_collected": 5000,
                "total_validated": 4500,
                "total_alive": 3200,
                "total_dead": 1300,
                "avg_latency_ms": 125.5,
                "min_latency_ms": 10,
                "max_latency_ms": 500,
                "by_protocol": {"http": 2000, "socks5": 1200},
                "by_anonymity": {"elite": 1500, "anonymous": 1200},
                "by_country": {"US": 1000, "CN": 800},
                "duration_seconds": 3600
            }
        }