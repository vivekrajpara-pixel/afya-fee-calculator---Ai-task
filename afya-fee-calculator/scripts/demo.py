#!/usr/bin/env python3
"""
Demo script for Afya Health Cross-Border Fee Calculator.
Runs 10 scenarios and displays formatted results.

Usage: python scripts/demo.py
"""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal

from app.config_loader import FeeConfigLoader
from app.fee_engine import calculate_fees
from app.models import FeeCalculationResponse


def format_money(amount: Decimal, currency: str) -> str:
    """Format a monetary amount with currency."""
    return f"{float(amount):,.2f} {currency}"


def print_divider(char: str = "=", length: int = 70) -> None:
    print(char * length)


def print_result(scenario_num: int, title: str, result: "FeeCalculationResponse") -> None:
    """Pretty-print a fee calculation result."""
    print_divider()
    print(f"  SCENARIO {scenario_num}: {title}")
    print_divider()
    print(f"  Transaction ID: {result.transaction_id}")
    print(f"  Input: {format_money(result.input.amount, result.input.currency)} "
          f"in {result.input.country_code} via {result.input.payment_method}")
    print(f"  Fee Bearer: {result.fee_bearer}")
    print()

    print("  FEE BREAKDOWN:")
    for item in result.breakdown:
        print(f"    - {item.label}: {format_money(item.amount, item.currency)}")
        print(f"      ({item.description})")
    print()

    print(f"  Total Fees: {format_money(result.total_fees.amount, result.total_fees.currency)}")
    print(f"  Customer Pays: {format_money(result.customer_pays.amount, result.customer_pays.currency)}")
    print(f"  Merchant Receives: {format_money(result.merchant_receives.amount, result.merchant_receives.currency)}")

    if result.currency_conversion:
        conv = result.currency_conversion
        print()
        print(f"  FX CONVERSION:")
        print(f"    {conv.from_currency} -> {conv.to_currency}")
        print(f"    Mid-market rate: {conv.mid_market_rate}")
        print(f"    Spread: {conv.spread_percent}%")
        print(f"    Effective rate: {conv.effective_rate}")
        print(f"    Spread cost: {format_money(conv.spread_cost_in_original_currency, conv.from_currency)}")

    print()


def run_calc(loader: FeeConfigLoader, country: str, method: str, amount: Decimal) -> FeeCalculationResponse:
    """Run a single calculation."""
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


def main() -> None:
    print()
    print_divider("*")
    print("  AFYA HEALTH CROSS-BORDER FEE CALCULATOR - DEMO")
    print("  Calculating fees for 10 scenarios across 4 countries")
    print_divider("*")

    # Load config
    loader = FeeConfigLoader()
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "fee_rules.json",
    )
    loader.load(config_path)

    # Scenario 1: Kenya mobile_money 5000 KES
    result = run_calc(loader, "KE", "mobile_money", Decimal("5000"))
    print_result(1, "Kenya Mobile Money 5,000 KES (merchant-absorbs, VAT, FX)", result)

    # Scenario 2: Kenya card 5000 KES
    result = run_calc(loader, "KE", "card", Decimal("5000"))
    print_result(2, "Kenya Card 5,000 KES (customer-pays, VAT, FX)", result)

    # Scenario 3: Kenya bank_transfer 5000 KES
    result = run_calc(loader, "KE", "bank_transfer", Decimal("5000"))
    print_result(3, "Kenya Bank Transfer 5,000 KES (fixed fee, merchant-absorbs)", result)

    # Scenario 4: Nigeria mobile_money 8000 NGN (below tier)
    result = run_calc(loader, "NG", "mobile_money", Decimal("8000"))
    print_result(4, "Nigeria Mobile Money 8,000 NGN (below 10K tier)", result)

    # Scenario 5: Nigeria mobile_money 25000 NGN (above tier)
    result = run_calc(loader, "NG", "mobile_money", Decimal("25000"))
    print_result(5, "Nigeria Mobile Money 25,000 NGN (above 10K tier - lower rate)", result)

    # Scenario 6: Ghana card 500 GHS (no FX, 15% tax)
    result = run_calc(loader, "GH", "card", Decimal("500"))
    print_result(6, "Ghana Card 500 GHS (no FX conversion, 15% tax)", result)

    # Scenario 7: South Africa card 500 ZAR (tier 1 - highest rate)
    result = run_calc(loader, "ZA", "card", Decimal("500"))
    print_result(7, "South Africa Card 500 ZAR (tier 1: 3.5% - small amount)", result)

    # Scenario 8: South Africa card 15000 ZAR (tier 3 - lowest rate)
    result = run_calc(loader, "ZA", "card", Decimal("15000"))
    print_result(8, "South Africa Card 15,000 ZAR (tier 3: 2.2% - large amount)", result)

    # Scenario 9: Fee Comparison for Kenya 5000 KES
    print_divider()
    print("  SCENARIO 9: Fee Comparison - Kenya 5,000 KES (all methods ranked)")
    print_divider()

    methods = ["mobile_money", "card", "bank_transfer"]
    comparisons = []
    for method in methods:
        r = run_calc(loader, "KE", method, Decimal("5000"))
        comparisons.append((method, r))

    comparisons.sort(key=lambda x: x[1].customer_pays.amount)

    for rank, (method, r) in enumerate(comparisons, 1):
        method_name = loader.get_payment_method("KE", method).get("name", method)
        print(f"  {rank}. {method_name}")
        print(f"     Customer Pays: {format_money(r.customer_pays.amount, r.customer_pays.currency)}")
        print(f"     Merchant Receives: {format_money(r.merchant_receives.amount, r.merchant_receives.currency)}")
        print(f"     Total Fees: {format_money(r.total_fees.amount, r.total_fees.currency)} ({r.fee_bearer} absorbs)")
        print()

    # Scenario 10: Error Case - unsupported country
    print_divider()
    print("  SCENARIO 10: Error Case - Unsupported Country")
    print_divider()

    try:
        loader.get_country("FR")
        print("  ERROR: Should have raised an exception!")
    except KeyError as e:
        print(f"  Correctly raised error: {e}")
        print("  The API would return HTTP 400 with a structured error response.")

    print()
    print_divider("*")
    print("  DEMO COMPLETE - All 10 scenarios executed successfully!")
    print_divider("*")
    print()


if __name__ == "__main__":
    main()
