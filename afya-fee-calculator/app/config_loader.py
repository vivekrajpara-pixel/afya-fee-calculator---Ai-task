"""Loads and validates the fee rules JSON configuration. Singleton pattern."""

import json
import os
from typing import Any, Optional


class ConfigValidationError(Exception):
    """Raised when the fee rules configuration is invalid."""
    pass


class FeeConfigLoader:
    """Singleton loader for fee rules configuration."""

    _instance: Optional["FeeConfigLoader"] = None
    _config: Optional[dict[str, Any]] = None
    _config_path: Optional[str] = None

    def __new__(cls) -> "FeeConfigLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None
        cls._config = None
        cls._config_path = None

    def load(self, config_path: Optional[str] = None) -> dict[str, Any]:
        """Load configuration from JSON file."""
        if self._config is not None and config_path == self._config_path:
            return self._config

        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
                "fee_rules.json",
            )

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Fee rules config not found: {config_path}")

        with open(config_path, "r") as f:
            config = json.load(f)

        self._validate(config)
        FeeConfigLoader._config = config
        FeeConfigLoader._config_path = config_path
        return config

    def _validate(self, config: dict[str, Any]) -> None:
        """Validate the structure of the config."""
        if "countries" not in config:
            raise ConfigValidationError("Config missing 'countries' key")
        if "fx_rates" not in config:
            raise ConfigValidationError("Config missing 'fx_rates' key")

        for code, country in config["countries"].items():
            if "currency" not in country:
                raise ConfigValidationError(f"Country {code} missing 'currency'")
            if "settlement_currency" not in country:
                raise ConfigValidationError(f"Country {code} missing 'settlement_currency'")
            if "tax" not in country:
                raise ConfigValidationError(f"Country {code} missing 'tax'")
            if "rate_percent" not in country["tax"]:
                raise ConfigValidationError(f"Country {code} tax missing 'rate_percent'")
            if country["tax"]["rate_percent"] < 0:
                raise ConfigValidationError(f"Country {code} tax rate_percent must be >= 0")
            if "applies_to" not in country["tax"]:
                raise ConfigValidationError(f"Country {code} tax missing 'applies_to'")
            if "payment_methods" not in country:
                raise ConfigValidationError(f"Country {code} missing 'payment_methods'")

            for method_key, method in country["payment_methods"].items():
                if "fee_bearer" not in method:
                    raise ConfigValidationError(
                        f"Country {code}, method {method_key} missing 'fee_bearer'"
                    )
                if "processor_fee" not in method:
                    raise ConfigValidationError(
                        f"Country {code}, method {method_key} missing 'processor_fee'"
                    )
                if "payment_method_fee" not in method:
                    raise ConfigValidationError(
                        f"Country {code}, method {method_key} missing 'payment_method_fee'"
                    )

                for fee_key in ("processor_fee", "payment_method_fee"):
                    fee = method[fee_key]
                    if "type" not in fee:
                        raise ConfigValidationError(
                            f"Country {code}, method {method_key}, {fee_key} missing 'type'"
                        )
                    fee_type = fee["type"]
                    if fee_type not in ("percentage_plus_fixed", "fixed", "tiered", "none"):
                        raise ConfigValidationError(
                            f"Country {code}, method {method_key}, {fee_key}: "
                            f"unknown type '{fee_type}'"
                        )
                    if fee_type == "percentage_plus_fixed":
                        if "percentage" not in fee or "fixed" not in fee:
                            raise ConfigValidationError(
                                f"Country {code}, method {method_key}, {fee_key}: "
                                f"percentage_plus_fixed requires 'percentage' and 'fixed'"
                            )
                        if fee["percentage"] < 0:
                            raise ConfigValidationError(
                                f"Country {code}, method {method_key}, {fee_key}: "
                                f"percentage must be >= 0"
                            )
                        if fee["fixed"] < 0:
                            raise ConfigValidationError(
                                f"Country {code}, method {method_key}, {fee_key}: "
                                f"fixed must be >= 0"
                            )
                    elif fee_type == "fixed":
                        if "fixed" not in fee:
                            raise ConfigValidationError(
                                f"Country {code}, method {method_key}, {fee_key}: "
                                f"fixed type requires 'fixed'"
                            )
                        if fee["fixed"] < 0:
                            raise ConfigValidationError(
                                f"Country {code}, method {method_key}, {fee_key}: "
                                f"fixed must be >= 0"
                            )
                    elif fee_type == "tiered":
                        if "tiers" not in fee or not fee["tiers"]:
                            raise ConfigValidationError(
                                f"Country {code}, method {method_key}, {fee_key}: "
                                f"tiered type requires non-empty 'tiers' list"
                            )
                        for i, tier in enumerate(fee["tiers"]):
                            if "percentage" not in tier or "fixed" not in tier:
                                raise ConfigValidationError(
                                    f"Country {code}, method {method_key}, {fee_key}: "
                                    f"tier {i} must have 'percentage' and 'fixed' keys"
                                )
                            if tier["percentage"] < 0:
                                raise ConfigValidationError(
                                    f"Country {code}, method {method_key}, {fee_key}: "
                                    f"tier {i} percentage must be >= 0"
                                )
                            if tier["fixed"] < 0:
                                raise ConfigValidationError(
                                    f"Country {code}, method {method_key}, {fee_key}: "
                                    f"tier {i} fixed must be >= 0"
                                )

        for pair_key, fx in config["fx_rates"].items():
            if pair_key.startswith("_"):
                continue
            if "mid_market_rate" not in fx:
                raise ConfigValidationError(f"FX pair {pair_key} missing 'mid_market_rate'")
            if fx["mid_market_rate"] <= 0:
                raise ConfigValidationError(f"FX pair {pair_key} mid_market_rate must be > 0")
            if "spread_percent" not in fx:
                raise ConfigValidationError(f"FX pair {pair_key} missing 'spread_percent'")
            if fx["spread_percent"] < 0 or fx["spread_percent"] >= 100:
                raise ConfigValidationError(
                    f"FX pair {pair_key} spread_percent must be >= 0 and < 100"
                )

    def get_config(self) -> dict[str, Any]:
        """Get the loaded configuration. Loads default if not already loaded."""
        if self._config is None:
            return self.load()
        return self._config

    def get_country(self, country_code: str) -> dict[str, Any]:
        """Get configuration for a specific country."""
        config = self.get_config()
        country_code = country_code.upper()
        if country_code not in config["countries"]:
            raise KeyError(f"Unsupported country: {country_code}")
        return config["countries"][country_code]

    def get_payment_method(self, country_code: str, payment_method: str) -> dict[str, Any]:
        """Get payment method configuration for a country."""
        country = self.get_country(country_code)
        payment_method = payment_method.lower()
        if payment_method not in country["payment_methods"]:
            raise KeyError(
                f"Unsupported payment method '{payment_method}' for country {country_code}. "
                f"Available: {list(country['payment_methods'].keys())}"
            )
        return country["payment_methods"][payment_method]

    def get_fx_rate(self, from_currency: str, to_currency: str) -> dict[str, Any]:
        """Get FX rate configuration for a currency pair."""
        config = self.get_config()
        pair_key = f"{from_currency.upper()}_{to_currency.upper()}"
        if pair_key not in config["fx_rates"]:
            raise KeyError(f"No FX rate configured for {pair_key}")
        return config["fx_rates"][pair_key]

    def get_available_countries(self) -> list[str]:
        """Get list of available country codes."""
        config = self.get_config()
        return list(config["countries"].keys())

    def get_payment_methods_for_country(self, country_code: str) -> list[str]:
        """Get list of payment methods for a country."""
        country = self.get_country(country_code)
        return list(country["payment_methods"].keys())
