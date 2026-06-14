"""
Scoring Engine - Assign quality scores to proxies
"""

from typing import Optional
from src.models.proxy import ProxyModel, AnonymityLevel
from src.core.constants import ANONYMITY_LEVELS, GOOD_QUALITY_SCORE, EXCELLENT_QUALITY_SCORE
import structlog

logger = structlog.get_logger(__name__)


class ScoringEngine:
    """Advanced quality scoring for proxies (0-100)"""
    
    # Scoring weights
    WEIGHTS = {
        "liveliness": 0.40,      # 40%
        "latency": 0.20,          # 20%
        "anonymity": 0.20,        # 20%
        "geolocation": 0.10,      # 10%
        "protocol": 0.10          # 10%
    }
    
    def calculate_score(self, proxy: ProxyModel) -> float:
        """Calculate comprehensive quality score"""
        score = 0.0
        
        # Liveliness score (40 points max)
        if proxy.is_alive:
            score += self.WEIGHTS["liveliness"] * 100
        
        # Latency score (20 points max)
        latency_score = self._calculate_latency_score(proxy.latency_ms)
        score += self.WEIGHTS["latency"] * latency_score
        
        # Anonymity score (20 points max)
        anonymity_score = self._calculate_anonymity_score(proxy.anonymity_level)
        score += self.WEIGHTS["anonymity"] * anonymity_score
        
        # Geolocation score (10 points max)
        if proxy.country_code:
            score += self.WEIGHTS["geolocation"] * 100
        
        # Protocol score (10 points max)
        if proxy.protocol:
            score += self.WEIGHTS["protocol"] * 100
        
        proxy.quality_score = min(100, max(0, score))
        
        logger.info(
            "Quality score calculated",
            ip=proxy.ip,
            score=proxy.quality_score,
            alive=proxy.is_alive,
            latency=proxy.latency_ms,
            anonymity=proxy.anonymity_level
        )
        
        return proxy.quality_score
    
    def _calculate_latency_score(self, latency_ms: Optional[float]) -> float:
        """Score based on latency (lower is better)"""
        if not latency_ms:
            return 0.0
        
        if latency_ms < 100:
            return 100.0  # Excellent
        elif latency_ms < 300:
            return 80.0   # Good
        elif latency_ms < 500:
            return 60.0   # Fair
        elif latency_ms < 1000:
            return 40.0   # Poor
        else:
            return 20.0   # Very poor
    
    def _calculate_anonymity_score(self, anonymity_level: Optional[str]) -> float:
        """Score based on anonymity level"""
        if not anonymity_level:
            return 0.0
        
        anonymity_lower = anonymity_level.lower() if isinstance(anonymity_level, str) else str(anonymity_level).lower()
        
        if 'elite' in anonymity_lower:
            return 100.0
        elif 'anonymous' in anonymity_lower:
            return 75.0
        elif 'transparent' in anonymity_lower:
            return 25.0
        else:
            return 50.0
    
    async def score_batch(self, proxies: list[ProxyModel]) -> list[ProxyModel]:
        """Score batch of proxies"""
        import asyncio
        
        scored_proxies = []
        for proxy in proxies:
            self.calculate_score(proxy)
            scored_proxies.append(proxy)
        
        # Log statistics
        excellent = sum(1 for p in scored_proxies if p.quality_score >= EXCELLENT_QUALITY_SCORE)
        good = sum(1 for p in scored_proxies if GOOD_QUALITY_SCORE <= p.quality_score < EXCELLENT_QUALITY_SCORE)
        
        logger.info(
            "Batch scoring complete",
            total=len(scored_proxies),
            excellent=excellent,
            good=good,
            avg_score=sum(p.quality_score or 0 for p in scored_proxies) / len(scored_proxies) if scored_proxies else 0
        )
        
        return scored_proxies