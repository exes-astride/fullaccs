"""
Custom exception classes for proxy collector system
"""


class ProxyCollectorException(Exception):
    """Base exception for all proxy collector errors"""
    pass


class ValidationException(ProxyCollectorException):
    """Raised when proxy validation fails"""
    pass


class ExtractionException(ProxyCollectorException):
    """Raised when data extraction fails"""
    pass


class SourceException(ProxyCollectorException):
    """Raised when source access fails"""
    pass


class DeduplicationException(ProxyCollectorException):
    """Raised during deduplication process"""
    pass


class ExportException(ProxyCollectorException):
    """Raised during data export"""
    pass


class ConfigurationException(ProxyCollectorException):
    """Raised for configuration errors"""
    pass


class RateLimitException(ProxyCollectorException):
    """Raised when rate limit is exceeded"""
    pass