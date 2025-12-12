import socket

import geoip2.database
import geoip2.errors
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn


class GeoIPLookup:
    def __init__(self, city_db_path: str, asn_db_path: str):
        self.city_db_path = city_db_path
        self.asn_db_path = asn_db_path

    @staticmethod
    def get_apex_domain(hostname: str | None) -> str | None:
        if not hostname:
            return None
        parts = hostname.rstrip(".").split(".")
        if len(parts) < 2:
            return hostname
        # Handle common two-part TLDs (co.uk, com.au, etc.)
        if len(parts) >= 3 and parts[-2] in ["co", "com", "net", "org", "gov", "ac", "edu"]:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])

    @classmethod
    def get_reverse_dns(cls, ip: str, use_fqdn: bool = False) -> str | None:
        """Get reverse DNS with timeout protection."""
        import threading

        result = [None]  # Mutable container for thread result

        def dns_lookup():
            try:
                hostname, _, _ = socket.gethostbyaddr(ip)
                result[0] = hostname if use_fqdn else cls.get_apex_domain(hostname)
            except (socket.herror, socket.gaierror, socket.timeout, OSError):
                result[0] = None

        # Run DNS lookup in a thread with timeout
        thread = threading.Thread(target=dns_lookup, daemon=True)
        thread.start()
        thread.join(timeout=1.0)  # Wait max 1 second

        # If thread is still alive, it's hung - return None
        if thread.is_alive():
            return None

        return result[0]

    def lookup_ip(self, city_reader, asn_reader, ip: str, use_fqdn: bool = False, skip_dns: bool = False) -> dict:
        try:
            city_resp = city_reader.city(ip)
            asn_resp = asn_reader.asn(ip)
            domain = None if skip_dns else self.get_reverse_dns(ip, use_fqdn)
        except geoip2.errors.AddressNotFoundError:
            return {"ip": ip, "error": "IP not found in database"}
        except ValueError:
            return {"ip": ip, "error": "Invalid IP format"}
        except Exception as e:
            return {"ip": ip, "error": str(e)}
        else:
            return {
                "ip": ip,
                "domain": domain,
                "city": city_resp.city.name,
                "region": city_resp.subdivisions.most_specific.name,
                "country": city_resp.country.name,
                "iso_code": city_resp.country.iso_code,
                "postal": city_resp.postal.code,
                "asn": asn_resp.autonomous_system_number,
                "asn_org": asn_resp.autonomous_system_organization,
                "error": None,
            }

    def lookup_ips(self, ips: list[str], use_fqdn: bool = False, skip_dns: bool = False) -> list[dict]:
        results = []
        with (
            geoip2.database.Reader(self.city_db_path) as city_reader,
            geoip2.database.Reader(self.asn_db_path) as asn_reader,
            Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Looking up IPs..."),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("[cyan]{task.fields[current_ip]}"),
            ) as progress,
        ):
            task = progress.add_task("lookup", total=len(ips), current_ip="")
            for ip in ips:
                progress.update(task, current_ip=ip)
                result = self.lookup_ip(city_reader, asn_reader, ip, use_fqdn, skip_dns)
                results.append(result)
                progress.advance(task)
        return results
