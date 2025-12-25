import json
import os

import typer
from rich.console import Console

from ..core.api_keys import API_KEYS
from ..core.config import Config


class SetupCommand:
    def __init__(self, console: Console):
        self.console = console
        self.config = Config()

    def execute(self) -> None:
        self.console.print("[bold cyan]Argus Setup[/bold cyan]")
        self.console.print("─" * 60)

        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        config_data = self._load_existing_config()
        self._show_api_key_status(config_data)

        choice = self._get_user_choice()
        if choice == 0:
            self.console.print("[yellow]Setup cancelled[/yellow]")
            raise typer.Exit(code=0)

        keys_to_update = self._determine_keys_to_update(choice)
        self._update_api_keys(config_data, keys_to_update)
        self._save_config(config_data)

        self.console.print(f"[green]✓[/green] Configuration saved to: [cyan]{self.config.config_file}[/cyan]")
        self.console.print("\nYou can now run: [cyan]argus lookup <IP>[/cyan]")

    def _load_existing_config(self) -> dict:
        config_data = {}
        if os.path.exists(self.config.config_file):
            with open(self.config.config_file, encoding="utf-8") as f:
                config_data = json.load(f)
        return config_data

    def _show_api_key_status(self, config_data: dict) -> None:
        self.console.print("\n[bold]Current API Keys Status:[/bold]")
        for idx, api_config in enumerate(API_KEYS, 1):
            key_name = api_config["key"]
            status = "[green]✓ Configured[/green]" if config_data.get(key_name) else "[yellow]✗ Not configured[/yellow]"
            self.console.print(f"  {idx}. {api_config['name']}: {status}")

        self.console.print(f"\n  {len(API_KEYS) + 1}. Update all keys")
        self.console.print("  0. Exit\n")

    def _get_user_choice(self) -> int:
        choice = typer.prompt("Select an option", type=int)
        return choice

    def _determine_keys_to_update(self, choice: int) -> list[dict]:
        if choice == len(API_KEYS) + 1:
            return API_KEYS
        elif 1 <= choice <= len(API_KEYS):
            return [API_KEYS[choice - 1]]
        else:
            self.console.print("[red]✗ Error:[/red] Invalid selection")
            raise typer.Exit(code=1)

    def _update_api_keys(self, config_data: dict, keys_to_update: list[dict]) -> None:
        self.console.print()
        for api_config in keys_to_update:
            self.console.print(f"[bold]{api_config['name']}[/bold]")
            self.console.print(f"{api_config['info']}")
            self.console.print(f"  [link={api_config['link']}]{api_config['link']}[/link]")

            current_value = config_data.get(api_config["key"])
            if current_value:
                masked = current_value[:4] + "..." + current_value[-4:] if len(current_value) > 8 else "***"
                self.console.print(f"  Current: [dim]{masked}[/dim]")

            key_value = typer.prompt(f"\n{api_config['prompt']}", default=current_value or "")

            if not key_value or not key_value.strip():
                self.console.print(f"[red]✗ Error:[/red] {api_config['name']} key cannot be empty")
                raise typer.Exit(code=1)

            config_data[api_config["key"]] = key_value.strip()
            self.console.print()

    def _save_config(self, config_data: dict) -> None:
        with open(self.config.config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
