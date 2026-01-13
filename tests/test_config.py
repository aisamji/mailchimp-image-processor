import sys
from pathlib import Path

import pytest

from mailchimp_image_processor import config


class TestDetectEnvironment:
    """Tests for detect_environment function"""

    def test_detect_venv_environment(self, monkeypatch: pytest.MonkeyPatch):
        """Should set environment to VENV when sys._MEIPASS is not present"""
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)

        config.detect_environment()
        assert config.environment == config.Environment.VENV

    def test_detect_pyinstaller_environment(self, monkeypatch: pytest.MonkeyPatch):
        """Should set environment to PYINSTALLER when sys._MEIPASS is present"""
        monkeypatch.setattr(sys, "_MEIPASS", "/fake/path", raising=False)

        config.detect_environment()
        assert config.environment == config.Environment.PYINSTALLER


class TestGetCredentialsPath:
    """Tests for get_credentials_path function"""

    def test_venv_credentials_path(self, monkeypatch: pytest.MonkeyPatch):
        """Should return project_root/credentials.json for VENV environment"""
        monkeypatch.setattr(config, "environment", config.Environment.VENV)

        result = config.get_credentials_path()

        expected_root = Path(config.__file__).parent.parent.parent
        expected_path = expected_root / "credentials.json"
        assert result == expected_path

    def test_pyinstaller_credentials_path(self, monkeypatch: pytest.MonkeyPatch):
        """Should return sys._MEIPASS/credentials.json for PYINSTALLER environment"""
        fake_meipass = "/fake/pyinstaller/path"
        monkeypatch.setattr(sys, "_MEIPASS", fake_meipass, raising=False)
        monkeypatch.setattr(config, "environment", config.Environment.PYINSTALLER)

        result = config.get_credentials_path()

        expected_path = Path(fake_meipass) / "credentials.json"
        assert result == expected_path

    def test_pyinstaller_without_meipass_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """Should raise RuntimeError if PYINSTALLER mode but sys._MEIPASS doesn't exist"""
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)
        monkeypatch.setattr(config, "environment", config.Environment.PYINSTALLER)

        with pytest.raises(RuntimeError, match="sys._MEIPASS not found"):
            config.get_credentials_path()

    def test_raises_error_when_environment_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """Should raise RuntimeError when config.environment is None"""
        monkeypatch.setattr(config, "environment", None)

        with pytest.raises(RuntimeError, match="config.environment is not set"):
            config.get_credentials_path()
