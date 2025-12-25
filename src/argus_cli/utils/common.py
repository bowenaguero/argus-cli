import json
import os
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)


class FileOperations:
    """Common file operation utilities."""

    @staticmethod
    def safe_read_json(file_path: str) -> dict[str, Any]:
        """Safely read JSON file with error handling."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}") from e  # noqa: TRY003
        except Exception as e:
            raise OSError(f"Error reading {file_path}: {e}") from e  # noqa: TRY003

    @staticmethod
    def safe_write_json(file_path: str, data: dict[str, Any]) -> None:
        """Safely write JSON file with error handling."""
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise OSError(f"Error writing {file_path}: {e}") from e  # noqa: TRY003

    @staticmethod
    def ensure_directory(dir_path: str) -> None:
        """Ensure directory exists."""
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def file_exists_and_readable(file_path: str) -> bool:
        """Check if file exists and is readable."""
        return os.path.exists(file_path) and os.access(file_path, os.R_OK)


class ProgressFactory:
    """Factory for creating consistent progress bars."""

    @staticmethod
    def create_download_progress(console: Console, description: str):
        """Create a download progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        )

    @staticmethod
    def create_processing_progress(console: Console, description: str):
        """Create a processing progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.fields[current_item]}"),
            transient=True,
            console=console,
        )


class ValidationHelper:
    """Common validation utilities."""

    @staticmethod
    def validate_required(value: Any, field_name: str) -> Any:
        """Validate that a value is not empty or None."""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"{field_name} is required")  # noqa: TRY003
        return value

    @staticmethod
    def validate_choice(value: str, choices: list[str], field_name: str) -> str:
        """Validate that value is in allowed choices."""
        if value not in choices:
            raise ValueError(f"{field_name} must be one of: {', '.join(choices)}")  # noqa: TRY003
        return value

    @staticmethod
    def validate_range(value: int, min_val: int, max_val: int, field_name: str) -> int:
        """Validate that value is within range."""
        if not (min_val <= value <= max_val):
            raise ValueError(f"{field_name} must be between {min_val} and {max_val}")  # noqa: TRY003
        return value


class ConfigHelper:
    """Configuration management utilities."""

    @staticmethod
    def merge_configs(base_config: dict[str, Any], override_config: dict[str, Any]) -> dict[str, Any]:
        """Merge two configuration dictionaries."""
        merged = base_config.copy()
        merged.update(override_config)
        return merged

    @staticmethod
    def get_nested_value(config: dict[str, Any], key_path: str, default: Any = None) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = key_path.split(".")
        value = config

        try:
            for key in keys:
                value = value[key]
        except (KeyError, TypeError):
            return default
        else:
            return value
