import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from platformdirs import user_data_dir

from argus_cli.core.config import Config


class TestConfig:
    def test_get_license_key_file_not_exists(self):
        config = Config()
        with patch.object(config, "config_file", "/nonexistent/keys.json"):
            assert config.get_license_key("maxmind_license_key") is None

    def test_get_license_key_valid_json(self):
        config = Config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"maxmind_license_key": "test_key_123"}, f)
            temp_path = f.name

        try:
            with patch.object(config, "config_file", temp_path):
                assert config.get_license_key("maxmind_license_key") == "test_key_123"
        finally:
            os.unlink(temp_path)

    def test_get_license_key_missing_key(self):
        config = Config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"other_key": "value"}, f)
            temp_path = f.name

        try:
            with patch.object(config, "config_file", temp_path):
                assert config.get_license_key("maxmind_license_key") is None
        finally:
            os.unlink(temp_path)

    def test_get_license_key_invalid_json(self):
        config = Config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json{")
            temp_path = f.name

        try:
            with patch.object(config, "config_file", temp_path):
                assert config.get_license_key("maxmind_license_key") is None
        finally:
            os.unlink(temp_path)

    def test_get_license_key_empty_file(self):
        config = Config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            with patch.object(config, "config_file", temp_path):
                assert config.get_license_key("maxmind_license_key") is None
        finally:
            os.unlink(temp_path)

    def test_get_data_dir(self):
        config = Config()
        assert Path(user_data_dir("argus", appauthor=False)) == config.data_dir
