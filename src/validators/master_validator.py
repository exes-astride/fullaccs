"""
Master validator orchestrator - runs all 5-dimensional validation
"""

import asyncio
from typing import List
from src.models.proxy import ProxyModel
from src.validators.01_liveliness_tcp import TCPLivelinessValidator
from src.validators.02_protocol_detector import ProtocolDetector
from src.validators.03_anonymity_check import AnonymityChecker
from src.validators.04_latency_tester import LatencyTester
from src.validators.05_geo_locator import GeoLocator
from src.core.constants import MIN_QUALITY_SCORE
import structlog

logger = structlog.get_logger(__name__)


class MasterValidator:
    """Orchestrates all 5-dimensional validation"""
    
    def __init__(self):
        self.liveliness_validator = TCPLivelinessValidator()
        self.protocol_detector = ProtocolDetector()
        self.anonymity_checker = AnonymityChecker()
        self.latency_tester = LatencyTester()
        self.geo_locator = GeoLocator()
    
    def _calculate_quality_score(self, proxy: ProxyModel) -> float:
        """Calculate quality score (0-100)"""
        score = 0.0
        
        # Liveliness: 40 points
        if proxy.is_alive:
            score += 40
        
        # Latency: 20 points (lower is better)
        if proxy.latency_ms:
            if proxy.latency_ms < 100:
                score += 20
            elif proxy.latency_ms < 500:
                score += 15
            elif proxy.latency_ms < 1000:
                score += 10
            else:
                score += 5
        
        # Anonymity: 20 points
        if proxy.anonymity_level:
            if proxy.anonymity_level == "elite":
                score += 20
            elif proxy.anonymity_level == "anonymous":
                score += 15
            else:
                score += 5
        
        # Geolocation: 10 points
        if proxy.country_code:
            score += 10
        
        # Protocol: 10 points
        if proxy.protocol:
            score += 10
        
        proxy.quality_score = min(100, score)
        return proxy.quality_score
    
    async def validate_batch(self, proxies: List[ProxyModel]) -> List[ProxyModel]:
        """Run complete 5-dimensional validation"""
        await logger.ainfo("Starting master validation", total_proxies=len(proxies))
        
        # Step 1: TCP Liveliness
        await logger.ainfo("Step 1: TCP Liveliness check")
        proxies = await self.liveliness_validator.validate_batch(proxies)
        alive_count = sum(1 for p in proxies if p.is_alive)
        await logger.ainfo("Liveliness check complete", alive=alive_count, total=len(proxies))
        
        # Only proceed with alive proxies
        alive_proxies = [p for p in proxies if p.is_alive]
        
        if not alive_proxies:
            await logger.awarning("No alive proxies found")
            return proxies
        
        # Step 2: Protocol Detection
        await logger.ainfo("Step 2: Protocol detection")
        alive_proxies = await self.protocol_detector.validate_batch(alive_proxies)
        
        # Step 3: Anonymity Check
        await logger.ainfo("Step 3: Anonymity check")
        alive_proxies = await self.anonymity_checker.validate_batch(alive_proxies)
        
        # Step 4: Latency Testing
        await logger.ainfo("Step 4: Latency testing")
        alive_proxies = await self.latency_tester.validate_batch(alive_proxies)
        
        # Step 5: Geolocation
        await logger.ainfo("Step 5: Geolocation")
        alive_proxies = await self.geo_locator.validate_batch(alive_proxies)
        
        # Calculate quality scores
        for proxy in alive_proxies:
            self._calculate_quality_score(proxy)
        
        # Filter by minimum quality score
        filtered_proxies = [
            p for p in alive_proxies 
            if p.quality_score >= MIN_QUALITY_SCORE
        ]
        
        await logger.ainfo(
            "Master validation complete",
            total=len(proxies),
            alive=len(alive_proxies),
            passing_quality=len(filtered_proxies)
        )
        
        return filtered_proxies