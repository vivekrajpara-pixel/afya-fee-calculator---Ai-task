"""API endpoints for Afya Health Fee Calculator. Thin routing layer."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.audit_store import AuditStore
from app.config_loader import FeeConfigLoader
from app.fee_engine import calculate_fees
from app.models import (
    AuditEntry,
    AuditQueryResponse,
    CompareInput,
    CompareItem,
    ErrorResponse,
    FeeCalculationRequest,
    FeeCalculationResponse,
    FeeCompareRequest,
    FeeCompareResponse,
    HealthResponse,
)

import uuid

router = APIRouter()
audit_store = AuditStore()


def _get_config_loader() -> FeeConfigLoader:
    """Get the singleton config loader."""
    return FeeConfigLoader()


@router.post(
    "/api/v1/calculate",
    response_model=FeeCalculationResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def calculate_fee(request: FeeCalculationRequest) -> FeeCalculationResponse:
    """Calculate fees for a single transaction."""
    loader = _get_config_loader()

    try:
        country_config = loader.get_country(request.country_code)
    except KeyError:
        return JSONResponse(
            status_code=400,
            content={
                "error": "unsupported_country",
                "detail": f"Country '{request.country_code}' is not supported. "
                f"Available countries: {loader.get_available_countries()}",
            },
        )

    # Validate currency matches country
    expected_currency = country_config["currency"]
    if request.currency != expected_currency:
        return JSONResponse(
            status_code=400,
            content={
                "error": "currency_mismatch",
                "detail": f"Country {request.country_code} expects currency "
                f"{expected_currency}, got {request.currency}",
            },
        )

    try:
        method_config = loader.get_payment_method(
            request.country_code, request.payment_method
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": "unsupported_payment_method",
                "detail": e.args[0],
            },
        )

    # Get FX config
    settlement_currency = country_config["settlement_currency"]
    fx_config = None
    if settlement_currency != request.currency:
        try:
            fx_config = loader.get_fx_rate(request.currency, settlement_currency)
        except KeyError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "fx_rate_not_found",
                    "detail": f"No FX rate configured for "
                    f"{request.currency} -> {settlement_currency}",
                },
            )

    result = calculate_fees(
        amount=request.amount,
        currency=request.currency,
        country_code=request.country_code,
        payment_method=request.payment_method,
        country_config=country_config,
        method_config=method_config,
        fx_config=fx_config,
    )

    audit_store.log(result)
    return result


@router.post(
    "/api/v1/compare",
    response_model=FeeCompareResponse,
    responses={400: {"model": ErrorResponse}},
)
def compare_fees(request: FeeCompareRequest) -> FeeCompareResponse:
    """Compare fees across all payment methods for a country."""
    loader = _get_config_loader()

    try:
        country_config = loader.get_country(request.country_code)
    except KeyError:
        return JSONResponse(
            status_code=400,
            content={
                "error": "unsupported_country",
                "detail": f"Country '{request.country_code}' is not supported. "
                f"Available countries: {loader.get_available_countries()}",
            },
        )

    expected_currency = country_config["currency"]
    if request.currency != expected_currency:
        return JSONResponse(
            status_code=400,
            content={
                "error": "currency_mismatch",
                "detail": f"Country {request.country_code} expects currency "
                f"{expected_currency}, got {request.currency}",
            },
        )

    settlement_currency = country_config["settlement_currency"]
    fx_config = None
    if settlement_currency != request.currency:
        try:
            fx_config = loader.get_fx_rate(request.currency, settlement_currency)
        except KeyError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "fx_rate_not_found",
                    "detail": f"No FX rate configured for "
                    f"{request.currency} -> {settlement_currency}",
                },
            )

    comparisons: list[CompareItem] = []
    methods = loader.get_payment_methods_for_country(request.country_code)

    for method_key in methods:
        method_config = loader.get_payment_method(request.country_code, method_key)

        result = calculate_fees(
            amount=request.amount,
            currency=request.currency,
            country_code=request.country_code,
            payment_method=method_key,
            country_config=country_config,
            method_config=method_config,
            fx_config=fx_config,
        )

        audit_store.log(result)

        comparisons.append(
            CompareItem(
                payment_method=method_key,
                payment_method_name=method_config.get("name", method_key),
                fee_bearer=result.fee_bearer,
                customer_pays=result.customer_pays,
                merchant_receives=result.merchant_receives,
                total_fees=result.total_fees,
            )
        )

    # Sort by customer_pays amount ascending (cheapest for customer first)
    comparisons.sort(key=lambda c: c.customer_pays.amount)

    transaction_id = f"cmp_{uuid.uuid4().hex[:12]}"

    return FeeCompareResponse(
        transaction_id=transaction_id,
        timestamp=datetime.now(timezone.utc),
        input=CompareInput(
            amount=request.amount,
            currency=request.currency,
            country_code=request.country_code,
        ),
        comparisons=comparisons,
    )


@router.get(
    "/api/v1/audit",
    response_model=AuditQueryResponse,
    responses={400: {"model": ErrorResponse}},
)
def query_audit(
    transaction_id: Optional[str] = Query(None, description="Filter by transaction ID"),
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> AuditQueryResponse:
    """Query audit log entries with optional filters."""
    # If specific transaction_id provided, return just that
    if transaction_id:
        entry = audit_store.get_by_id(transaction_id)
        if entry:
            return AuditQueryResponse(total=1, entries=[entry])
        return AuditQueryResponse(total=0, entries=[])

    total, entries = audit_store.query(
        country_code=country_code,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return AuditQueryResponse(total=total, entries=entries)


@router.get(
    "/api/v1/audit/{transaction_id}",
    responses={404: {"model": ErrorResponse}},
)
def get_audit_entry(transaction_id: str) -> AuditEntry:
    """Get a specific audit entry by transaction ID."""
    entry = audit_store.get_by_id(transaction_id)
    if entry is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found",
                "detail": f"No audit entry found for transaction ID: {transaction_id}",
            },
        )
    return entry


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint with config status."""
    loader = _get_config_loader()
    try:
        loader.get_config()
        config_loaded = True
        countries = loader.get_available_countries()
    except Exception:
        config_loaded = False
        countries = []

    return HealthResponse(
        status="healthy" if config_loaded else "degraded",
        config_loaded=config_loaded,
        countries_available=countries,
        timestamp=datetime.now(timezone.utc),
    )
