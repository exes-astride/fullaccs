"""
Default configuration file generator
"""

DEFAULT_CONFIG = """
app_name: "Ultimate Proxy Collector"
app_version: "1.0.0"

# Maximum concurrent tasks (1-5000)
max_concurrent_tasks: 100
timeout_seconds: 10

# Logging configuration
log_level: "INFO"
log_format: "json"

# Proxy sources
sources:
  # Example HTML table source
  - name: "free_proxy_list"
    url: "https://www.freeproxylists.net/"
    type: "html_table"
    enabled: true
    priority: 5
    extraction_config:
      table_selector: "table.table"
      ip_column: 0
      port_column: 1
      protocol_column: 2
    requests_per_minute: 60
  
  # Example GitHub raw source
  - name: "github_proxies"
    url: "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
    type: "regex_text"
    enabled: true
    priority: 5
    extraction_config:
      pattern: "(\\d{1,3}\\\\.\\d{1,3}\\\\.\\d{1,3}\\\\.\\d{1,3}):(\\d+)"
    requests_per_minute: 60

# Validator configuration
validators:
  enable_liveliness: true
  enable_protocol_detection: true
  enable_anonymity_check: true
  enable_latency_testing: true
  enable_geolocation: true
  min_quality_score: 50

# Deduplication configuration
deduplication:
  use_early_aggregator: true
  use_bloom_filter: true
  use_redis: false
  redis_host: "localhost"
  redis_port: 6379
  redis_db: 0

# Export configuration
export:
  output_dir: "outputs"
  export_formats:
    - txt
    - json
    - csv
    - grouped
  enable_grouped_export: true
"""


def create_default_config(path: str = "config.yaml") -> None:
    """Create default configuration file"""
    with open(path, 'w') as f:
        f.write(DEFAULT_CONFIG)
    
    print(f"Default configuration created at {path}")