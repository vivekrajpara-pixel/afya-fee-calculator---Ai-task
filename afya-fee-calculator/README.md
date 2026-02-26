# Afya Health Cross-Border Fee Calculator

A production-grade backend service that calculates payment processing fees across 4 African countries (Kenya, Nigeria, Ghana, South Africa) with multiple payment methods, tiered pricing, cascading taxes, currency conversion, and full audit logging. Built with Python/FastAPI using `Decimal` for precise monetary calculations.

---

## Architecture

```
afya-fee-calculator/
├── main.py                    # FastAPI app entry point, uvicorn launcher
├── requirements.txt           # Python dependencies
├── config/
│   └── fee_rules.json         # All fee configuration (countries, methods, taxes, FX)
├── app/
│   ├── models.py              # Pydantic v2 request/response models with validation
│   ├── config_loader.py       # Singleton config loader with validation
│   ├── fee_engine.py          # Pure-function calculation engine (Decimal math)
│   ├── audit_store.py         # In-memory audit log with query support
│   └── routes.py              # Thin API routing layer (delegates to engine)
├── tests/
│   ├── test_fee_engine.py     # 36 unit tests for calculation logic
│   ├── test_api.py            # 22 integration tests for all endpoints
│   └── test_config.py         # 17 config loading/validation tests
└── scripts/
    └── demo.py                # Runnable demo showing 10 scenarios
```

```
┌──────────────┐     ┌────────────┐     ┌──────────────┐
│  HTTP Client │────>│  routes.py │────>│  fee_engine  │
│  (curl/app)  │<────│  (FastAPI)  │<────│  (pure math) │
└──────────────┘     └─────┬──────┘     └──────┬───────┘
                           │                    │
                     ┌─────▼──────┐     ┌──────▼───────┐
                     │ audit_store│     │config_loader │
                     │ (in-memory)│     │ (singleton)  │
                     └────────────┘     └──────┬───────┘
                                               │
                                        ┌──────▼───────┐
                                        │fee_rules.json│
                                        └──────────────┘
```

---

## Quick Start

### Install and Run (3 commands)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Server starts at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### Run Tests

```bash
python -m pytest tests/ -v
```

Expected output: `75 passed` — 36 engine tests, 22 API tests, 17 config tests.

### Run Demo Script

```bash
python scripts/demo.py
```

Displays 10 formatted scenarios with full breakdowns covering all countries, payment methods, tiers, and edge cases.

---

## API Reference

### `POST /api/v1/calculate` — Calculate Fees

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "currency": "KES",
    "country_code": "KE",
    "payment_method": "mobile_money"
  }'
```

**Response:**
```json
{
  "transaction_id": "txn_abc123def456",
  "timestamp": "2026-02-26T10:30:00Z",
  "input": {
    "amount": 5000.0,
    "currency": "KES",
    "country_code": "KE",
    "payment_method": "mobile_money"
  },
  "customer_pays": { "amount": 5000.0, "currency": "KES" },
  "merchant_receives": { "amount": 30.85, "currency": "USD" },
  "total_fees": { "amount": 156.60, "currency": "KES" },
  "fee_bearer": "merchant",
  "breakdown": [
    { "label": "Processor Fee", "description": "1.5% fee on 5000 KES", "amount": 75.0, "currency": "KES" },
    { "label": "Payment Method Fee", "description": "1.0% + 10.0 fee on 5000 KES", "amount": 60.0, "currency": "KES" },
    { "label": "VAT on Fees", "description": "16.0% on processor_fee + payment_method_fee", "amount": 21.60, "currency": "KES" },
    { "label": "FX Conversion", "description": "KES->USD at 0.006370 (mid: 0.0065, spread: 2.0%)", "amount": 0.65, "currency": "KES" }
  ],
  "currency_conversion": {
    "from_currency": "KES",
    "to_currency": "USD",
    "mid_market_rate": 0.0065,
    "spread_percent": 2.0,
    "effective_rate": 0.006370,
    "original_amount": 5000.0,
    "converted_amount": 30.85,
    "spread_cost_in_original_currency": 0.65
  }
}
```

### `POST /api/v1/compare` — Compare Payment Methods

```bash
curl -X POST http://localhost:8000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "currency": "KES",
    "country_code": "KE"
  }'
```

Returns all payment methods for a country, ranked by customer cost (cheapest first).

### `GET /api/v1/audit` — Query Audit Log

```bash
# All entries
curl http://localhost:8000/api/v1/audit

# Filter by country
curl "http://localhost:8000/api/v1/audit?country_code=KE"

# Filter by payment method
curl "http://localhost:8000/api/v1/audit?payment_method=card"

# Pagination
curl "http://localhost:8000/api/v1/audit?limit=10&offset=0"
```

### `GET /api/v1/audit/{transaction_id}` — Get Specific Entry

```bash
curl http://localhost:8000/api/v1/audit/txn_abc123def456
```

### `GET /health` — Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "config_loaded": true,
  "countries_available": ["KE", "NG", "GH", "ZA"],
  "timestamp": "2026-02-26T10:30:00Z"
}
```

### Error Responses

Invalid input returns HTTP 400 with structured error (never 500):

```json
{
  "error": "unsupported_country",
  "detail": "Country 'FR' is not supported. Available countries: ['KE', 'NG', 'GH', 'ZA']"
}
```

---

## Example Scenarios

### Scenario 1: Kenya Mobile Money — Merchant Absorbs Fees + FX

- **Input:** 5,000 KES via mobile_money in Kenya
- **Processor Fee:** 1.5% × 5,000 = 75.00 KES
- **Payment Method Fee:** 1.0% × 5,000 + 10 = 60.00 KES
- **VAT:** 16% × (75 + 60) = 21.60 KES
- **Total Fees:** 156.60 KES (merchant absorbs)
- **Customer Pays:** 5,000.00 KES
- **FX:** KES→USD at 0.006370 (mid 0.0065, 2% spread)
- **Merchant Receives:** (5,000 - 156.60) × 0.006370 = **30.85 USD**

### Scenario 2: Nigeria Mobile Money — Tiered Pricing Comparison

**Below threshold (8,000 NGN ≤ 10,000):**
- Payment Method Fee: 3.2% × 8,000 + 50 = 306.00 NGN
- Total Fees: 487.68 NGN

**Above threshold (25,000 NGN > 10,000):**
- Payment Method Fee: 2.5% × 25,000 + 50 = 675.00 NGN (lower rate kicks in)
- Total Fees: 1,185.63 NGN

### Scenario 3: South Africa Card — 3-Tier Pricing

| Amount | Tier | Rate | Processor Fee | Total Fees |
|--------|------|------|---------------|------------|
| 500 ZAR | ≤1,000 | 3.5% + 5 | 22.50 ZAR | 22.50 ZAR |
| 5,000 ZAR | 1K–10K | 2.8% + 5 | 145.00 ZAR | 145.00 ZAR |
| 15,000 ZAR | >10K | 2.2% + 5 | 335.00 ZAR | 335.00 ZAR |

### Scenario 4: Ghana Card — No FX Conversion

- **Input:** 500 GHS via card in Ghana
- Settlement is GHS (no FX conversion needed)
- Tax: 15% combined tax on all fees
- **Customer Pays:** 519.55 GHS
- **Merchant Receives:** 500.00 GHS

---

## Design Decisions

### Why `Decimal` for All Money Math

Floating-point arithmetic causes rounding errors in financial calculations (e.g., `0.1 + 0.2 = 0.30000000000000004`). Using Python's `Decimal` with explicit `ROUND_HALF_UP` quantization ensures cent-accurate calculations across all currencies. Every line item is rounded individually, then summed.

### Why JSON Configuration

Fee rules change frequently (new processor contracts, tax law changes). `fee_rules.json` is:
- **Human-readable**: Includes descriptions and comments for non-engineers
- **Externalized**: No code changes needed to update fees, add countries, or change tax rates
- **Validated on load**: The config loader validates structure at startup, failing fast on errors

### Fee Engine Architecture

`fee_engine.py` is a **pure function module** — it takes config + input, returns a result, with no side effects. This makes it:
- Easy to test (no mocking needed)
- Thread-safe (no shared state)
- Deterministic (same input always produces same output)

### How to Add a New Country

**Only edit `config/fee_rules.json`** — no code changes required:

1. Add a new entry under `"countries"` (e.g., `"TZ"` for Tanzania)
2. Define `currency`, `settlement_currency`, `tax`, and `payment_methods`
3. If settlement currency differs, add an FX pair under `"fx_rates"` (e.g., `"TZS_USD"`)
4. Restart the server — the new country is automatically available

---

## How to Modify Fee Rules (For Non-Engineers)

Open `config/fee_rules.json` in any text editor.

**To update a fee rate:**
Find the country → payment method → fee component and change the number:
```json
"processor_fee": {
  "type": "percentage_plus_fixed",
  "percentage": 2.9,    // Change this to update the percentage
  "fixed": 10.00        // Change this to update the fixed fee
}
```

**To change a tax rate:**
```json
"tax": {
  "rate_percent": 16.0,  // Change this number
  "applies_to": ["processor_fee", "payment_method_fee"]  // Controls which fees get taxed
}
```

**To update an FX rate:**
```json
"KES_USD": {
  "mid_market_rate": 0.0065,  // Update with current market rate
  "spread_percent": 2.0       // Update spread if contract changes
}
```

---

## Trade-Offs

| Decision | Trade-off |
|----------|-----------|
| **In-memory audit store** | Simple and fast, but data is lost on restart. Production would use a database. |
| **Single JSON config file** | Easy to edit but no versioning or rollback. Production might use a database or config service. |
| **Singleton config loader** | Loads once for performance, but requires restart to pick up changes. Could add a reload endpoint. |
| **6-decimal FX rate precision** | Sufficient for major currency pairs; some exotic pairs may need more precision. |
| **Synchronous API** | Simpler code, adequate for calculation-only service. Would need async for external API calls. |
| **No authentication** | Simplified for demo. Production would add API key/OAuth middleware. |

---

## Supported Countries & Payment Methods

| Country | Currency | Settlement | Tax | Payment Methods |
|---------|----------|-----------|-----|-----------------|
| Kenya (KE) | KES | USD | 16% VAT on all fees | mobile_money, card, bank_transfer |
| Nigeria (NG) | NGN | USD | 7.5% VAT on processor only | mobile_money (tiered), card, bank_transfer |
| Ghana (GH) | GHS | GHS | 15% combined tax on all fees | mobile_money, card, bank_transfer |
| South Africa (ZA) | ZAR | USD | 0% (no tax on fees) | mobile_money, card (3-tier), bank_transfer |
