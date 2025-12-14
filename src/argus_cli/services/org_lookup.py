import gzip
import pickle
from pathlib import Path


class OrgLookup:
    def __init__(self, org_db_dir: str):
        self.org_db_dir = Path(org_db_dir)
        self.databases = []
        self.has_org_dbs = False

    def load_databases(self) -> bool:
        """Load all org databases from the org/ directory into memory."""
        if not self.org_db_dir.exists():
            return False

        # Find all .bin files in the org directory
        bin_files = list(self.org_db_dir.glob("*.bin"))
        if not bin_files:
            return False

        self.has_org_dbs = True
        loaded_count = 0

        for bin_file in bin_files:
            try:
                data = self._load_single_database(str(bin_file))
                if data:
                    self.databases.append({
                        "name": bin_file.stem,  # e.g., "aws" from "aws.bin"
                        "data": data,
                    })
                    loaded_count += 1
            except Exception:  # noqa: S112
                continue

        return loaded_count > 0

    def _load_single_database(self, db_path: str) -> dict | None:
        """Load a single database file, trying compressed format first."""
        try:
            # Try compressed first
            try:
                with gzip.open(db_path, "rb") as f:
                    return pickle.load(f)  # noqa: S301
            except (OSError, gzip.BadGzipFile):
                # Fall back to uncompressed
                with open(db_path, "rb") as f:
                    return pickle.load(f)  # noqa: S301
        except Exception:
            return None

    def lookup_ip(self, ip: str) -> dict | None:
        """
        Look up an IP across all loaded org databases.
        Returns dict with org_managed, org_id, and platform, or None if not found.
        """
        if not self.databases:
            return None

        # Search through all databases
        for db in self.databases:
            result = self._lookup_in_database(ip, db["data"], db["name"])
            if result:
                return result

        return None

    def _lookup_in_database(self, ip: str, data: dict, db_name: str) -> dict | None:
        """Look up an IP in a specific database."""
        try:
            rows = data["rows"]
            indexes = data["indexes"]

            # Look up IP in the ip column index
            if "ip" not in indexes:
                return None

            ip_index = indexes["ip"]
            if ip not in ip_index:
                return None

            # Get matching row indices
            matching_indices = ip_index[ip]

            # Get the first matching row (should typically be only one)
            if matching_indices:
                # Handle both single index and iterable of indices
                row_idx = matching_indices if isinstance(matching_indices, int) else next(iter(matching_indices))

                row = rows[row_idx]

                # Extract fields from the row
                org_id = row.get("org_id")
                platform = row.get("platform")

                return {
                    "org_managed": True,
                    "org_id": org_id,
                    "platform": platform,
                }

        except (KeyError, IndexError, StopIteration):
            pass

        return None
