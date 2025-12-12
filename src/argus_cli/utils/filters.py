class ResultFilter:
    def __init__(self, exclude_countries=None, exclude_cities=None, exclude_asns=None, exclude_orgs=None):
        self.exclude_countries = [c.upper() for c in (exclude_countries or [])]
        self.exclude_cities = [c.lower() for c in (exclude_cities or [])]
        self.exclude_asns = exclude_asns or []
        self.exclude_orgs = [o.lower() for o in (exclude_orgs or [])]

    def should_exclude(self, result: dict) -> bool:
        if result["error"]:
            return False

        if self.exclude_countries and result["country"] and result["country"].upper() in self.exclude_countries:
            return True

        if self.exclude_cities and result["city"] and result["city"].lower() in self.exclude_cities:
            return True

        if self.exclude_asns and result["asn"] in self.exclude_asns:
            return True

        if self.exclude_orgs and result["asn_org"]:
            org_lower = result["asn_org"].lower()
            if any(excl in org_lower for excl in self.exclude_orgs):
                return True

        return False

    def filter_results(self, results: list[dict]) -> list[dict]:
        return [r for r in results if not self.should_exclude(r)]
