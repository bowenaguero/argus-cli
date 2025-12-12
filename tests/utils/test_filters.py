from argus_cli.utils.filters import ResultFilter


class TestResultFilter:
    def test_filter_by_country(self):
        result_filter = ResultFilter(exclude_countries=["US", "CN"])
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "Austin", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "8.8.8.8", "country": "CA", "city": "Toronto", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "9.9.9.9", "country": "CN", "city": "Beijing", "asn": 13335, "asn_org": "Cloudflare", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 1
        assert filtered[0]["country"] == "CA"

    def test_filter_by_city(self):
        result_filter = ResultFilter(exclude_cities=["austin", "beijing"])
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "Austin", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "8.8.8.8", "country": "CA", "city": "Toronto", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "9.9.9.9", "country": "CN", "city": "Beijing", "asn": 13335, "asn_org": "Cloudflare", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 1
        assert filtered[0]["city"] == "Toronto"

    def test_filter_by_asn(self):
        result_filter = ResultFilter(exclude_asns=[15169])
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "Austin", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "8.8.8.8", "country": "CA", "city": "Toronto", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "9.9.9.9", "country": "CN", "city": "Beijing", "asn": 13335, "asn_org": "Cloudflare", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 1
        assert filtered[0]["asn"] == 13335

    def test_filter_by_org(self):
        result_filter = ResultFilter(exclude_orgs=["google"])
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "Austin", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "8.8.8.8", "country": "CA", "city": "Toronto", "asn": 15169, "asn_org": "GOOGLE", "error": None},
            {"ip": "9.9.9.9", "country": "CN", "city": "Beijing", "asn": 13335, "asn_org": "Cloudflare", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 1
        assert filtered[0]["asn_org"] == "Cloudflare"

    def test_filter_multiple_criteria(self):
        result_filter = ResultFilter(exclude_countries=["US"], exclude_asns=[13335])
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "Austin", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "8.8.8.8", "country": "CA", "city": "Toronto", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "9.9.9.9", "country": "CN", "city": "Beijing", "asn": 13335, "asn_org": "Cloudflare", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 1
        assert filtered[0]["country"] == "CA"

    def test_no_filters(self):
        result_filter = ResultFilter()
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "Austin", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "8.8.8.8", "country": "CA", "city": "Toronto", "asn": 15169, "asn_org": "Google", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 2

    def test_filter_all_results(self):
        result_filter = ResultFilter(exclude_countries=["US"])
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "Austin", "asn": 15169, "asn_org": "Google", "error": None},
            {"ip": "8.8.8.8", "country": "US", "city": "New York", "asn": 15169, "asn_org": "Google", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 0

    def test_case_insensitive_city(self):
        result_filter = ResultFilter(exclude_cities=["AUSTIN"])
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "austin", "asn": 15169, "asn_org": "Google", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 0

    def test_case_insensitive_org_partial_match(self):
        result_filter = ResultFilter(exclude_orgs=["goog"])
        results = [
            {"ip": "1.1.1.1", "country": "US", "city": "Austin", "asn": 15169, "asn_org": "Google LLC", "error": None},
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 0

    def test_unknown_values(self):
        result_filter = ResultFilter(exclude_countries=["US"], exclude_cities=["Austin"])
        results = [
            {
                "ip": "1.1.1.1",
                "country": "Unknown",
                "city": "Unknown",
                "asn": None,
                "asn_org": "Unknown",
                "error": None,
            },
        ]
        filtered = result_filter.filter_results(results)
        assert len(filtered) == 1
