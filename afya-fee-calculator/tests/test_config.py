"""Tests for config loading and validation."""

import json
import os
import tempfile

import pytest

from app.config_loader import ConfigValidationError, FeeConfigLoader


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the config loader singleton before each test."""
    FeeConfigLoader.reset()
    yield
    FeeConfigLoader.reset()


def _config_path() -> str:
    """Get the path to the default config file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "fee_rules.json",
    )


class TestConfigLoading:
    """Tests for loading the fee rules configuration."""

    def test_load_default_config(self):
        """Test loading the default fee_rules.json."""
        loader = FeeConfigLoader()
        config = loader.load(_config_path())
        assert "countries" in config
        assert "fx_rates" in config

    def test_singleton_pattern(self):
        """Test that FeeConfigLoader is a singleton."""
        loader1 = FeeConfigLoader()
        loader2 = FeeConfigLoader()
        assert loader1 is loader2

    def test_load_nonexistent_file(self):
        """Test error on missing config file."""
        loader = FeeConfigLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/path/fee_rules.json")

    def test_get_available_countries(self):
        """Test retrieving available country codes."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        countries = loader.get_available_countries()
        assert set(countries) == {"KE", "NG", "GH", "ZA"}

    def test_get_country_valid(self):
        """Test retrieving a valid country config."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        country = loader.get_country("KE")
        assert country["currency"] == "KES"
        assert country["settlement_currency"] == "USD"

    def test_get_country_invalid(self):
        """Test error on unsupported country."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        with pytest.raises(KeyError, match="Unsupported country"):
            loader.get_country("XX")

    def test_get_payment_method_valid(self):
        """Test retrieving a valid payment method."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        method = loader.get_payment_method("KE", "mobile_money")
        assert method["fee_bearer"] == "merchant"
        assert method["processor_fee"]["type"] == "percentage_plus_fixed"

    def test_get_payment_method_invalid(self):
        """Test error on unsupported payment method."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        with pytest.raises(KeyError, match="Unsupported payment method"):
            loader.get_payment_method("KE", "crypto")

    def test_get_fx_rate_valid(self):
        """Test retrieving a valid FX rate."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        fx = loader.get_fx_rate("KES", "USD")
        assert fx["mid_market_rate"] == 0.0065
        assert fx["spread_percent"] == 2.0

    def test_get_fx_rate_invalid(self):
        """Test error on missing FX pair."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        with pytest.raises(KeyError, match="No FX rate"):
            loader.get_fx_rate("EUR", "USD")

    def test_country_case_insensitive(self):
        """Test that country codes are case-insensitive."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        country = loader.get_country("ke")
        assert country["currency"] == "KES"

    def test_payment_methods_for_country(self):
        """Test listing payment methods for a country."""
        loader = FeeConfigLoader()
        loader.load(_config_path())
        methods = loader.get_payment_methods_for_country("KE")
        assert set(methods) == {"mobile_money", "card", "bank_transfer"}


class TestConfigValidation:
    """Tests for config structure validation."""

    def _write_temp_config(self, config: dict) -> str:
        """Write a config dict to a temp file and return the path."""
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(config, f)
        return path

    def test_missing_countries_key(self):
        """Test validation fails if 'countries' key is missing."""
        path = self._write_temp_config({"fx_rates": {}})
        loader = FeeConfigLoader()
        with pytest.raises(ConfigValidationError, match="missing 'countries'"):
            loader.load(path)
        os.unlink(path)

    def test_missing_fx_rates_key(self):
        """Test validation fails if 'fx_rates' key is missing."""
        path = self._write_temp_config({"countries": {}})
        loader = FeeConfigLoader()
        with pytest.raises(ConfigValidationError, match="missing 'fx_rates'"):
            loader.load(path)
        os.unlink(path)

    def test_missing_country_currency(self):
        """Test validation fails if country is missing currency."""
        config = {
            "countries": {
                "KE": {
                    "settlement_currency": "USD",
                    "tax": {"rate_percent": 16, "applies_to": []},
                    "payment_methods": {},
                }
            },
            "fx_rates": {},
        }
        path = self._write_temp_config(config)
        loader = FeeConfigLoader()
        with pytest.raises(ConfigValidationError, match="missing 'currency'"):
            loader.load(path)
        os.unlink(path)

    def test_unknown_fee_type(self):
        """Test validation fails for unknown fee type."""
        config = {
            "countries": {
                "KE": {
                    "currency": "KES",
                    "settlement_currency": "USD",
                    "tax": {"rate_percent": 16, "applies_to": []},
                    "payment_methods": {
                        "card": {
                            "fee_bearer": "merchant",
                            "processor_fee": {"type": "unknown_type"},
                            "payment_method_fee": {"type": "none"},
                        }
                    },
                }
            },
            "fx_rates": {},
        }
        path = self._write_temp_config(config)
        loader = FeeConfigLoader()
        with pytest.raises(ConfigValidationError, match="unknown type"):
            loader.load(path)
        os.unlink(path)

    def test_valid_minimal_config(self):
        """Test that a minimal but valid config passes validation."""
        config = {
            "countries": {
                "KE": {
                    "currency": "KES",
                    "settlement_currency": "KES",
                    "tax": {"rate_percent": 0, "applies_to": []},
                    "payment_methods": {
                        "card": {
                            "fee_bearer": "merchant",
                            "processor_fee": {"type": "fixed", "fixed": 10},
                            "payment_method_fee": {"type": "none"},
                        }
                    },
                }
            },
            "fx_rates": {},
        }
        path = self._write_temp_config(config)
        loader = FeeConfigLoader()
        loaded = loader.load(path)
        assert "KE" in loaded["countries"]
        os.unlink(path)
