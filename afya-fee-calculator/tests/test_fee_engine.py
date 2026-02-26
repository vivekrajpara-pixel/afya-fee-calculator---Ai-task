"""Unit tests for the fee calculation engine. 20+ tests covering all fee types and edge cases."""

import os
from decimal import Decimal

import pytest

from app.config_loader import FeeConfigLoader
from app.fee_engine import _calculate_single_fee, _round, calculate_fees


@pytest.fixture(autouse=True)
def reset_singleton():
    FeeConfigLoader.reset()
    yield
    FeeConfigLoader.reset()


@pytest.fixture
def loader() -> FeeConfigLoader:
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "fee_rules.json",
    )
    loader = FeeConfigLoader()
    loader.load(config_path)
    return loader


def _calc(loader: FeeConfigLoader, country: str, method: str, amount: Decimal):
    """Helper to run a calculation with loaded config."""
    country_config = loader.get_country(country)
    method_config = loader.get_payment_method(country, method)
    settlement = country_config["settlement_currency"]
    fx_config = None
    if settlement != country_config["currency"]:
        fx_config = loader.get_fx_rate(country_config["currency"], settlement)
    return calculate_fees(
        amount=amount,
        currency=country_config["currency"],
        country_code=country,
        payment_method=method,
        country_config=country_config,
        method_config=method_config,
        fx_config=fx_config,
    )


class TestRounding:
    """Tests for Decimal rounding."""

    def test_round_half_up(self):
        assert _round(Decimal("1.235")) == Decimal("1.24")

    def test_round_half_up_exact(self):
        assert _round(Decimal("1.225")) == Decimal("1.23")

    def test_round_down(self):
        assert _round(Decimal("1.234")) == Decimal("1.23")

    def test_round_already_two_places(self):
        assert _round(Decimal("1.50")) == Decimal("1.50")


class TestSingleFeeCalculation:
    """Tests for individual fee component calculations."""

    def test_percentage_plus_fixed(self):
        config = {"type": "percentage_plus_fixed", "percentage": 2.9, "fixed": 10.0}
        fee, desc = _calculate_single_fee(config, Decimal("5000"))
        # 5000 * 2.9% + 10 = 145 + 10 = 155
        assert fee == Decimal("155.00")

    def test_fixed_only(self):
        config = {"type": "fixed", "fixed": 50.0}
        fee, desc = _calculate_single_fee(config, Decimal("5000"))
        assert fee == Decimal("50.00")

    def test_none_fee(self):
        config = {"type": "none"}
        fee, desc = _calculate_single_fee(config, Decimal("5000"))
        assert fee == Decimal("0")

    def test_tiered_below_threshold(self):
        config = {
            "type": "tiered",
            "tiers": [
                {"max_amount": 10000, "percentage": 3.2, "fixed": 50},
                {"max_amount": None, "percentage": 2.5, "fixed": 50},
            ],
        }
        fee, desc = _calculate_single_fee(config, Decimal("8000"))
        # 8000 * 3.2% + 50 = 256 + 50 = 306
        assert fee == Decimal("306.00")

    def test_tiered_above_threshold(self):
        config = {
            "type": "tiered",
            "tiers": [
                {"max_amount": 10000, "percentage": 3.2, "fixed": 50},
                {"max_amount": None, "percentage": 2.5, "fixed": 50},
            ],
        }
        fee, desc = _calculate_single_fee(config, Decimal("25000"))
        # 25000 * 2.5% + 50 = 625 + 50 = 675
        assert fee == Decimal("675.00")

    def test_tiered_at_exact_boundary(self):
        config = {
            "type": "tiered",
            "tiers": [
                {"max_amount": 10000, "percentage": 3.2, "fixed": 50},
                {"max_amount": None, "percentage": 2.5, "fixed": 50},
            ],
        }
        fee, desc = _calculate_single_fee(config, Decimal("10000"))
        # At boundary: <=10000 so uses first tier: 10000 * 3.2% + 50 = 320 + 50 = 370
        assert fee == Decimal("370.00")

    def test_three_tier_pricing(self):
        """Test South Africa 3-tier card pricing."""
        config = {
            "type": "tiered",
            "tiers": [
                {"max_amount": 1000, "percentage": 3.5, "fixed": 5},
                {"max_amount": 10000, "percentage": 2.8, "fixed": 5},
                {"max_amount": None, "percentage": 2.2, "fixed": 5},
            ],
        }
        # Small: 500 ZAR -> 3.5% + 5 = 17.5 + 5 = 22.5
        fee, _ = _calculate_single_fee(config, Decimal("500"))
        assert fee == Decimal("22.50")

        # Medium: 5000 ZAR -> 2.8% + 5 = 140 + 5 = 145
        fee, _ = _calculate_single_fee(config, Decimal("5000"))
        assert fee == Decimal("145.00")

        # Large: 15000 ZAR -> 2.2% + 5 = 330 + 5 = 335
        fee, _ = _calculate_single_fee(config, Decimal("15000"))
        assert fee == Decimal("335.00")


class TestKenyaFees:
    """Tests for Kenya fee calculations (16% VAT on both fees, FX to USD)."""

    def test_ke_mobile_money_5000(self, loader):
        """Kenya mobile_money 5000 KES: merchant-absorbs, VAT on both, FX."""
        result = _calc(loader, "KE", "mobile_money", Decimal("5000"))

        assert result.fee_bearer == "merchant"
        assert result.input.currency == "KES"
        assert result.customer_pays.amount == Decimal("5000.00")
        assert result.customer_pays.currency == "KES"

        # Processor: 1.5% * 5000 + 0 = 75.00
        # PM fee: 1.0% * 5000 + 10 = 60.00
        # VAT: 16% * (75 + 60) = 16% * 135 = 21.60
        # Total fees: 75 + 60 + 21.60 = 156.60
        assert result.total_fees.amount == Decimal("156.60")

        # FX: effective = 0.0065 * (1 - 0.02) = 0.006370
        # Merchant receives: (5000 - 156.60) * 0.006370 = 4843.40 * 0.006370 = 30.85
        assert result.merchant_receives.currency == "USD"
        assert result.merchant_receives.amount == Decimal("30.85")
        assert result.currency_conversion is not None
        assert result.currency_conversion.effective_rate == Decimal("0.006370")

    def test_ke_card_5000(self, loader):
        """Kenya card 5000 KES: customer-pays, VAT, FX."""
        result = _calc(loader, "KE", "card", Decimal("5000"))

        assert result.fee_bearer == "customer"

        # Processor: 2.9% * 5000 + 10 = 145 + 10 = 155.00
        # PM fee: none = 0
        # VAT: 16% * 155 = 24.80
        # Total: 155 + 0 + 24.80 = 179.80
        assert result.total_fees.amount == Decimal("179.80")

        # Customer pays: 5000 + 179.80 = 5179.80
        assert result.customer_pays.amount == Decimal("5179.80")

    def test_ke_bank_transfer_5000(self, loader):
        """Kenya bank_transfer 5000 KES: fixed fee, merchant-absorbs, VAT."""
        result = _calc(loader, "KE", "bank_transfer", Decimal("5000"))

        assert result.fee_bearer == "merchant"

        # Processor: fixed 50 KES
        # PM fee: none = 0
        # VAT: 16% * 50 = 8.00
        # Total: 50 + 0 + 8 = 58.00
        assert result.total_fees.amount == Decimal("58.00")
        assert result.customer_pays.amount == Decimal("5000.00")


class TestNigeriaFees:
    """Tests for Nigeria fee calculations (7.5% VAT on processor only, tiered mobile money)."""

    def test_ng_mobile_money_below_tier(self, loader):
        """Nigeria mobile_money 8000 NGN: below 10K tier threshold."""
        result = _calc(loader, "NG", "mobile_money", Decimal("8000"))

        # Processor: 1.8% * 8000 + 25 = 144 + 25 = 169.00
        # PM (tier <=10K): 3.2% * 8000 + 50 = 256 + 50 = 306.00
        # VAT: 7.5% on processor only = 7.5% * 169 = 12.675 -> 12.68
        # Total: 169 + 306 + 12.68 = 487.68
        assert result.total_fees.amount == Decimal("487.68")

    def test_ng_mobile_money_above_tier(self, loader):
        """Nigeria mobile_money 25000 NGN: above 10K tier threshold."""
        result = _calc(loader, "NG", "mobile_money", Decimal("25000"))

        # Processor: 1.8% * 25000 + 25 = 450 + 25 = 475.00
        # PM (tier >10K): 2.5% * 25000 + 50 = 625 + 50 = 675.00
        # VAT: 7.5% on processor only = 7.5% * 475 = 35.625 -> 35.63
        # Total: 475 + 675 + 35.63 = 1185.63
        assert result.total_fees.amount == Decimal("1185.63")

    def test_ng_card_customer_pays(self, loader):
        """Nigeria card: customer pays fees."""
        result = _calc(loader, "NG", "card", Decimal("10000"))

        assert result.fee_bearer == "customer"

        # Processor: 3.5% * 10000 + 100 = 350 + 100 = 450
        # PM: none = 0
        # VAT: 7.5% on 450 = 33.75
        # Total: 450 + 0 + 33.75 = 483.75
        assert result.total_fees.amount == Decimal("483.75")
        assert result.customer_pays.amount == Decimal("10483.75")

    def test_ng_bank_transfer_fixed(self, loader):
        """Nigeria bank_transfer: flat fee, merchant absorbs."""
        result = _calc(loader, "NG", "bank_transfer", Decimal("50000"))

        # Processor: fixed 75 NGN
        # PM: none = 0
        # VAT: 7.5% * 75 = 5.625 -> 5.63
        # Total: 75 + 0 + 5.63 = 80.63
        assert result.total_fees.amount == Decimal("80.63")
        assert result.fee_bearer == "merchant"


class TestGhanaFees:
    """Tests for Ghana (15% tax on both fees, settles in GHS - no FX)."""

    def test_gh_card_500(self, loader):
        """Ghana card 500 GHS: small amount, no FX, 15% tax."""
        result = _calc(loader, "GH", "card", Decimal("500"))

        assert result.currency_conversion is None  # GHS settles in GHS

        # Processor: 2.5% * 500 + 2 = 12.5 + 2 = 14.50
        # PM: 0.5% * 500 + 0 = 2.50
        # Tax: 15% * (14.50 + 2.50) = 15% * 17 = 2.55
        # Total: 14.50 + 2.50 + 2.55 = 19.55
        assert result.total_fees.amount == Decimal("19.55")

        # Customer pays (customer-bearing): 500 + 19.55 = 519.55
        assert result.customer_pays.amount == Decimal("519.55")
        assert result.customer_pays.currency == "GHS"

    def test_gh_mobile_money_merchant_absorbs(self, loader):
        """Ghana mobile_money: merchant absorbs fees."""
        result = _calc(loader, "GH", "mobile_money", Decimal("1000"))

        # Processor: 1.5% * 1000 + 0.50 = 15 + 0.50 = 15.50
        # PM: 1.0% * 1000 + 0.20 = 10 + 0.20 = 10.20
        # Tax: 15% * (15.50 + 10.20) = 15% * 25.70 = 3.855 -> 3.86
        # Total: 15.50 + 10.20 + 3.86 = 29.56
        assert result.total_fees.amount == Decimal("29.56")
        assert result.customer_pays.amount == Decimal("1000.00")
        assert result.merchant_receives.amount == Decimal("970.44")  # 1000 - 29.56

    def test_gh_no_fx_conversion(self, loader):
        """Ghana: settlement is GHS, no FX conversion needed."""
        result = _calc(loader, "GH", "bank_transfer", Decimal("500"))
        assert result.currency_conversion is None
        assert result.merchant_receives.currency == "GHS"


class TestSouthAfricaFees:
    """Tests for South Africa (0% tax, tiered card pricing, FX to USD)."""

    def test_za_card_small_500(self, loader):
        """South Africa card 500 ZAR: tier 1 (3.5% + 5), customer pays."""
        result = _calc(loader, "ZA", "card", Decimal("500"))

        # Processor (tier <=1000): 3.5% * 500 + 5 = 17.5 + 5 = 22.50
        # PM: none = 0
        # Tax: 0% = 0
        # Total: 22.50
        assert result.total_fees.amount == Decimal("22.50")
        assert result.customer_pays.amount == Decimal("522.50")

    def test_za_card_large_15000(self, loader):
        """South Africa card 15000 ZAR: tier 3 (2.2% + 5), customer pays."""
        result = _calc(loader, "ZA", "card", Decimal("15000"))

        # Processor (tier >10000): 2.2% * 15000 + 5 = 330 + 5 = 335.00
        # PM: none = 0
        # Tax: 0% = 0
        # Total: 335.00
        assert result.total_fees.amount == Decimal("335.00")
        assert result.customer_pays.amount == Decimal("15335.00")

    def test_za_card_mid_tier(self, loader):
        """South Africa card 5000 ZAR: tier 2 (2.8% + 5)."""
        result = _calc(loader, "ZA", "card", Decimal("5000"))

        # Processor (tier 1001-10000): 2.8% * 5000 + 5 = 140 + 5 = 145.00
        assert result.total_fees.amount == Decimal("145.00")

    def test_za_no_tax_on_fees(self, loader):
        """South Africa: 0% tax means no tax component."""
        result = _calc(loader, "ZA", "mobile_money", Decimal("1000"))
        # Should have no tax breakdown item
        tax_items = [b for b in result.breakdown if "Tax" in b.label or "VAT" in b.label]
        assert len(tax_items) == 0

    def test_za_bank_transfer_fixed(self, loader):
        """South Africa bank_transfer: flat 15 ZAR, 0% tax."""
        result = _calc(loader, "ZA", "bank_transfer", Decimal("10000"))

        assert result.total_fees.amount == Decimal("15.00")
        assert result.fee_bearer == "merchant"


class TestFXConversion:
    """Tests for currency conversion logic."""

    def test_kes_to_usd_spread(self, loader):
        """Test KES->USD conversion with 2% spread."""
        result = _calc(loader, "KE", "mobile_money", Decimal("5000"))
        conv = result.currency_conversion

        assert conv is not None
        assert conv.from_currency == "KES"
        assert conv.to_currency == "USD"
        assert conv.mid_market_rate == Decimal("0.0065")
        assert conv.spread_percent == Decimal("2.0")
        # effective = 0.0065 * (1 - 0.02) = 0.0065 * 0.98 = 0.006370
        assert conv.effective_rate == Decimal("0.006370")
        assert conv.spread_cost_in_original_currency == Decimal("0.65")

    def test_ngn_to_usd_spread(self, loader):
        """Test NGN->USD conversion with 3% spread."""
        result = _calc(loader, "NG", "bank_transfer", Decimal("50000"))
        conv = result.currency_conversion

        assert conv is not None
        assert conv.mid_market_rate == Decimal("0.00062")
        assert conv.spread_percent == Decimal("3.0")
        # effective = 0.00062 * (1 - 0.03) = 0.00062 * 0.97 = 0.000601
        assert conv.effective_rate == Decimal("0.000601")

    def test_ghs_no_conversion(self, loader):
        """Test GHS settles in GHS, no conversion."""
        result = _calc(loader, "GH", "card", Decimal("100"))
        assert result.currency_conversion is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_amount(self, loader):
        """Test with very small amount where fixed fee dominates."""
        result = _calc(loader, "KE", "bank_transfer", Decimal("10"))
        # Fixed fee 50 KES > the transaction amount of 10 KES
        # Fee is still 50 KES + VAT 8 = 58 KES
        assert result.total_fees.amount == Decimal("58.00")

    def test_very_large_amount(self, loader):
        """Test with very large amount for tiered pricing."""
        result = _calc(loader, "ZA", "card", Decimal("1000000"))
        # Tier 3: 2.2% * 1000000 + 5 = 22000 + 5 = 22005
        assert result.total_fees.amount == Decimal("22005.00")

    def test_amount_at_exact_tier_boundary_10000_ngn(self, loader):
        """Test amount exactly at tier boundary (10000 NGN for Nigeria mobile_money)."""
        result = _calc(loader, "NG", "mobile_money", Decimal("10000"))
        # At 10000: uses tier <=10K
        # Processor: 1.8% * 10000 + 25 = 180 + 25 = 205
        # PM (tier <=10K): 3.2% * 10000 + 50 = 320 + 50 = 370
        # VAT: 7.5% * 205 = 15.375 -> 15.38
        # Total: 205 + 370 + 15.38 = 590.38
        assert result.total_fees.amount == Decimal("590.38")

    def test_amount_just_above_tier_boundary(self, loader):
        """Test amount just above tier boundary (10001 NGN)."""
        result = _calc(loader, "NG", "mobile_money", Decimal("10001"))
        # Above 10000: uses tier >10K
        # Processor: 1.8% * 10001 + 25 = 180.018 + 25 = 205.018 -> 205.02
        # PM (tier >10K): 2.5% * 10001 + 50 = 250.025 + 50 = 300.025 -> 300.03
        # VAT: 7.5% * 205.02 = 15.3765 -> 15.38
        # Total: 205.02 + 300.03 + 15.38 = 520.43
        assert result.total_fees.amount == Decimal("520.43")

    def test_breakdown_contains_expected_items(self, loader):
        """Test that breakdown has the expected line items."""
        result = _calc(loader, "KE", "mobile_money", Decimal("5000"))

        labels = [b.label for b in result.breakdown]
        assert "Processor Fee" in labels
        assert "Payment Method Fee" in labels
        assert "VAT on Fees" in labels
        assert "FX Conversion" in labels

    def test_transaction_id_generated(self, loader):
        """Test that a unique transaction ID is generated."""
        result1 = _calc(loader, "KE", "card", Decimal("100"))
        result2 = _calc(loader, "KE", "card", Decimal("100"))
        assert result1.transaction_id.startswith("txn_")
        assert result2.transaction_id.startswith("txn_")
        assert result1.transaction_id != result2.transaction_id

    def test_timestamp_is_set(self, loader):
        """Test that timestamp is set on result."""
        result = _calc(loader, "KE", "card", Decimal("100"))
        assert result.timestamp is not None
