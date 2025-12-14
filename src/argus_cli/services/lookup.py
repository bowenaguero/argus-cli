import os

import geoip2.database
import geoip2.errors
import IP2Proxy
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from .cfa_lookup import CFALookup


class GeoIPLookup:
    def __init__(self, city_db_path: str, asn_db_path: str, proxy_db_path: str, cfa_db_dir: str):
        self.city_db_path = city_db_path
        self.asn_db_path = asn_db_path
        self.proxy_db_path = proxy_db_path
        self.cfa_db_dir = cfa_db_dir
        self.has_proxy_db = os.path.exists(proxy_db_path)
        self.cfa_lookup = CFALookup(cfa_db_dir)

    def lookup_ip(self, city_reader, asn_reader, proxy_db, ip: str) -> dict:
        try:
            city_resp = city_reader.city(ip)
            asn_resp = asn_reader.asn(ip)
        except geoip2.errors.AddressNotFoundError:
            return {"ip": ip, "error": "IP not found in database"}
        except ValueError:
            return {"ip": ip, "error": "Invalid IP format"}
        except Exception as e:
            return {"ip": ip, "error": str(e)}

        result = {
            "ip": ip,
            "domain": None,
            "city": city_resp.city.name if city_resp.city.name else None,
            "region": (
                city_resp.subdivisions.most_specific.name if city_resp.subdivisions.most_specific.name else None
            ),
            "country": city_resp.country.name if city_resp.country.name else None,
            "iso_code": (city_resp.country.iso_code if city_resp.country.iso_code else None),
            "postal": city_resp.postal.code if city_resp.postal.code else None,
            "asn": (asn_resp.autonomous_system_number if asn_resp.autonomous_system_number else None),
            "asn_org": (asn_resp.autonomous_system_organization if asn_resp.autonomous_system_organization else None),
            "cfa_managed": False,
            "cfa_id": None,
            "platform": None,
            "error": None,
        }

        if proxy_db and self.has_proxy_db:
            try:
                proxy_record = proxy_db.get_all(ip)
            except Exception:  # noqa: S110
                pass
            else:
                if proxy_record and proxy_record["country_short"] != "-":
                    result["proxy_type"] = proxy_record["proxy_type"] if proxy_record["proxy_type"] != "-" else None
                    result["domain"] = proxy_record["domain"] if proxy_record["domain"] != "-" else None
                    result["isp"] = proxy_record["isp"] if proxy_record["isp"] != "-" else None
                    result["domain_name"] = proxy_record["domain"] if proxy_record["domain"] != "-" else None
                    result["usage_type"] = proxy_record["usage_type"] if proxy_record["usage_type"] != "-" else None

        # Check CFA databases for CFA managed IPs
        if self.cfa_lookup.has_cfa_dbs:
            cfa_result = self.cfa_lookup.lookup_ip(ip)
            if cfa_result:
                result["cfa_managed"] = cfa_result["cfa_managed"]
                result["cfa_id"] = cfa_result["cfa_id"]
                result["platform"] = cfa_result["platform"]

        return result

    def lookup_ips(self, ips: list[str]) -> list[dict]:
        results = []

        show_progress = len(ips) > 1

        # Load CFA databases if available
        if self.cfa_lookup.load_databases():
            self.cfa_lookup.has_cfa_dbs = True

        proxy_db = None
        if self.has_proxy_db:
            proxy_db = IP2Proxy.IP2Proxy()
            proxy_db.open(self.proxy_db_path)

        try:
            with (
                geoip2.database.Reader(self.city_db_path) as city_reader,
                geoip2.database.Reader(self.asn_db_path) as asn_reader,
            ):
                if show_progress:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold blue]Looking up IPs..."),
                        BarColumn(),
                        TaskProgressColumn(),
                        TextColumn("[cyan]{task.fields[current_ip]}"),
                    ) as progress:
                        task = progress.add_task("lookup", total=len(ips), current_ip="")
                        for ip in ips:
                            progress.update(task, current_ip=ip)
                            result = self.lookup_ip(city_reader, asn_reader, proxy_db, ip)
                            results.append(result)
                            progress.advance(task)
                else:
                    for ip in ips:
                        result = self.lookup_ip(city_reader, asn_reader, proxy_db, ip)
                        results.append(result)
        finally:
            if proxy_db:
                proxy_db.close()

        return results
