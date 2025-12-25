class ResultFilter:
    def __init__(
        self,
        exclude_countries=None,
        exclude_cities=None,
        exclude_asns=None,
        exclude_orgs=None,
        exclude_org_managed=False,
        exclude_not_org_managed=False,
        exclude_platforms=None,
        exclude_org_ids=None,
    ):
        self.exclude_countries = [c.upper() for c in (exclude_countries or [])]
        self.exclude_cities = [c.lower() for c in (exclude_cities or [])]
        self.exclude_asns = exclude_asns or []
        self.exclude_orgs = [o.lower() for o in (exclude_orgs or [])]
        self.exclude_org_managed = exclude_org_managed
        self.exclude_not_org_managed = exclude_not_org_managed
        self.exclude_platforms = [p.lower() for p in (exclude_platforms or [])]
        self.exclude_org_ids = [o.lower() for o in (exclude_org_ids or [])]

    def should_exclude(self, result: dict) -> bool:
        if result.get("error"):
            return False

        return self._exclude_by_location(result) or self._exclude_by_asn(result) or self._exclude_by_org_status(result)

    def _exclude_by_location(self, result: dict) -> bool | list:
        if self.exclude_countries and result["country"] and result["country"].upper() in self.exclude_countries:
            return True
        return self.exclude_cities and result["city"] and result["city"].lower() in self.exclude_cities

    def _exclude_by_asn(self, result: dict) -> bool:
        if self.exclude_asns and result["asn"] in self.exclude_asns:
            return True

        if self.exclude_orgs and result.get("asn_org"):
            org_lower = result["asn_org"].lower()
            if any(excl in org_lower for excl in self.exclude_orgs):
                return True

        return False

    def _exclude_by_org_status(self, result: dict) -> bool | list | None:
        if self.exclude_org_managed and result.get("org_managed") is True:
            return True

        if self.exclude_not_org_managed and result.get("org_managed") is False:
            return True

        if self.exclude_platforms and result.get("platform") and result["platform"].lower() in self.exclude_platforms:
            return True
        return self.exclude_org_ids and result.get("org_id") and result["org_id"].lower() in self.exclude_org_ids

    def filter_results(self, results: list[dict]) -> list[dict]:
        return [r for r in results if not self.should_exclude(r)]
