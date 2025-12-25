"""Tests for data models."""

from argus_cli.models import FilterConfig, LookupResult, ProcessingStats


class TestLookupResult:
    """Test cases for LookupResult dataclass."""

    def test_create_valid_lookup_result(self):
        """Test creating a valid LookupResult."""
        result = LookupResult(
            ip="8.8.8.8",
            country="United States",
            asn=15169,
            asn_org="Google LLC",
            org_managed=False,
            error=None,
        )

        assert result.ip == "8.8.8.8"
        assert result.country == "United States"
        assert result.asn == 15169
        assert result.asn_org == "Google LLC"
        assert result.org_managed is False
        assert result.error is None

    def test_create_result_with_error(self):
        """Test creating a LookupResult with error."""
        result = LookupResult(
            ip="192.168.1.1",
            error="Private IP address",
        )

        assert result.ip == "192.168.1.1"
        assert result.error == "Private IP address"
        assert result.has_error() is True
        assert result.is_org_managed() is False
        assert result.has_proxy_info() is False

    def test_to_dict(self):
        """Test converting LookupResult to dictionary."""
        result = LookupResult(
            ip="8.8.8.8",
            domain="dns.google",
            country="United States",
            asn=15169,
            asn_org="Google LLC",
            org_managed=False,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["ip"] == "8.8.8.8"
        assert result_dict["country"] == "United States"
        assert result_dict["asn"] == 15169
        assert result_dict["asn_org"] == "Google LLC"
        assert result_dict["org_managed"] is False

    def test_from_dict(self):
        """Test creating LookupResult from dictionary."""
        data = {
            "ip": "8.8.8.8",
            "country": "United States",
            "asn": 15169,
            "asn_org": "Google LLC",
            "org_managed": True,
            "org_id": "GOOGLE",
            "platform": "gcp",
        }

        result = LookupResult.from_dict(data)

        assert result.ip == "8.8.8.8"
        assert result.country == "United States"
        assert result.asn == 15169
        assert result.asn_org == "Google LLC"
        assert result.org_managed is True
        assert result.org_id == "GOOGLE"
        assert result.platform == "gcp"

    def test_has_error(self):
        """Test error detection."""
        result_with_error = LookupResult(ip="192.168.1.1", error="Private IP")
        result_without_error = LookupResult(ip="8.8.8.8")

        assert result_with_error.has_error() is True
        assert result_without_error.has_error() is False

    def test_is_org_managed(self):
        """Test org managed detection."""
        result_org_managed = LookupResult(ip="1.1.1.1", org_managed=True)
        result_not_org_managed = LookupResult(ip="8.8.8.8", org_managed=False)

        assert result_org_managed.is_org_managed() is True
        assert result_not_org_managed.is_org_managed() is False

    def test_has_proxy_info(self):
        """Test proxy info detection."""
        result_with_proxy = LookupResult(ip="8.8.8.8", proxy_type="DCH")
        result_without_proxy = LookupResult(ip="8.8.8.8")

        assert result_with_proxy.has_proxy_info() is True
        assert result_without_proxy.has_proxy_info() is False

    def test_get_location_display(self):
        """Test location display formatting."""
        result_with_location = LookupResult(ip="8.8.8.8", city="Mountain View", country="United States")
        result_with_city_only = LookupResult(ip="1.1.1.1", city="Unknown")
        result_no_location = LookupResult(ip="192.168.1.1")

        assert result_with_location.get_location_display() == "Mountain View, United States"
        assert result_with_city_only.get_location_display() == "Unknown"
        assert result_no_location.get_location_display() == "-"

    def test_get_asn_display(self):
        """Test ASN display formatting."""
        result_full = LookupResult(ip="8.8.8.8", asn=15169, asn_org="Google LLC")
        result_asn_only = LookupResult(ip="1.1.1.1", asn=13335, asn_org=None)
        result_no_asn = LookupResult(ip="192.168.1.1")

        assert result_full.get_asn_display() == "AS15169 (Google LLC)"
        assert result_asn_only.get_asn_display() == "AS13335"
        assert result_no_asn.get_asn_display() == "-"


class TestFilterConfig:
    """Test cases for FilterConfig dataclass."""

    def test_create_empty_filter(self):
        """Test creating empty filter configuration."""
        filter_config = FilterConfig()

        assert filter_config.exclude_countries == []
        assert filter_config.exclude_cities == []
        assert filter_config.exclude_asns == []
        assert filter_config.exclude_orgs == []
        assert filter_config.exclude_org_managed is False
        assert filter_config.exclude_not_org_managed is False
        assert filter_config.exclude_platforms == []
        assert filter_config.exclude_org_ids == []

    def test_create_filter_with_values(self):
        """Test creating filter configuration with values."""
        filter_config = FilterConfig(
            exclude_countries=["us", "cn"],
            exclude_cities=["Mountain View"],
            exclude_asns=[15169],
            exclude_orgs=["google"],
            exclude_org_managed=True,
            exclude_platforms=["aws"],
        )

        assert filter_config.exclude_countries == ["US", "CN"]  # Normalized to uppercase
        assert filter_config.exclude_cities == ["mountain view"]  # Normalized to lowercase
        assert filter_config.exclude_asns == [15169]
        assert filter_config.exclude_orgs == ["google"]  # Normalized to lowercase
        assert filter_config.exclude_org_managed is True
        assert filter_config.exclude_platforms == ["aws"]  # Normalized to lowercase


class TestProcessingStats:
    """Test cases for ProcessingStats dataclass."""

    def test_create_stats(self):
        """Test creating processing statistics."""
        stats = ProcessingStats(
            total_ips=100,
            successful_lookups=95,
            failed_lookups=5,
            filtered_ips=20,
            processing_time=2.5,
        )

        assert stats.total_ips == 100
        assert stats.successful_lookups == 95
        assert stats.failed_lookups == 5
        assert stats.filtered_ips == 20
        assert stats.processing_time == 2.5

    def test_success_rate(self):
        """Test success rate calculation."""
        stats_perfect = ProcessingStats(
            total_ips=100, successful_lookups=100, failed_lookups=0, filtered_ips=0, processing_time=1.0
        )
        stats_partial = ProcessingStats(
            total_ips=100, successful_lookups=95, failed_lookups=5, filtered_ips=0, processing_time=1.0
        )
        stats_zero = ProcessingStats(
            total_ips=0, successful_lookups=0, failed_lookups=0, filtered_ips=0, processing_time=1.0
        )

        assert stats_perfect.success_rate == 100.0
        assert stats_partial.success_rate == 95.0
        assert stats_zero.success_rate == 0.0

    def test_filter_rate(self):
        """Test filter rate calculation."""
        stats_no_filter = ProcessingStats(
            total_ips=100, successful_lookups=100, failed_lookups=0, filtered_ips=0, processing_time=1.0
        )
        stats_with_filter = ProcessingStats(
            total_ips=100, successful_lookups=95, failed_lookups=5, filtered_ips=20, processing_time=1.0
        )
        stats_zero_success = ProcessingStats(
            total_ips=100, successful_lookups=0, failed_lookups=100, filtered_ips=0, processing_time=1.0
        )

        assert stats_no_filter.filter_rate == 0.0
        assert stats_with_filter.filter_rate == 21.05  # 20/95 * 100
        assert stats_zero_success.filter_rate == 0.0

    def test_to_dict(self):
        """Test converting stats to dictionary."""
        stats = ProcessingStats(
            total_ips=100,
            successful_lookups=95,
            failed_lookups=5,
            filtered_ips=20,
            processing_time=2.5,
        )

        stats_dict = stats.to_dict()

        assert isinstance(stats_dict, dict)
        assert stats_dict["total_ips"] == 100
        assert stats_dict["successful_lookups"] == 95
        assert stats_dict["failed_lookups"] == 5
        assert stats_dict["filtered_ips"] == 20
        assert stats_dict["processing_time"] == 2.5
        assert stats_dict["success_rate"] == 95.0
        assert stats_dict["filter_rate"] == 21.05
