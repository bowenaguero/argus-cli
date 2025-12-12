import os
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from .core.api_keys import API_KEYS
from .core.config import Config
from .services.database import DatabaseManager
from .services.lookup import GeoIPLookup
from .utils.filters import ResultFilter
from .utils.formatter import ResultFormatter
from .utils.parser import FileParser

console = Console()
app = typer.Typer(
    help="IP lookup and enrichment",
    add_completion=False,
    no_args_is_help=True,
)


class ArgusApp:
    def __init__(self):
        self.config = Config()
        self.console = console
        self.db_manager = DatabaseManager(self.config, self.console)
        self.lookup_service = GeoIPLookup(self.config.db_city, self.config.db_asn)
        self.file_parser = FileParser()
        self.formatter = ResultFormatter(self.console)

    def collect_ips(self, ip: str | None, file: Path | None) -> list[str]:
        ips = []
        if ip:
            ips.append(ip)
        if file:
            try:
                with self.console.status(f"[bold blue]Reading file {file}...", spinner="dots"):
                    content = self.file_parser.read_file_content(str(file))
                    extracted = self.file_parser.extract_ips(content)
                if extracted:
                    ips.extend(extracted)
                    self.console.print(f"[green]✓[/green] Extracted {len(extracted)} unique public IP(s) from file")
                else:
                    self.console.print("[yellow]⚠[/yellow] Warning: No public IPs found in file")
            except FileNotFoundError as e:
                self.console.print(f"[red]✗ Error:[/red] File '[cyan]{file}[/cyan]' not found")
                raise typer.Exit(1) from e
        return ips

    def run(
        self,
        ip: str | None,
        file: Path | None,
        fqdn: bool,
        output: str | None,
        output_format: str,
        exclude_country: list[str] | None,
        exclude_city: list[str] | None,
        exclude_asn: list[int] | None,
        exclude_org: list[str] | None,
    ):
        # Ensure databases are available
        self.db_manager.ensure_databases()

        # Collect IP addresses
        ips = self.collect_ips(ip, file)
        if not ips:
            return None

        # Perform lookups
        try:
            results = self.lookup_service.lookup_ips(ips, fqdn)
        except Exception as e:
            self.console.print(f"[red]✗ Error:[/red] {e}", style="bold")
            raise typer.Exit(1) from e

        # Apply filters
        result_filter = ResultFilter(
            exclude_countries=exclude_country,
            exclude_cities=exclude_city,
            exclude_asns=exclude_asn,
            exclude_orgs=exclude_org,
        )
        filtered_results = result_filter.filter_results(results)

        # Show filter stats
        if len(filtered_results) < len(results):
            self.console.print(f"[yellow][i][/i][/yellow] Filtered out {len(results) - len(filtered_results)} IP(s)")

        # Always display table to console
        self.console.print(self.formatter.format_table(filtered_results))

        # Write to file if output is specified
        if output is not None:
            self.formatter.write_to_file(filtered_results, output, output_format)

        return filtered_results


@app.command(help="Initial setup for Argus CLI (run this first)")
def setup():
    import json

    config_obj = Config()

    console.print("[bold cyan]Argus Setup[/bold cyan]")
    console.print("─" * 60)

    config_obj.data_dir.mkdir(parents=True, exist_ok=True)

    config_data = {}
    if os.path.exists(config_obj.config_file):
        with open(config_obj.config_file) as f:
            config_data = json.load(f)

    for api_config in API_KEYS:
        console.print(f"\n{api_config['info']}")
        console.print(f"  [link={api_config['link']}]{api_config['link']}[/link]\n")

        key_value = typer.prompt(api_config["prompt"])

        if not key_value or not key_value.strip():
            console.print(f"[red]✗ Error:[/red] {api_config['name']} key cannot be empty")
            raise typer.Exit(1)

        config_data[api_config["key"]] = key_value.strip()

    with open(config_obj.config_file, "w") as f:
        json.dump(config_data, f, indent=2)

    console.print(f"\n[green]✓[/green] Configuration saved to: [cyan]{config_obj.config_file}[/cyan]")
    console.print("\nYou can now run: [cyan]argus lookup <IP>[/cyan]")


@app.command(help="Lookup an IP address")
def lookup(
    ip: Annotated[str | None, typer.Argument(help="IP address to lookup")] = None,
    file: Annotated[Path | None, typer.Option("-f", "--file", help="Extract IPs from file")] = None,
    fqdn: Annotated[bool, typer.Option(help="Show full hostname (FQDN) instead of apex domain")] = False,
    output_format: Annotated[str, typer.Option("-fmt", "--format", help="Output file format (json or csv)")] = "json",
    exclude_country: Annotated[
        list[str] | None,
        typer.Option("-xc", "--exclude-country", help="Exclude IPs from country (ISO code, e.g., US, CN)"),
    ] = None,
    exclude_city: Annotated[
        list[str] | None, typer.Option("-xct", "--exclude-city", help="Exclude IPs from city (case-insensitive)")
    ] = None,
    exclude_asn: Annotated[
        list[int] | None, typer.Option("-xa", "--exclude-asn", help="Exclude IPs from ASN (e.g., 15169)")
    ] = None,
    exclude_org: Annotated[
        list[str] | None,
        typer.Option("-xo", "--exclude-org", help="Exclude IPs from organizations containing text (case-insensitive)"),
    ] = None,
    output: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output",
            help="Write results to file. Use '-o -' for auto-naming (argus_results_TIMESTAMP.json)",
        ),
    ] = None,
):
    # Check if no input provided
    if not ip and not file:
        console.print("[yellow]No IP or file provided. Use --help for usage information.[/yellow]")
        raise typer.Exit(0)

    # Handle special case for -o flag without value (auto-naming)
    if output == "-":
        output = ""

    # Validate format
    if output_format not in ["json", "csv"]:
        console.print(f"[red]✗ Error:[/red] Invalid format '{output_format}'. Must be 'json' or 'csv'.")
        raise typer.Exit(1)

    argus_app = ArgusApp()
    argus_app.run(ip, file, fqdn, output, output_format, exclude_country, exclude_city, exclude_asn, exclude_org)


if __name__ == "__main__":
    app()
