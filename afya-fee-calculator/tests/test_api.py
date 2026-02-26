"""Integration tests for all API endpoints. 15+ tests."""

import os

import pytest
from fastapi.testclient import TestClient

from app.config_loader import FeeConfigLoader
from app.routes import audit_store


@pytest.fixture(autouse=True)
def reset_state():
    """Reset singleton and audit store before each test."""
    FeeConfigLoader.reset()
    audit_store.clear()
    # Force config load from default path
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "fee_rules.json",
    )
    loader = FeeConfigLoader()
    loader.load(config_path)
    yield
    FeeConfigLoader.reset()
    audit_store.clear()


@pytest.fixture
def client():
    """Create a test client."""
    from main import app
    return TestClient(app)


class TestCalculateEndpoint:
    """Tests for POST /api/v1/calculate."""

    def test_calculate_ke_mobile_money(self, client):
        """Test basic Kenya mobile money calculation."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 5000,
                "currency": "KES",
                "country_code": "KE",
                "payment_method": "mobile_money",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"].startswith("txn_")
        assert data["fee_bearer"] == "merchant"
        assert float(data["customer_pays"]["amount"]) == 5000.0
        assert data["total_fees"]["currency"] == "KES"
        assert data["currency_conversion"] is not None
        assert data["currency_conversion"]["to_currency"] == "USD"

    def test_calculate_ng_card(self, client):
        """Test Nigeria card calculation with customer pays."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 10000,
                "currency": "NGN",
                "country_code": "NG",
                "payment_method": "card",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fee_bearer"] == "customer"
        assert float(data["customer_pays"]["amount"]) > 10000

    def test_calculate_gh_no_fx(self, client):
        """Test Ghana calculation with no FX conversion."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 500,
                "currency": "GHS",
                "country_code": "GH",
                "payment_method": "card",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["currency_conversion"] is None
        assert data["merchant_receives"]["currency"] == "GHS"

    def test_calculate_za_tiered_card(self, client):
        """Test South Africa tiered card pricing."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 15000,
                "currency": "ZAR",
                "country_code": "ZA",
                "payment_method": "card",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Tier 3: 2.2% + 5 = 335.00
        assert float(data["total_fees"]["amount"]) == 335.0

    def test_calculate_has_breakdown(self, client):
        """Test that response contains breakdown items."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 5000,
                "currency": "KES",
                "country_code": "KE",
                "payment_method": "mobile_money",
            },
        )
        data = response.json()
        assert len(data["breakdown"]) >= 3  # processor, pm, tax, fx

    def test_calculate_unsupported_country(self, client):
        """Test error for unsupported country."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 100,
                "currency": "EUR",
                "country_code": "FR",
                "payment_method": "card",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "unsupported_country"
        assert "detail" in data

    def test_calculate_unsupported_payment_method(self, client):
        """Test error for unsupported payment method."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 5000,
                "currency": "KES",
                "country_code": "KE",
                "payment_method": "crypto",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "unsupported_payment_method"
        # Verify no extra quotes wrapping the detail string
        assert not data["detail"].startswith('"')
        assert "crypto" in data["detail"]

    def test_calculate_currency_mismatch(self, client):
        """Test error when currency doesn't match country."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 5000,
                "currency": "USD",
                "country_code": "KE",
                "payment_method": "card",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "currency_mismatch" in str(data)

    def test_calculate_negative_amount(self, client):
        """Test validation error for negative amount."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": -100,
                "currency": "KES",
                "country_code": "KE",
                "payment_method": "card",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "validation_error"
        assert "detail" in data

    def test_calculate_zero_amount(self, client):
        """Test validation error for zero amount."""
        response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 0,
                "currency": "KES",
                "country_code": "KE",
                "payment_method": "card",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "validation_error"

    def test_calculate_missing_fields(self, client):
        """Test validation error for missing required fields."""
        response = client.post(
            "/api/v1/calculate",
            json={"amount": 5000},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "validation_error"


class TestCompareEndpoint:
    """Tests for POST /api/v1/compare."""

    def test_compare_ke_all_methods(self, client):
        """Test comparing all payment methods in Kenya."""
        response = client.post(
            "/api/v1/compare",
            json={
                "amount": 5000,
                "currency": "KES",
                "country_code": "KE",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["comparisons"]) == 3
        # Should be sorted by customer_pays ascending
        amounts = [c["customer_pays"]["amount"] for c in data["comparisons"]]
        assert amounts == sorted(amounts)

    def test_compare_unsupported_country(self, client):
        """Test error for unsupported country in comparison."""
        response = client.post(
            "/api/v1/compare",
            json={
                "amount": 5000,
                "currency": "EUR",
                "country_code": "FR",
            },
        )
        assert response.status_code == 400

    def test_compare_has_all_fields(self, client):
        """Test that comparison items have required fields."""
        response = client.post(
            "/api/v1/compare",
            json={
                "amount": 1000,
                "currency": "GHS",
                "country_code": "GH",
            },
        )
        data = response.json()
        for item in data["comparisons"]:
            assert "payment_method" in item
            assert "payment_method_name" in item
            assert "fee_bearer" in item
            assert "customer_pays" in item
            assert "merchant_receives" in item
            assert "total_fees" in item


class TestAuditEndpoint:
    """Tests for GET /api/v1/audit and GET /api/v1/audit/{id}."""

    def test_audit_empty(self, client):
        """Test audit log returns empty when no calculations done."""
        response = client.get("/api/v1/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["entries"] == []

    def test_audit_after_calculation(self, client):
        """Test audit log contains entry after calculation."""
        # Do a calculation first
        calc_response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 5000,
                "currency": "KES",
                "country_code": "KE",
                "payment_method": "mobile_money",
            },
        )
        txn_id = calc_response.json()["transaction_id"]

        # Query audit
        response = client.get("/api/v1/audit")
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["transaction_id"] == txn_id

    def test_audit_get_by_id(self, client):
        """Test getting specific audit entry by ID."""
        calc_response = client.post(
            "/api/v1/calculate",
            json={
                "amount": 5000,
                "currency": "KES",
                "country_code": "KE",
                "payment_method": "card",
            },
        )
        txn_id = calc_response.json()["transaction_id"]

        response = client.get(f"/api/v1/audit/{txn_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == txn_id

    def test_audit_get_by_id_not_found(self, client):
        """Test 404 for nonexistent audit entry."""
        response = client.get("/api/v1/audit/txn_nonexistent")
        assert response.status_code == 404

    def test_audit_filter_by_country(self, client):
        """Test filtering audit log by country code."""
        # Do calculations for different countries
        client.post(
            "/api/v1/calculate",
            json={"amount": 5000, "currency": "KES", "country_code": "KE", "payment_method": "card"},
        )
        client.post(
            "/api/v1/calculate",
            json={"amount": 500, "currency": "GHS", "country_code": "GH", "payment_method": "card"},
        )

        response = client.get("/api/v1/audit?country_code=KE")
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["country_code"] == "KE"

    def test_audit_filter_by_transaction_id_query(self, client):
        """Test filtering audit by transaction_id query param."""
        calc_response = client.post(
            "/api/v1/calculate",
            json={"amount": 5000, "currency": "KES", "country_code": "KE", "payment_method": "card"},
        )
        txn_id = calc_response.json()["transaction_id"]

        response = client.get(f"/api/v1/audit?transaction_id={txn_id}")
        data = response.json()
        assert data["total"] == 1


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_ok(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["config_loaded"] is True
        assert set(data["countries_available"]) == {"KE", "NG", "GH", "ZA"}

    def test_health_has_timestamp(self, client):
        """Test health check includes timestamp."""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
