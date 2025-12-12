from argus_cli.utils.parser import FileParser


class TestExtractIPs:
    def test_extract_single_ip(self):
        text = "Server IP is 8.8.8.8"
        result = FileParser.extract_ips(text)
        assert result == ["8.8.8.8"]

    def test_extract_multiple_ips(self):
        text = "IPs: 1.1.1.1, 8.8.8.8, and 9.9.9.9"
        result = FileParser.extract_ips(text)
        assert result == ["1.1.1.1", "8.8.8.8", "9.9.9.9"]

    def test_ignore_private_ips(self):
        text = "Private: 192.168.1.1, Public: 8.8.8.8"
        result = FileParser.extract_ips(text)
        assert result == ["8.8.8.8"]
        assert "192.168.1.1" not in result

    def test_ignore_localhost(self):
        text = "Local: 127.0.0.1, Public: 1.1.1.1"
        result = FileParser.extract_ips(text)
        assert result == ["1.1.1.1"]
        assert "127.0.0.1" not in result

    def test_ignore_invalid_ips(self):
        text = "Invalid: 999.999.999.999, Valid: 8.8.8.8"
        result = FileParser.extract_ips(text)
        assert result == ["8.8.8.8"]

    def test_deduplicate_ips(self):
        text = "IPs: 8.8.8.8, 1.1.1.1, 8.8.8.8"
        result = FileParser.extract_ips(text)
        assert result == ["1.1.1.1", "8.8.8.8"]

    def test_empty_text(self):
        result = FileParser.extract_ips("")
        assert result == []

    def test_no_ips_in_text(self):
        text = "This text has no IP addresses"
        result = FileParser.extract_ips(text)
        assert result == []
