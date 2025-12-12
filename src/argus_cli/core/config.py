import json
import os
import sys
from pathlib import Path


class Config:
    def __init__(self):
        self.data_dir = self._get_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_city = str(self.data_dir / "GeoLite2-City.mmdb")
        self.db_asn = str(self.data_dir / "GeoLite2-ASN.mmdb")
        self.state_file = str(self.data_dir / "state.json")
        self.config_file = str(self.data_dir / "keys.json")

    def _get_data_dir(self) -> Path:
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "argus"
        elif sys.platform == "win32":
            return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "argus"
        else:
            return Path.home() / ".local" / "share" / "argus"

    def get_license_key(self) -> str | None:
        if not os.path.exists(self.config_file):
            return None
        try:
            with open(self.config_file) as f:
                config = json.load(f)
                return config.get("maxmind_license_key")
        except Exception:  # noqa: S110
            pass
        return None
