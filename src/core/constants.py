"""
Global constants and hardcoded configurations
"""

# HTTP Headers for anti-bot bypass
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Proxy protocol types
PROXY_PROTOCOLS = {
    "HTTP": 80,
    "HTTPS": 443,
    "SOCKS4": 1080,
    "SOCKS5": 1080
}

# Default validation timeouts (in seconds)
DEFAULT_TIMEOUT = 10
SOCKET_TIMEOUT = 5
LATENCY_TEST_TIMEOUT = 8

# Rate limiting defaults
DEFAULT_RATE_LIMIT = 100  # requests per second
TOKEN_BUCKET_CAPACITY = 1000
TOKEN_BUCKET_REFILL_RATE = 100  # tokens per second

# Deduplication settings
BLOOM_FILTER_SIZE = 100000000  # 100M entries
BLOOM_FILTER_HASH_FUNCTIONS = 3

# Concurrency settings
DEFAULT_SEMAPHORE_LIMIT = 100
MAX_CONCURRENT_TASKS = 5000

# Anonymity levels
ANONYMITY_LEVELS = {
    "transparent": 1,
    "anonymous": 2,
    "elite": 3
}

# Quality score thresholds
MIN_QUALITY_SCORE = 50  # Minimum score for export
GOOD_QUALITY_SCORE = 75
EXCELLENT_QUALITY_SCORE = 90

# GeoIP database paths
GEOIP_COUNTRY_DB = "data/geoip/GeoLite2-Country.mmdb"
GEOIP_ASN_DB = "data/geoip/GeoLite2-ASN.mmdb"

# Cache settings
CACHE_TTL = 3600  # 1 hour in seconds
GEOLOCATION_CACHE_FILE = "data/cache/geolocation_cache.json"

# Logging levels
LOG_LEVEL = "INFO"
LOG_FORMAT = "json"

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2

# Output file settings
OUTPUT_DIR = "outputs"
MASTER_FILE = "outputs/proxies.txt"
MANIFEST_FILE = "outputs/metadata/manifest.json"
ATOMIC_WRITE_TEMP_SUFFIX = ".tmp"