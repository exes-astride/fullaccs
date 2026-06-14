"""
Validator 5: GeoLocator - MaxMind offline .mmdb integration for geolocation
"""

import json
from typing import Optional, Tuple
from src.models.proxy import ProxyModel
from src.core.constants import GEOIP_COUNTRY_DB, GEOIP_ASN_DB, GEOLOCATION_CACHE_FILE
import structlog
import os

logger = structlog.get_logger(__name__)

try:
    import maxminddb
    MAXMIND_AVAILABLE = True
except ImportError:
    MAXMIND_AVAILABLE = False


class GeoLocator:
    """Geolocate proxy using MaxMind databases"""
    
    def __init__(self):
        self.country_reader = None
        self.asn_reader = None
        self.cache = {}
        self._load_cache()
        self._initialize_readers()
    
    def _initialize_readers(self):
        """Initialize MaxMind readers if available"""
        if not MAXMIND_AVAILABLE:
            await logger.awarning("MaxMind library not available")
            return
        
        try:
            if os.path.exists(GEOIP_COUNTRY_DB):
                self.country_reader = maxminddb.open_database(GEOIP_COUNTRY_DB)
            
            if os.path.exists(GEOIP_ASN_DB):
                self.asn_reader = maxminddb.open_database(GEOIP_ASN_DB)
        except Exception as e:
            logger.warning(f"Failed to initialize MaxMind readers: {str(e)}")
    
    def _load_cache(self):
        """Load geolocation cache from file"""
        try:
            if os.path.exists(GEOLOCATION_CACHE_FILE):
                with open(GEOLOCATION_CACHE_FILE, 'r') as f:
                    self.cache = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load geolocation cache: {str(e)}")
    
    def _save_cache(self):
        """Save geolocation cache to file"""
        try:
            os.makedirs(os.path.dirname(GEOLOCATION_CACHE_FILE), exist_ok=True)
            with open(GEOLOCATION_CACHE_FILE, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"Failed to save geolocation cache: {str(e)}")
    
    async def geolocate(self, proxy: ProxyModel) -> Tuple[Optional[str], Optional[str]]:
        """Geolocate proxy IP
        
        Returns: (country_code, asn)
        """
        if not proxy.is_alive:
            return None, None
        
        # Check cache first
        if proxy.ip in self.cache:
            cached = self.cache[proxy.ip]
            proxy.country_code = cached.get('country_code')
            proxy.asn = cached.get('asn')
            return proxy.country_code, proxy.asn
        
        try:
            country_code = None
            asn = None
            
            # Get country code
            if self.country_reader:
                try:
                    result = self.country_reader.get(proxy.ip)
                    if result and 'country' in result:
                        country_code = result['country'].get('iso_code')
                except Exception as e:
                    logger.warning(f"Country lookup error for {proxy.ip}: {str(e)}")
            
            # Get ASN
            if self.asn_reader:
                try:
                    result = self.asn_reader.get(proxy.ip)
                    if result and 'autonomous_system_number' in result:
                        asn = f"AS{result['autonomous_system_number']}"
                except Exception as e:
                    logger.warning(f"ASN lookup error for {proxy.ip}: {str(e)}")
            
            # Cache result
            self.cache[proxy.ip] = {
                'country_code': country_code,
                'asn': asn
            }
            
            proxy.country_code = country_code
            proxy.asn = asn
            
            await logger.ainfo(
                "Geolocation determined",
                ip=proxy.ip,
                country=country_code,
                asn=asn
            )
            
            return country_code, asn
        
        except Exception as e:
            await logger.aerror(
                "Geolocation error",
                ip=proxy.ip,
                error=str(e)
            )
            return None, None
    
    async def validate_batch(self, proxies: list[ProxyModel]) -> list[ProxyModel]:
        """Geolocate batch of proxies"""
        import asyncio
        tasks = [self.geolocate(p) for p in proxies]
        await asyncio.gather(*tasks, return_exceptions=True)
        self._save_cache()
        return proxies