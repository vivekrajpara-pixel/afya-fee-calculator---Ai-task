"""Core fee calculation engine using Decimal math. Pure functions, no side effects."""

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional
import uuid

from app.models import (
    AmountCurrency,
    BreakdownItem,
    CurrencyConversion,
    FeeCalculationResponse,
    TransactionInput,
)

# Precision constants
TWO_PLACES = Decimal("0.01")
SIX_PLACES = Decimal("0.000001")


def _round(value: Decimal) -> Decimal:
    """Round a Decimal to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _round_rate(value: Decimal) -> Decimal:
    """Round an FX rate to 6 decimal places using ROUND_HALF_UP."""
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _to_decimal(value: Any) -> Decimal:
    """Convert a value to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _calculate_single_fee(fee_config: dict[str, Any], amount: Decimal) -> tuple[Decimal, str]:
    """
    Calculate a single fee component based on its config type.
    Returns (fee_amount, description).
    """
    fee_type = fee_config["type"]

    if fee_type == "none":
        return Decimal("0"), "No fee"

    if fee_type == "fixed":
        fixed = _to_decimal(fee_config["fixed"])
        return _round(fixed), f"Flat {fixed} fee"

    if fee_type == "percentage_plus_fixed":
        pct = _to_decimal(fee_config["percentage"])
        fixed = _to_decimal(fee_config["fixed"])
        fee = amount * pct / Decimal("100") + fixed
        if fixed > 0:
            desc = f"{pct}% + {fixed} fee"
        else:
            desc = f"{pct}% fee"
        return _round(fee), desc

    if fee_type == "tiered":
        tiers = fee_config["tiers"]
        for tier in tiers:
            max_amount = tier.get("max_amount")
            if max_amount is None or amount <= _to_decimal(max_amount):
                pct = _to_decimal(tier["percentage"])
                fixed = _to_decimal(tier["fixed"])
                fee = amount * pct / Decimal("100") + fixed
                tier_desc = tier.get("description", "")
                if max_amount is not None:
                    desc = f"{pct}% + {fixed} (tier: <={_to_decimal(max_amount)})"
                else:
                    desc = f"{pct}% + {fixed} (tier: above threshold)"
                return _round(fee), desc
        # Fallback to last tier if no match (shouldn't happen with null max_amount)
        last_tier = tiers[-1]
        pct = _to_decimal(last_tier["percentage"])
        fixed = _to_decimal(last_tier["fixed"])
        fee = amount * pct / Decimal("100") + fixed
        return _round(fee), f"{pct}% + {fixed} (fallback tier)"

    raise ValueError(f"Unknown fee type: {fee_type}")


def calculate_fees(
    amount: Decimal,
    currency: str,
    country_code: str,
    payment_method: str,
    country_config: dict[str, Any],
    method_config: dict[str, Any],
    fx_config: Optional[dict[str, Any]],
) -> FeeCalculationResponse:
    """
    Calculate all fees for a transaction. Pure function.

    Args:
        amount: Transaction amount
        currency: Transaction currency code
        country_code: Country code
        payment_method: Payment method key
        country_config: Country configuration from fee_rules.json
        method_config: Payment method configuration
        fx_config: FX rate configuration (None if same currency settlement)

    Returns:
        FeeCalculationResponse with full breakdown
    """
    amount = _to_decimal(amount)
    settlement_currency = country_config["settlement_currency"]
    fee_bearer = method_config["fee_bearer"]
    tax_config = country_config["tax"]

    # Step 1: Calculate processor fee
    processor_fee, processor_desc = _calculate_single_fee(
        method_config["processor_fee"], amount
    )

    # Step 2: Calculate payment method fee
    payment_method_fee, pm_desc = _calculate_single_fee(
        method_config["payment_method_fee"], amount
    )

    # Step 3: Calculate tax (cascading on specified fee components)
    tax_rate = _to_decimal(tax_config["rate_percent"])
    applies_to = tax_config["applies_to"]
    taxable_amount = Decimal("0")
    taxed_components = []

    if "processor_fee" in applies_to:
        taxable_amount += processor_fee
        taxed_components.append("processor_fee")
    if "payment_method_fee" in applies_to:
        taxable_amount += payment_method_fee
        taxed_components.append("payment_method_fee")

    tax_amount = _round(taxable_amount * tax_rate / Decimal("100"))
    tax_name = tax_config.get("name", "Tax")

    # Step 4: Total fees in local currency
    total_fees = processor_fee + payment_method_fee + tax_amount

    # Step 5: Build breakdown
    breakdown: list[BreakdownItem] = []

    if processor_fee > 0 or method_config["processor_fee"]["type"] != "none":
        breakdown.append(
            BreakdownItem(
                label="Processor Fee",
                description=f"{processor_desc} on {amount} {currency}",
                amount=processor_fee,
                currency=currency,
            )
        )

    if payment_method_fee > 0 or method_config["payment_method_fee"]["type"] != "none":
        breakdown.append(
            BreakdownItem(
                label="Payment Method Fee",
                description=f"{pm_desc} on {amount} {currency}",
                amount=payment_method_fee,
                currency=currency,
            )
        )

    if tax_rate > 0 and taxable_amount > 0:
        breakdown.append(
            BreakdownItem(
                label=f"{tax_name} on Fees",
                description=f"{tax_rate}% on {' + '.join(taxed_components)}",
                amount=tax_amount,
                currency=currency,
            )
        )

    # Step 6: Currency conversion
    currency_conversion: Optional[CurrencyConversion] = None

    if settlement_currency != currency and fx_config is not None:
        mid_rate = _to_decimal(fx_config["mid_market_rate"])
        spread_pct = _to_decimal(fx_config["spread_percent"])
        effective_rate = _round_rate(mid_rate * (Decimal("1") - spread_pct / Decimal("100")))

        # Spread cost: difference between mid-rate and effective-rate conversion
        # Expressed in settlement currency terms
        spread_cost = _round(amount * mid_rate - amount * effective_rate)

        # For merchant-absorbs: merchant gets (amount - fees) converted
        # For customer-pays: merchant gets amount converted (fees added on top for customer)
        if fee_bearer == "merchant":
            amount_to_convert = amount - total_fees
        else:
            amount_to_convert = amount

        converted_amount = _round(amount_to_convert * effective_rate)

        currency_conversion = CurrencyConversion(
            from_currency=currency,
            to_currency=settlement_currency,
            mid_market_rate=mid_rate,
            spread_percent=spread_pct,
            effective_rate=effective_rate,
            original_amount=amount,
            converted_amount=converted_amount,
            spread_cost_in_original_currency=spread_cost,
        )

        breakdown.append(
            BreakdownItem(
                label="FX Conversion",
                description=(
                    f"{currency}->{settlement_currency} at {effective_rate} "
                    f"(mid: {mid_rate}, spread: {spread_pct}%)"
                ),
                amount=spread_cost,
                currency=currency,
            )
        )

    # Step 7: Determine customer_pays and merchant_receives
    if fee_bearer == "merchant":
        customer_pays_amount = amount
        customer_pays_currency = currency

        if currency_conversion is not None:
            merchant_receives_amount = currency_conversion.converted_amount
            merchant_receives_currency = settlement_currency
        else:
            merchant_receives_amount = _round(amount - total_fees)
            merchant_receives_currency = currency
    else:
        # customer pays: fees are added on top
        customer_pays_amount = _round(amount + total_fees)
        customer_pays_currency = currency

        if currency_conversion is not None:
            merchant_receives_amount = currency_conversion.converted_amount
            merchant_receives_currency = settlement_currency
        else:
            merchant_receives_amount = amount
            merchant_receives_currency = currency

    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"

    return FeeCalculationResponse(
        transaction_id=transaction_id,
        timestamp=datetime.now(timezone.utc),
        input=TransactionInput(
            amount=amount,
            currency=currency,
            country_code=country_code,
            payment_method=payment_method,
        ),
        customer_pays=AmountCurrency(
            amount=customer_pays_amount,
            currency=customer_pays_currency,
        ),
        merchant_receives=AmountCurrency(
            amount=merchant_receives_amount,
            currency=merchant_receives_currency,
        ),
        total_fees=AmountCurrency(
            amount=total_fees,
            currency=currency,
        ),
        fee_bearer=fee_bearer,
        breakdown=breakdown,
        currency_conversion=currency_conversion,
    )
