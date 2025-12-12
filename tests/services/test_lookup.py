from unittest.mock import Mock, patch

from argus_cli.services.lookup import GeoIPLookup


class TestGetApexDomain:
    def test_basic_domain(self):
        assert GeoIPLookup.get_apex_domain("www.example.com") == "example.com"

    def test_subdomain(self):
        assert GeoIPLookup.get_apex_domain("api.v2.example.com") == "example.com"

    def test_two_part_tld(self):
        assert GeoIPLookup.get_apex_domain("www.example.co.uk") == "example.co.uk"

    def test_already_apex(self):
        assert GeoIPLookup.get_apex_domain("example.com") == "example.com"

    def test_single_part(self):
        assert GeoIPLookup.get_apex_domain("localhost") == "localhost"

    def test_trailing_dot(self):
        assert GeoIPLookup.get_apex_domain("www.example.com.") == "example.com"

    def test_none_input(self):
        assert GeoIPLookup.get_apex_domain(None) is None

    def test_empty_string(self):
        assert GeoIPLookup.get_apex_domain("") is None


class TestGetReverseDNS:
    @patch("argus_cli.services.lookup.socket.gethostbyaddr")
    def test_successful_fqdn_lookup(self, mock_gethostbyaddr):
        mock_gethostbyaddr.return_value = ("dns.google", [], ["8.8.8.8"])
        result = GeoIPLookup.get_reverse_dns("8.8.8.8", use_fqdn=True)
        assert result == "dns.google"

    @patch("argus_cli.services.lookup.socket.gethostbyaddr")
    def test_successful_apex_lookup(self, mock_gethostbyaddr):
        mock_gethostbyaddr.return_value = ("www.example.com", [], ["1.2.3.4"])
        result = GeoIPLookup.get_reverse_dns("1.2.3.4", use_fqdn=False)
        assert result == "example.com"

    @patch("argus_cli.services.lookup.socket.gethostbyaddr")
    def test_lookup_failure(self, mock_gethostbyaddr):
        import socket

        mock_gethostbyaddr.side_effect = socket.herror("Host not found")
        result = GeoIPLookup.get_reverse_dns("1.2.3.4")
        assert result is None


class TestLookupIP:
    def test_successful_lookup(self):
        city_reader = Mock()
        city_response = Mock()
        city_response.city.name = "Mountain View"
        city_response.subdivisions.most_specific.name = "California"
        city_response.country.name = "United States"
        city_response.country.iso_code = "US"
        city_response.postal.code = "94035"
        city_reader.city.return_value = city_response

        asn_reader = Mock()
        asn_response = Mock()
        asn_response.autonomous_system_number = 15169
        asn_response.autonomous_system_organization = "GOOGLE"
        asn_reader.asn.return_value = asn_response

        with patch("argus_cli.services.lookup.GeoIPLookup.get_reverse_dns", return_value="google.com"):
            lookup_service = GeoIPLookup("", "")
            result = lookup_service.lookup_ip(city_reader, asn_reader, "8.8.8.8")

        assert result["ip"] == "8.8.8.8"
        assert result["city"] == "Mountain View"
        assert result["country"] == "United States"
        assert result["iso_code"] == "US"
        assert result["asn"] == 15169
        assert result["asn_org"] == "GOOGLE"
        assert result["domain"] == "google.com"
        assert result["error"] is None

    def test_ip_not_found(self):
        city_reader = Mock()
        asn_reader = Mock()

        import geoip2.errors

        city_reader.city.side_effect = geoip2.errors.AddressNotFoundError("IP not found")

        lookup_service = GeoIPLookup("", "")
        result = lookup_service.lookup_ip(city_reader, asn_reader, "1.2.3.4")

        assert result["ip"] == "1.2.3.4"
        assert result["error"] == "IP not found in database"

    def test_invalid_ip_format(self):
        city_reader = Mock()
        asn_reader = Mock()
        city_reader.city.side_effect = ValueError("Invalid IP")

        lookup_service = GeoIPLookup("", "")
        result = lookup_service.lookup_ip(city_reader, asn_reader, "invalid")

        assert result["ip"] == "invalid"
        assert result["error"] == "Invalid IP format"
