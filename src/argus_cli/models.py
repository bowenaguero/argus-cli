"""Data classes for lookup results."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LookupResult:
    """Represents the result of an IP lookup."""

    ip: str
    domain: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    iso_code: Optional[str] = None
    postal: Optional[str] = None
    asn: Optional[int] = None
    asn_org: Optional[str] = None
    org_managed: bool = False
    org_id: Optional[str] = None
    platform: Optional[str] = None
    proxy_type: Optional[str] = None
    isp: Optional[str] = None
    domain_name: Optional[str] = None
    usage_type: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "ip": self.ip,
            "domain": self.domain,
            "city": self.city,
            "region": self.region,
            "country": self.country,
            "iso_code": self.iso_code,
            "postal": self.postal,
            "asn": self.asn,
            "asn_org": self.asn_org,
            "org_managed": self.org_managed,
            "org_id": self.org_id,
            "platform": self.platform,
            "proxy_type": self.proxy_type,
            "isp": self.isp,
            "domain_name": self.domain_name,
            "usage_type": self.usage_type,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LookupResult":
        """Create from dictionary format."""
        return cls(**data)

    def has_error(self) -> bool:
        """Check if result contains an error."""
        return self.error is not None

    def is_org_managed(self) -> bool:
        """Check if IP is organization-managed."""
        return self.org_managed

    def has_proxy_info(self) -> bool:
        """Check if result has proxy information."""
        return self.proxy_type is not None

    def get_location_display(self) -> str:
        """Get formatted location for display."""
        parts = [p for p in [self.city, self.country] if p]
        return ", ".join(parts) if parts else "-"

    def get_asn_display(self) -> str:
        """Get formatted ASN for display."""
        parts = []
        if self.asn:
            parts.append(f"AS{self.asn}")
        if self.asn_org:
            parts.append(f"({self.asn_org})")
        return " ".join(parts) if parts else "-"


@dataclass
class FilterConfig:
    """Configuration for filtering lookup results."""

    exclude_countries: list[str] = field(default_factory=list)
    exclude_cities: list[str] = field(default_factory=list)
    exclude_asns: list[int] = field(default_factory=list)
    exclude_orgs: list[str] = field(default_factory=list)
    exclude_org_managed: bool = False
    exclude_not_org_managed: bool = False
    exclude_platforms: list[str] = field(default_factory=list)
    exclude_org_ids: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Normalize filter values."""
        self.exclude_countries = [c.upper() for c in self.exclude_countries]
        self.exclude_cities = [c.lower() for c in self.exclude_cities]
        self.exclude_orgs = [o.lower() for o in self.exclude_orgs]
        self.exclude_platforms = [p.lower() for p in self.exclude_platforms]
        self.exclude_org_ids = [o.lower() for o in self.exclude_org_ids]


@dataclass
class ProcessingStats:
    """Statistics for IP processing operations."""

    total_ips: int
    successful_lookups: int
    failed_lookups: int
    filtered_ips: int
    processing_time: float

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_ips == 0:
            return 0.0
        return (self.successful_lookups / self.total_ips) * 100

    @property
    def filter_rate(self) -> float:
        """Calculate filter rate as percentage."""
        if self.successful_lookups == 0:
            return 0.0
        return round((self.filtered_ips / self.successful_lookups) * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "total_ips": self.total_ips,
            "successful_lookups": self.successful_lookups,
            "failed_lookups": self.failed_lookups,
            "filtered_ips": self.filtered_ips,
            "processing_time": self.processing_time,
            "success_rate": round(self.success_rate, 2),
            "filter_rate": round(self.filter_rate, 2),
        }
