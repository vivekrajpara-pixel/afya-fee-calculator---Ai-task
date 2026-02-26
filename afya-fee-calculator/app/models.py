"""Pydantic request/response models with validation for Afya Health Fee Calculator."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, Field, PlainSerializer, field_validator

# Serialize Decimal as float in JSON output (spec requires numbers, not strings)
SerializedDecimal = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float)]


class FeeCalculationRequest(BaseModel):
    """Request model for fee calculation."""

    amount: Decimal = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(..., min_length=3, max_length=3, description="3-letter currency code (e.g., KES, NGN)")
    country_code: str = Field(..., min_length=2, max_length=2, description="2-letter country code (e.g., KE, NG)")
    payment_method: str = Field(..., min_length=1, description="Payment method (e.g., mobile_money, card, bank_transfer)")

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("country_code")
    @classmethod
    def country_code_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("payment_method")
    @classmethod
    def payment_method_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class FeeCompareRequest(BaseModel):
    """Request model for fee comparison across payment methods."""

    amount: Decimal = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(..., min_length=3, max_length=3, description="3-letter currency code")
    country_code: str = Field(..., min_length=2, max_length=2, description="2-letter country code")

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("country_code")
    @classmethod
    def country_code_uppercase(cls, v: str) -> str:
        return v.upper()


class BreakdownItem(BaseModel):
    """A single line item in the fee breakdown."""

    label: str
    description: str
    amount: SerializedDecimal
    currency: str


class CurrencyConversion(BaseModel):
    """Currency conversion details."""

    from_currency: str
    to_currency: str
    mid_market_rate: SerializedDecimal
    spread_percent: SerializedDecimal
    effective_rate: SerializedDecimal
    original_amount: SerializedDecimal
    converted_amount: SerializedDecimal
    spread_cost_in_original_currency: SerializedDecimal


class TransactionInput(BaseModel):
    """Echo of the original transaction input."""

    amount: SerializedDecimal
    currency: str
    country_code: str
    payment_method: str


class AmountCurrency(BaseModel):
    """Amount with its currency."""

    amount: SerializedDecimal
    currency: str


class FeeCalculationResponse(BaseModel):
    """Response model for fee calculation with full breakdown."""

    transaction_id: str
    timestamp: datetime
    input: TransactionInput
    customer_pays: AmountCurrency
    merchant_receives: AmountCurrency
    total_fees: AmountCurrency
    fee_bearer: str
    breakdown: list[BreakdownItem]
    currency_conversion: Optional[CurrencyConversion] = None


class CompareInput(BaseModel):
    """Input echo for fee comparison."""

    amount: SerializedDecimal
    currency: str
    country_code: str


class CompareItem(BaseModel):
    """A single payment method comparison result."""

    payment_method: str
    payment_method_name: str
    fee_bearer: str
    customer_pays: AmountCurrency
    merchant_receives: AmountCurrency
    total_fees: AmountCurrency


class FeeCompareResponse(BaseModel):
    """Response model for fee comparison."""

    transaction_id: str
    timestamp: datetime
    input: CompareInput
    comparisons: list[CompareItem]


class AuditEntry(BaseModel):
    """An audit log entry."""

    transaction_id: str
    timestamp: datetime
    country_code: str
    payment_method: str
    amount: SerializedDecimal
    currency: str
    result: FeeCalculationResponse


class AuditQueryResponse(BaseModel):
    """Response for audit log queries."""

    total: int
    entries: list[AuditEntry]


class ErrorResponse(BaseModel):
    """Structured error response."""

    error: str
    detail: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    config_loaded: bool
    countries_available: list[str]
    timestamp: datetime
