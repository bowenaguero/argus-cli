import json
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table


class ResultFormatter:
    def __init__(self, console: Console):
        self.console = console

    def format_json(self, results: list[dict]) -> str:
        return json.dumps(results, indent=2)

    def format_table(self, results: list[dict]) -> Table:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("IP Address", style="cyan", no_wrap=True)
        table.add_column("Org Managed", style="bright_green")
        table.add_column("Org ID", style="bright_cyan")
        table.add_column("Platform", style="bright_magenta")
        table.add_column("Proxy Type", style="red")
        table.add_column("Domain", style="blue")
        table.add_column("City", style="green")
        table.add_column("Country", style="yellow")
        table.add_column("ASN", style="magenta")
        table.add_column("Organization", style="white")
        table.add_column("Usage Type", style="dim")

        for r in results:
            if r["error"]:
                table.add_row(r["ip"], "", "", "", "", f"[red]ERROR: {r['error']}[/red]", "", "", "", "", "")
            else:
                org_managed = "✓" if r.get("org_managed") else "-"
                org_id = r.get("org_id") or "-"
                platform = r.get("platform") or "-"
                proxy_type = r.get("proxy_type") or "-"
                domain = r.get("domain") or "-"
                city = r.get("city") or "-"
                country = r.get("country") or "-"
                asn = f"AS{r['asn']}" if r.get("asn") else "-"
                asn_org = r.get("asn_org") or "-"
                usage_type = r.get("usage_type") or "-"
                table.add_row(
                    r["ip"], org_managed, org_id, platform, proxy_type, domain, city, country, asn, asn_org, usage_type
                )

        return table

    def format_csv(self, results: list[dict]) -> str:
        if not results:
            return ""

        fieldnames = [
            "ip",
            "org_managed",
            "org_id",
            "platform",
            "proxy_type",
            "domain",
            "city",
            "region",
            "country",
            "iso_code",
            "isp",
            "domain_name",
            "usage_type",
            "asn",
            "asn_org",
            "error",
        ]

        output_str = []
        output_str.append(",".join(fieldnames))

        for result in results:
            row = []
            for field in fieldnames:
                value = result.get(field, "")
                if value is None:
                    value = ""
                row.append(str(value))
            output_str.append(",".join(f'"{v}"' for v in row))

        return "\n".join(output_str)

    def write_to_file(self, results: list[dict], output_file: str | None, file_format: str = "json") -> None:
        file_path: str
        if output_file == "":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = "json" if file_format == "json" else "csv"
            file_path = f"argus_results_{timestamp}.{extension}"
        else:
            file_path = output_file if output_file is not None else "argus_results.json"

        try:
            if file_format == "csv":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.format_csv(results))
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)

            self.console.print(f"[green]✓[/green] Results written to [cyan]{file_path}[/cyan]")
        except Exception as e:
            self.console.print(f"[red]✗ Error writing to file:[/red] {e}")
            sys.exit(1)

    def output_results(
        self,
        results: list[dict],
        json_output: bool = False,
        output_file: str | None = None,
    ) -> None:
        if output_file is not None:
            self.write_to_file(results, output_file)
        elif json_output:
            print(self.format_json(results))
        else:
            self.console.print(self.format_table(results))
