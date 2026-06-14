"""
README - Project documentation
"""

# Ultimate Proxy Collector - Production-Grade Proxy Collection System

## Overview

Ultimate Proxy Collector is a high-performance, production-ready proxy collection, validation, and export system. It features:

- **Multi-Source Collection**: HTML tables, JSON APIs, GitHub raw files, regex patterns
- **5-Dimensional Validation**: TCP liveliness, protocol detection, anonymity, latency, geolocation
- **Multi-Layer Deduplication**: Early aggregator, Bloom filters, Redis persistence
- **Advanced Scoring**: Quality metrics (0-100) based on multiple factors
- **Multiple Export Formats**: Plain text, JSON, CSV, grouped by country/protocol/anonymity
- **Async/Concurrent**: 5000+ concurrent tasks with token bucket rate limiting
- **Anti-Bot Protection**: User-Agent rotation, proxy rotation, rate limiting

## Architecture

```
Collection Phase → Deduplication → Validation → Export Phase
     ↓                ↓               ↓            ↓
  Scrapers      Set + Bloom    5D Validators   Multi-Format
  (4 types)     + Redis        (Scoring)       (4 formats)
```

## Installation

```bash
# Clone repository
git clone https://github.com/exes-astride/fullaccs.git
cd fullaccs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install optional dependencies
pip install beautifulsoup4  # For HTML scraping
pip install dnspython       # For spam blacklist checks
pip install redis           # For Redis state persistence
```

## Quick Start

### 1. Create Configuration File

```bash
cp config.example.yaml config.yaml
# Edit config.yaml to add your proxy sources
```

### 2. Run Collector

```bash
python -m src.main
```

### 3. Check Output

```bash
ls outputs/
# proxies.txt - Plain text format
# proxies.json - JSON with metadata
# proxies.csv - CSV spreadsheet
# by_country/ - Grouped by country
# by_protocol/ - Grouped by protocol
# by_anonymity/ - Grouped by anonymity level
```

## Configuration

Edit `config.yaml` to customize:

- **Proxy Sources**: Add/remove/enable sources
- **Validators**: Enable/disable validation steps
- **Deduplication**: Set Bloom filter size, Redis settings
- **Export**: Choose output formats
- **Performance**: Adjust concurrency limits

### Example Source Configuration

```yaml
sources:
  - name: "free-proxy-list"
    url: "https://www.freeproxylists.net/"
    type: "html_table"
    enabled: true
    extraction_config:
      table_selector: "table.table"
      ip_column: 0
      port_column: 1
      protocol_column: 2
```

## Usage Examples

### Python API

```python
import asyncio
from src.collectors.factory import ScraperFactory
from src.deduplication.master_deduplicator import MasterDeduplicator
from src.validators.master_validator import MasterValidator

async def collect_proxies():
    # Create scraper
    scraper = ScraperFactory.create_scraper(
        source_type='github_raw',
        name='my_source',
        url='https://example.com/proxies.txt',
        extraction_config={'pattern': r'(\d+\.\d+\.\d+\.\d+):(\d+)'}
    )
    
    # Collect
    batch = await scraper.collect()
    
    # Deduplicate
    dedup = MasterDeduplicator()
    unique = await dedup.deduplicate(batch.proxies)
    
    # Validate
    validator = MasterValidator()
    validated = await validator.validate_batch(unique)
    
    return validated

asyncio.run(collect_proxies())
```

## Performance

- **Collection**: ~1000 proxies/second from single source
- **Validation**: ~100 concurrent TCP checks
- **Deduplication**: O(1) with Bloom filters
- **Memory**: <100MB for 1M proxies (Bloom filter)

## Quality Scoring

Proxies are scored 0-100 based on:

- **Liveliness** (40%): Is proxy alive?
- **Latency** (20%): Response time <100ms = 100, >1000ms = 20
- **Anonymity** (20%): Elite = 100, Anonymous = 75, Transparent = 25
- **Geolocation** (10%): Has valid country code
- **Protocol** (10%): Detected protocol type

## Validators

1. **TCP Liveliness**: Direct socket connection
2. **Protocol Detection**: HTTP/HTTPS/SOCKS4/SOCKS5
3. **Anonymity Check**: Via header analysis
4. **Latency Tester**: RTT measurement
5. **Geo Locator**: MaxMind geolocation

## Deduplication Layers

1. **Early Aggregator**: Fast Set-based dedup
2. **Bloom Filter**: Memory-efficient (100M capacity)
3. **Redis State**: Cross-run persistence

## Export Formats

### Plain Text
```
192.168.1.1:8080
192.168.1.2:8081
```

### JSON
```json
{
  "proxies": [
    {"ip": "192.168.1.1", "port": 8080, "quality_score": 85}
  ],
  "stats": {...}
}
```

### CSV
```csv
ip,port,protocol,latency_ms,quality_score,country_code
192.168.1.1,8080,http,45.2,85,US
```

### Grouped
- `by_country/US.txt`
- `by_protocol/http.txt`
- `by_anonymity/elite.txt`

## Troubleshooting

### No proxies collected
- Check source URLs are accessible
- Verify extraction config matches HTML/JSON structure
- Check logs for parsing errors

### Low quality scores
- Reduce min_quality_score threshold
- Disable non-critical validators
- Check network connectivity

### Memory usage high
- Reduce max_concurrent_tasks
- Disable Bloom filter
- Export and clear older batches

## License

MIT License

## Support

For issues, create a GitHub issue with:
- Config file (sanitized)
- Error logs
- Expected vs actual behavior
