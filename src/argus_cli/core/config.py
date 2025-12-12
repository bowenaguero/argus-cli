import json
import os
from pathlib import Path

from platformdirs import user_data_dir


class Config:
    def __init__(self):
        self.data_dir = self._get_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_city = str(self.data_dir / "GeoLite2-City.mmdb")
        self.db_asn = str(self.data_dir / "GeoLite2-ASN.mmdb")
        self.state_file = str(self.data_dir / "state.json")
        self.config_file = str(self.data_dir / "keys.json")

    def _get_data_dir(self) -> Path:
        return Path(user_data_dir("argus", appauthor=False))

    def get_license_key(self, license_key_name) -> str | None:
        if not os.path.exists(self.config_file):
            return None
        try:
            with open(self.config_file) as f:
                config = json.load(f)
                return config.get(license_key_name)
        except Exception:  # noqa: S110
            pass
        return None
