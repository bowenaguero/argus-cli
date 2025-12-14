import os
import time
from pathlib import Path
from typing import Annotated

import click
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
        self.lookup_service = GeoIPLookup(
            self.config.db_city, self.config.db_asn, self.config.db_proxy, self.config.db_cfa_dir
        )
        self.file_parser = FileParser()
        self.formatter = ResultFormatter(self.console)

    def collect_ips(self, ip: str | None, file: Path | None) -> list[str]:
        ips = []
        if ip:
            if "/" in ip:
                try:
                    expanded = self.file_parser.expand_cidr(ip)
                    ips.extend(expanded)
                    self.console.print(f"[green]✓[/green] Expanded CIDR block {ip} into {len(expanded)} IP(s)")
                except ValueError as e:
                    self.console.print(f"[red]✗ Error:[/red] {e}")
                    raise typer.Exit(1) from e
            else:
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
        output: str | None,
        output_format: str,
        exclude_country: list[str] | None,
        exclude_city: list[str] | None,
        exclude_asn: list[int] | None,
        exclude_org: list[str] | None,
        sort_by: str,
    ):
        start_time = time.time()

        self.db_manager.ensure_databases()

        ips = self.collect_ips(ip, file)
        if not ips:
            return None

        try:
            results = self.lookup_service.lookup_ips(ips)
        except Exception as e:
            self.console.print(f"[red]✗ Error:[/red] {e}", style="bold")
            raise typer.Exit(1) from e

        result_filter = ResultFilter(
            exclude_countries=exclude_country,
            exclude_cities=exclude_city,
            exclude_asns=exclude_asn,
            exclude_orgs=exclude_org,
        )
        filtered_results = result_filter.filter_results(results)

        if len(filtered_results) < len(results):
            self.console.print(f"[yellow][i][/i][/yellow] Filtered out {len(results) - len(filtered_results)} IP(s)")

        sorted_results = sorted(
            filtered_results,
            key=lambda x: ((x.get(sort_by) or "") if sort_by != "asn" else (x.get(sort_by) or 0)),
        )

        self.console.print(self.formatter.format_table(sorted_results))

        if output is not None:
            self.formatter.write_to_file(sorted_results, output, output_format)

        elapsed_time = time.time() - start_time
        self.console.print(f"\n[dim]Processed {len(ips)} IP(s) in {elapsed_time:.2f}s[/dim]")

        return sorted_results


@app.command(help="Initial setup for Argus CLI (run this first)")
def setup():
    import json

    config_obj = Config()

    console.print("[bold cyan]Argus Setup[/bold cyan]")
    console.print("─" * 60)

    config_obj.data_dir.mkdir(parents=True, exist_ok=True)

    config_data = {}
    if os.path.exists(config_obj.config_file):
        with open(config_obj.config_file, encoding="utf-8") as f:
            config_data = json.load(f)

    console.print("\n[bold]Current API Keys Status:[/bold]")
    for idx, api_config in enumerate(API_KEYS, 1):
        key_name = api_config["key"]
        status = "[green]✓ Configured[/green]" if config_data.get(key_name) else "[yellow]✗ Not configured[/yellow]"
        console.print(f"  {idx}. {api_config['name']}: {status}")

    console.print(f"\n  {len(API_KEYS) + 1}. Update all keys")
    console.print("  0. Exit\n")

    choice = typer.prompt("Select an option", type=int)

    if choice == 0:
        console.print("[yellow]Setup cancelled[/yellow]")
        raise typer.Exit(0)

    keys_to_update = []
    if choice == len(API_KEYS) + 1:
        keys_to_update = API_KEYS
    elif 1 <= choice <= len(API_KEYS):
        keys_to_update = [API_KEYS[choice - 1]]
    else:
        console.print("[red]✗ Error:[/red] Invalid selection")
        raise typer.Exit(1)

    console.print()
    for api_config in keys_to_update:
        console.print(f"[bold]{api_config['name']}[/bold]")
        console.print(f"{api_config['info']}")
        console.print(f"  [link={api_config['link']}]{api_config['link']}[/link]")

        current_value = config_data.get(api_config["key"])
        if current_value:
            masked = current_value[:4] + "..." + current_value[-4:] if len(current_value) > 8 else "***"
            console.print(f"  Current: [dim]{masked}[/dim]")

        key_value = typer.prompt(f"\n{api_config['prompt']}", default=current_value or "")

        if not key_value or not key_value.strip():
            console.print(f"[red]✗ Error:[/red] {api_config['name']} key cannot be empty")
            raise typer.Exit(1)

        config_data[api_config["key"]] = key_value.strip()
        console.print()

    with open(config_obj.config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    console.print(f"[green]✓[/green] Configuration saved to: [cyan]{config_obj.config_file}[/cyan]")
    console.print("\nYou can now run: [cyan]argus lookup <IP>[/cyan]")


@app.command(help="Lookup an IP address")
def lookup(
    ip: Annotated[str | None, typer.Argument(help="IP address to lookup")] = None,
    file: Annotated[Path | None, typer.Option("-f", "--file", help="Extract IPs from file")] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "-fmt",
            "--format",
            click_type=click.Choice(["json", "csv"]),
            help="Output file format",
        ),
    ] = "json",
    exclude_country: Annotated[
        list[str] | None,
        typer.Option(
            "-xc",
            "--exclude-country",
            help="Exclude IPs from country (ISO code, e.g., US, CN)",
        ),
    ] = None,
    exclude_city: Annotated[
        list[str] | None,
        typer.Option("-xct", "--exclude-city", help="Exclude IPs from city (case-insensitive)"),
    ] = None,
    exclude_asn: Annotated[
        list[int] | None,
        typer.Option("-xa", "--exclude-asn", help="Exclude IPs from ASN (e.g., 15169)"),
    ] = None,
    exclude_org: Annotated[
        list[str] | None,
        typer.Option(
            "-xo",
            "--exclude-org",
            help="Exclude IPs from organizations containing text (case-insensitive)",
        ),
    ] = None,
    sort_by: Annotated[
        str,
        typer.Option(
            "--sort-by",
            click_type=click.Choice(["ip", "domain", "city", "country", "asn", "asn_org"]),
            help="Sort results by field (default: asn_org)",
        ),
    ] = "asn_org",
    output: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output",
            help="Write results to file. Use '-o -' for auto-naming (argus_results_TIMESTAMP.json)",
        ),
    ] = None,
):
    if not ip and not file:
        console.print("[yellow]No IP or file provided. Use --help for usage information.[/yellow]")
        raise typer.Exit(0)

    if output == "-":
        output = ""

    argus_app = ArgusApp()
    argus_app.run(
        ip,
        file,
        output,
        output_format,
        exclude_country,
        exclude_city,
        exclude_asn,
        exclude_org,
        sort_by,
    )


if __name__ == "__main__":
    app()
