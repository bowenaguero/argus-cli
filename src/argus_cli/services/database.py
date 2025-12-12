import json
import os
import shutil
import sys
import tarfile
from datetime import datetime, timedelta

import requests
from rich.console import Console
from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn, TransferSpeedColumn


class DatabaseManager:
    def __init__(self, config, console: Console):
        self.config = config
        self.console = console

    def load_state(self) -> dict:
        if not os.path.exists(self.config.state_file):
            return {}
        try:
            with open(self.config.state_file) as f:
                return json.load(f)
        except Exception:
            return {}

    def save_state(self, state: dict) -> None:
        try:
            with open(self.config.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:  # noqa: S110
            pass

    def needs_download(self, edition_id: str) -> bool:
        state = self.load_state()
        last_download = state.get(edition_id)
        if not last_download:
            return True
        try:
            last_dt = datetime.fromisoformat(last_download)
            return datetime.now() - last_dt > timedelta(hours=24)
        except Exception:
            return True

    def download_database(self, license_key: str, edition_id: str, db_path: str) -> bool:
        if not self.needs_download(edition_id):
            return True

        url = f"https://download.maxmind.com/app/geoip_download?edition_id={edition_id}&license_key={license_key}&suffix=tar.gz"
        temp_file = str(self.config.data_dir / "temp_geo.tar.gz")

        try:
            self._download_file(url, temp_file, edition_id)
            self._extract_database(temp_file, db_path)
            self._update_state(edition_id)
            self.console.print(f"[green]✓[/green] {edition_id} downloaded successfully")
        except Exception as e:
            self.console.print(f"[red]✗ Error:[/red] {e}", style="bold")
            self.console.print(f"[red]✗ Error:[/red] {e}", style="bold")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(db_path):
                self.console.print("[yellow]Continuing with existing database...[/yellow]")
                return True
            return False

    def _download_file(self, url: str, temp_file: str, edition_id: str) -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(f"Downloading {edition_id}", total=None)

            with requests.get(url, stream=True, timeout=30) as r:
                if r.status_code in [401, 403]:
                    msg = f"{r.status_code} {r.reason}: Invalid or expired license key"
                    raise requests.exceptions.HTTPError(msg)
                r.raise_for_status()

                total_size = int(r.headers.get("content-length", 0))
                progress.update(task, total=total_size)

                with open(temp_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

    def _extract_database(self, temp_file: str, db_path: str) -> None:
        with tarfile.open(temp_file, "r:gz") as tar:
            mmdb_member = next((m for m in tar.getmembers() if m.name.endswith(".mmdb")), None)
            if not mmdb_member:
                msg = "Could not find .mmdb file in archive."
                raise ValueError(msg)

            tar.extract(mmdb_member)
            shutil.move(mmdb_member.name, db_path)

            extracted_dir = os.path.dirname(mmdb_member.name)
            if extracted_dir and os.path.exists(extracted_dir):
                shutil.rmtree(extracted_dir)

        os.remove(temp_file)

    def _update_state(self, edition_id: str) -> None:
        state = self.load_state()
        state[edition_id] = datetime.now().isoformat()
        self.save_state(state)

    def ensure_databases(self) -> None:
        license_key = self.config.get_license_key()
        if not license_key:
            if os.path.exists(self.config.db_city) and os.path.exists(self.config.db_asn):
                return
            self._show_missing_config_error()
            sys.exit(1)

        city_ok = self.download_database(license_key, "GeoLite2-City", self.config.db_city)
        asn_ok = self.download_database(license_key, "GeoLite2-ASN", self.config.db_asn)

        if (not city_ok and not os.path.exists(self.config.db_city)) or (
            not asn_ok and not os.path.exists(self.config.db_asn)
        ):
            sys.exit(1)

    def _show_missing_config_error(self) -> None:
        self.console.print("\n[red]✗ Missing license key[/red]")
        self.console.print("─" * 60, style="dim")
        self.console.print("Run setup to configure your MaxMind license key:")
        self.console.print("  [cyan]argus setup[/cyan]")
        self.console.print(
            "\nGet a free key at: [link=https://www.maxmind.com/en/geolite2/signup]https://www.maxmind.com/en/geolite2/signup[/link]"
        )
