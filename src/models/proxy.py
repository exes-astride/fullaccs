"""
Pydantic models for proxy validation and serialization
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class ProtocolType(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class AnonymityLevel(str, Enum):
    TRANSPARENT = "transparent"
    ANONYMOUS = "anonymous"
    ELITE = "elite"


class ProxyModel(BaseModel):
    """Strict proxy validation model"""
    
    ip: str
    port: int = Field(ge=1, le=65535)
    protocol: ProtocolType = Field(default=ProtocolType.HTTP)
    
    # Optional validation metrics
    latency_ms: Optional[float] = Field(default=None, ge=0)
    anonymity_level: Optional[AnonymityLevel] = Field(default=None)
    country_code: Optional[str] = Field(default=None)
    asn: Optional[str] = Field(default=None)
    isp: Optional[str] = Field(default=None)
    
    # Quality scoring
    quality_score: Optional[float] = Field(default=0, ge=0, le=100)
    is_alive: bool = Field(default=False)
    last_checked_at: Optional[str] = Field(default=None)
    
    # Metadata
    source_name: Optional[str] = Field(default=None)
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "ip": "192.168.1.1",
                "port": 8080,
                "protocol": "http",
                "latency_ms": 45.2,
                "anonymity_level": "elite",
                "country_code": "US",
                "quality_score": 85,
                "is_alive": True,
                "source_name": "source_1"
            }
        }
    
    @field_validator("ip")
    @classmethod
    def validate_ip_format(cls, v):
        """Validate IP address format"""
        parts = v.split(".")
        if len(parts) != 4:
            raise ValueError(f"Invalid IP format: {v}")
        
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError(f"Invalid IP octet: {num}")
            except ValueError:
                raise ValueError(f"Invalid IP octet: {part}")
        return v
    
    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v):
        """Validate ISO 3166 country code format"""
        if v and (len(v) != 2 or not v.isupper()):
            raise ValueError(f"Invalid country code: {v}")
        return v
    
    def to_proxy_string(self) -> str:
        """Convert to proxy URL format: protocol://ip:port"""
        return f"{self.protocol}://{self.ip}:{self.port}"
    
    def to_simple_format(self) -> str:
        """Convert to simple format: ip:port"""
        return f"{self.ip}:{self.port}"


class ProxyBatch(BaseModel):
    """Batch of proxies for bulk processing"""
    proxies: list[ProxyModel] = Field(default_factory=list)
    source_name: str
    batch_id: str
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "proxies": [],
                "source_name": "source_1",
                "batch_id": "batch_001",
                "total_count": 100
            }
        }