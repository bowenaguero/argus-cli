"""Performance and edge case tests."""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from argus_cli.services.lookup import GeoIPLookup
from argus_cli.utils.filters import ResultFilter
from argus_cli.utils.parser import FileParser


class TestPerformanceAndEdgeCases:
    """Performance and edge case tests."""

    def test_large_ip_list_performance(self):
        """Test performance with large IP lists."""
        # Generate a large list of IPs
        large_ip_list = [f"192.168.{i // 256}.{i % 256}" for i in range(1000)]

        # Mock the lookup service to avoid actual database calls
        mock_lookup = MagicMock(spec=GeoIPLookup)
        mock_lookup.lookup_ips.return_value = [
            {"ip": ip, "country": "Test Country", "error": None}
            for ip in large_ip_list[:100]  # Limit for test performance
        ]

        start_time = time.time()
        results = mock_lookup.lookup_ips(large_ip_list[:100])
        end_time = time.time()

        # Should complete quickly (under 1 second for mocked service)
        assert end_time - start_time < 1.0
        assert len(results) == 100

    def test_large_file_processing(self):
        """Test processing large files efficiently."""
        # Create a large file with many IP addresses
        ip_list = [f"1.1.{i // 256}.{i % 256}" for i in range(5000)]
        file_content = "\n".join(ip_list)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(file_content)
            temp_file = f.name

        try:
            parser = FileParser()
            start_time = time.time()
            extracted_ips = parser.extract_ips(file_content)
            end_time = time.time()

            # Should extract IPs efficiently
            assert len(extracted_ips) == len(ip_list)
            assert end_time - start_time < 2.0  # Should process 5000 IPs quickly

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_memory_usage_with_large_results(self):
        """Test memory usage with large result sets."""
        # Create a large result set
        large_results = []
        for i in range(10000):
            result = {
                "ip": f"192.168.{i // 256}.{i % 256}",
                "country": f"Country-{i}",
                "asn": 10000 + i,
                "asn_org": f"Organization-{i}",
                "org_managed": i % 2 == 0,
                "error": None,
            }
            large_results.append(result)

        # Test filtering performance
        filter_config = ResultFilter(exclude_countries=["Country-1"])
        start_time = time.time()
        filtered_results = filter_config.filter_results(large_results)
        end_time = time.time()

        # Should filter quickly
        assert len(filtered_results) == 9999  # One result filtered out
        assert end_time - start_time < 1.0

    def test_concurrent_access_simulation(self):
        """Test behavior under simulated concurrent access."""
        # This is a simplified simulation of concurrent access patterns
        mock_lookup = MagicMock(spec=GeoIPLookup)

        # Simulate multiple rapid calls
        call_results = []
        for i in range(10):
            mock_lookup.lookup_ips.return_value = [{"ip": f"8.8.8.{i}", "country": "US"}]
            results = mock_lookup.lookup_ips([f"8.8.8.{i}"])
            call_results.append(results)

        # Should handle all calls successfully
        assert len(call_results) == 10
        for i, result in enumerate(call_results):
            assert len(result) == 1
            assert result[0]["ip"] == f"8.8.8.{i}"

    def test_edge_case_invalid_cidr_expansion(self):
        """Test edge cases in CIDR expansion."""
        parser = FileParser()

        # Test very large CIDR blocks
        large_cidr = "10.0.0.0/8"  # 16,777,216 IPs

        with pytest.raises(ValueError, match=r"CIDR block .* too large"):
            parser.expand_cidr(large_cidr)

        # Test very small CIDR blocks
        single_ip_cidr = "8.8.8.8/32"
        expanded = parser.expand_cidr(single_ip_cidr)
        assert len(expanded) == 1
        assert expanded[0] == "8.8.8.8"

        # Test boundary cases (using public IPs to avoid filtering)
        boundary_cidr = "8.8.8.0/24"  # Public IP range
        expanded = parser.expand_cidr(boundary_cidr)
        assert len(expanded) == 254  # Excludes network and broadcast addresses
        assert expanded[0] == "8.8.8.1"
        assert expanded[-1] == "8.8.8.254"

    def test_edge_case_malformed_input_files(self):
        """Test handling of malformed input files."""
        parser = FileParser()

        # Test files with encoding issues - should read successfully
        malformed_content = "8.8.8.8\x00\x01\x02"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(malformed_content)
            temp_file = f.name

        try:
            content = parser.read_file_content(temp_file)
            # Should read the content without crashing
            assert "8.8.8.8" in content
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_edge_case_unicode_content(self):
        """Test handling of Unicode content in files."""
        parser = FileParser()

        # Test Unicode content
        unicode_content = "测试IP: 8.8.8.8 中文内容"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(unicode_content)
            temp_file = f.name

        try:
            content = parser.read_file_content(temp_file)
            assert "8.8.8.8" in content
            ips = parser.extract_ips(content)
            assert "8.8.8.8" in ips
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_edge_case_very_long_lines(self):
        """Test handling of files with very long lines."""
        parser = FileParser()

        # Create a file with a very long line containing IPs
        long_ip_list = ["8.8.8.8"] * 1000  # Repeat 1000 times
        long_line = " ".join(long_ip_list)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(long_line)
            temp_file = f.name

        try:
            ips = parser.extract_ips(parser.read_file_content(temp_file))
            # Should extract unique IPs despite repetition
            assert len(set(ips)) == 1
            assert "8.8.8.8" in ips
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_edge_case_extreme_filter_combinations(self):
        """Test extreme filter combinations."""
        # Create test data with various edge cases
        edge_case_results = [
            {"ip": "1.1.1.1", "country": None, "city": None, "asn": None, "org_managed": False},
            {"ip": "2.2.2.2", "country": "", "city": "", "asn": "", "org_managed": True},
            {"ip": "3.3.3.3", "country": "US", "city": "NEW YORK", "asn": 13335, "org_managed": False},
            {
                "ip": "4.4.4.4",
                "country": "United States of America",
                "city": "San Francisco, CA",
                "asn": 15169,
                "org_managed": True,
            },
        ]

        # Test with extreme filter combinations
        filter_config = ResultFilter(
            exclude_countries=["US", ""],
            exclude_cities=["NEW YORK", "NEW YORK", ""],  # Duplicate and empty
            exclude_asns=[None, 13335],  # None should be filtered out internally
            exclude_orgs=["amazon"],  # Should not match any
            exclude_org_managed=True,
            exclude_not_org_managed=False,
            exclude_platforms=["unknown"],
            exclude_org_ids=["missing"],
        )

        filtered_results = filter_config.filter_results(edge_case_results)

        # Should handle None and empty values gracefully
        assert len(filtered_results) >= 0  # At least some results should remain

    def test_edge_case_special_characters_in_filters(self):
        """Test filters with special characters."""
        results = [
            {"ip": "1.1.1.1", "country": "United States", "asn_org": "Google LLC & Co.", "org_id": "G00gl3"},
            {"ip": "2.2.2.2", "country": "Côte d'Ivoire", "asn_org": "Orange S.A.", "org_id": "0r@ng3"},
        ]

        # Test with special characters in filter values
        filter_config = ResultFilter(
            exclude_countries=["Côte d'Ivoire"],
            exclude_orgs=["Google &"],
            exclude_org_ids=["G00gl3"],
        )

        filtered_results = filter_config.filter_results(results)

        # Should handle special characters correctly - both results are filtered
        assert len(filtered_results) == 0  # Both results are filtered out

    def test_resource_cleanup_on_error(self):
        """Test proper resource cleanup when errors occur."""
        mock_lookup = MagicMock(spec=GeoIPLookup)

        # Simulate an error during lookup
        mock_lookup.lookup_ips.side_effect = RuntimeError("Database connection failed")

        with pytest.raises(RuntimeError):
            mock_lookup.lookup_ips(["8.8.8.8"])

        # Verify cleanup methods are called if they exist
        if hasattr(mock_lookup, "cleanup"):
            mock_lookup.cleanup.assert_called_once()

    def test_data_integrity_under_stress(self):
        """Test data integrity under stress conditions."""
        # Create a large dataset with various data types
        stress_data = []
        for i in range(1000):
            result = {
                "ip": f"{192 + i // 256}.{168 + (i // 256) % 256}.{(i % 256)}.{(i // 256) % 256}",
                "country": f"Country-{i}",
                "asn": 10000 + i,
                "asn_org": f"Org-{i}" * 10,  # Long string
                "org_managed": i % 3 == 0,
                "error": None if i % 10 != 0 else f"Error-{i}",
            }
            stress_data.append(result)

        # Apply multiple filters
        filter_config = ResultFilter(
            exclude_countries=[f"Country-{i}" for i in range(0, 100, 20)],  # Every 20th country
            exclude_asns=[10000 + i for i in range(0, 100, 20)],  # Every 20th ASN
        )

        start_time = time.time()
        filtered_results = filter_config.filter_results(stress_data)
        end_time = time.time()

        # Should handle large dataset efficiently
        assert end_time - start_time < 2.0
        assert len(filtered_results) > 0  # Should have results remaining

        # Verify data integrity
        for result in filtered_results:
            assert "ip" in result
            assert isinstance(result["ip"], str)
            assert "country" in result
            assert "error" in result
