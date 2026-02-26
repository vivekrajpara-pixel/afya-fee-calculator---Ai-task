# MASTER PROMPT: Build Afya Health Cross-Border Fee Calculator (Target: 100/100)

## ROLE & CONTEXT
You are a senior backend engineer. Build a **complete, production-grade, fully tested** backend service for Afya Health's cross-border payment fee calculator. Every file must be created, every test must pass, every edge case must be handled. Do NOT stop until the entire project is built, tested, and verified working.

## WHAT TO BUILD
A Python/FastAPI REST API service that calculates payment processing fees across 4 African countries (Kenya, Nigeria, Ghana, South Africa) with multiple payment methods, tiered pricing, cascading taxes, currency conversion, and full audit logging.

## CRITICAL SCORING REQUIREMENTS (100 points total)

### 1. FEE CALCULATION ACCURACY (25 pts) — MOST IMPORTANT
Build a calculation engine using Python `Decimal` for ALL money math (never float). Must handle:
- **Percentage + fixed fees**: e.g., 2.9% + 10 KES
- **Fixed-only fees**: e.g., flat 50 KES per bank transfer
- **Tiered/threshold pricing**: e.g., Nigeria mobile money: 3.2%+50 NGN for ≤10,000 NGN, 2.5%+50 NGN for >10,000 NGN. South Africa cards: 3.5% ≤1K ZAR, 2.8% 1K-10K, 2.2% >10K
- **Cascading taxes**: Kenya: 16% VAT applied ON TOP of processor+payment_method fees. Nigeria: 7.5% VAT on processor fees ONLY. Ghana: 15% on both. South Africa: 0% tax on fees
- **Currency conversion**: KES→USD, NGN→USD, ZAR→USD with configurable FX spread (2-3%) on mid-market rate. GHS settles in GHS (no conversion)
- **Rounding**: All monetary values rounded to 2 decimal places using ROUND_HALF_UP
- **Fee bearer logic**: Some methods pass fees to customer, others merchant absorbs
- **Edge cases**: Very small amounts (where fixed fee > percentage fee), very large amounts (tiered pricing kicks in), amounts at exact tier boundaries

### 2. CONFIGURATION-DRIVEN DESIGN (20 pts)
- ALL fee rules in a single `config/fee_rules.json` file — NO hardcoded if/else for countries/methods
- JSON must be human-readable with comments/descriptions so non-engineers can edit it
- Structure: countries → payment_methods → processor_fee + payment_method_fee + tax rules + FX rates
- Fee types supported in config: `"percentage_plus_fixed"`, `"fixed"`, `"tiered"`, `"none"`
- Tax config specifies `"applies_to"` list: which fee components get taxed
- FX config: mid-market rate + spread percentage per currency pair
- The engine code reads config generically — adding a 5th country means ONLY editing JSON

### 3. CODE QUALITY & ARCHITECTURE (20 pts)
Create these files with clean separation:
```
afya-fee-calculator/
├── main.py                    # FastAPI app entry, uvicorn launcher
├── requirements.txt           # fastapi, uvicorn, pydantic, pytest, httpx
├── config/
│   └── fee_rules.json         # All fee configuration data
├── app/
│   ├── __init__.py
│   ├── models.py              # Pydantic request/response models with validation
│   ├── config_loader.py       # Loads & validates JSON config, singleton pattern
│   ├── fee_engine.py          # Core calculation logic (Decimal math, no hardcoding)
│   ├── audit_store.py         # In-memory audit log with query support
│   └── routes.py              # API endpoints (calculate, compare, audit, health)
├── tests/
│   ├── __init__.py
│   ├── test_fee_engine.py     # Unit tests for calculation logic (15+ tests)
│   ├── test_api.py            # Integration tests for all endpoints (10+ tests)
│   └── test_config.py         # Config loading/validation tests
├── scripts/
│   └── demo.py                # Runnable demo script showing 8+ scenarios with output
└── README.md                  # Complete documentation
```

Architecture principles:
- `fee_engine.py` is a pure function module — takes config + transaction input, returns breakdown. No side effects.
- `config_loader.py` uses singleton pattern — loads once, reusable
- `routes.py` is thin — delegates to engine, handles HTTP concerns only
- `models.py` uses Pydantic v2 with field validators for input sanitization
- Proper error handling: custom exceptions, HTTP 400/404/422 with structured error bodies
- Type hints everywhere

### 4. TEST DATA & SCENARIOS (15 pts)
The `fee_rules.json` must include realistic data for:

**4 Countries with DIFFERENT fee structures:**
- **Kenya (KE)**: KES currency, settles in USD, 16% VAT on processor+payment_method fees
- **Nigeria (NG)**: NGN currency, settles in USD, 7.5% VAT on processor fees only, tiered mobile money pricing
- **Ghana (GH)**: GHS currency, settles in GHS (no FX conversion), 15% combined tax on all fees
- **South Africa (ZA)**: ZAR currency, settles in USD, 0% tax on fees, tiered card pricing

**3 Payment methods per country:** mobile_money, card, bank_transfer

**Fee rules covering:**
- Tiered: Nigeria mobile_money (≤10K vs >10K NGN), South Africa card (3 tiers)
- Percentage+fixed: Kenya card (2.9% + 10 KES), Nigeria card (3.5% + 100 NGN)  
- Fixed only: All bank_transfers (flat fee)
- No fee: payment_method_fee = "none" for bank transfers

**FX rates in config:**
- KES_USD: rate 0.0065, spread 2.0%
- NGN_USD: rate 0.00062, spread 3.0%
- ZAR_USD: rate 0.053, spread 2.5%
- GHS_GHS: rate 1.0, spread 0% (same currency)
- Include self-pairs (KES_KES etc.) with 0% spread

**Demo script must show 8+ scenarios:**
1. Kenya mobile_money 5000 KES (small, merchant-absorbs, VAT, FX conversion)
2. Kenya card 5000 KES (customer-pays, VAT, FX)
3. Kenya bank_transfer 5000 KES (fixed fee, merchant-absorbs, VAT, FX)
4. Nigeria mobile_money 8000 NGN (below tier threshold)
5. Nigeria mobile_money 25000 NGN (above tier threshold — lower rate kicks in)
6. Ghana card 500 GHS (small amount, no FX conversion, 15% tax)
7. South Africa card 500 ZAR (small — hits highest tier rate 3.5%)
8. South Africa card 15000 ZAR (large — hits lowest tier rate 2.2%)
9. Fee comparison endpoint for Kenya 5000 KES (all 3 methods ranked)
10. Error case: unsupported country

### 5. API/INTERFACE DESIGN (10 pts)
**Endpoints:**
- `POST /api/v1/calculate` — Main fee calculation
- `POST /api/v1/compare` — Fee comparison across payment methods
- `GET /api/v1/audit` — Query audit log (by transaction_id, country_code, date range)
- `GET /api/v1/audit/{transaction_id}` — Get specific audit entry
- `GET /health` — Health check with config status

**Request model (POST /calculate):**
```json
{
  "amount": 5000.00,
  "currency": "KES",
  "country_code": "KE",
  "payment_method": "mobile_money"
}
```

**Response model (detailed breakdown):**
```json
{
  "transaction_id": "txn_abc123",
  "timestamp": "2026-02-26T10:30:00Z",
  "input": { "amount": 5000.00, "currency": "KES", "country_code": "KE", "payment_method": "mobile_money" },
  "customer_pays": { "amount": 5000.00, "currency": "KES" },
  "merchant_receives": { "amount": 30.42, "currency": "USD" },
  "total_fees": { "amount": 131.60, "currency": "KES" },
  "fee_bearer": "merchant",
  "breakdown": [
    { "label": "Processor Fee", "description": "1.5% of 5,000.00 KES", "amount": 75.00, "currency": "KES" },
    { "label": "Payment Method Fee", "description": "1.0% + 10.00 KES (tier: ≤5,000 KES)", "amount": 60.00, "currency": "KES" },
    { "label": "VAT on Fees", "description": "16.0% on processor_fee + payment_method_fee", "amount": 21.60, "currency": "KES" },
    { "label": "FX Conversion", "description": "KES→USD at 0.006370 (mid: 0.006500, spread: 2.0%)", "amount": "...", "currency": "KES" }
  ],
  "currency_conversion": {
    "from_currency": "KES",
    "to_currency": "USD",
    "mid_market_rate": 0.006500,
    "spread_percent": 2.0,
    "effective_rate": 0.006370,
    "original_amount": 5000.00,
    "converted_amount": 31.85,
    "spread_cost_in_original_currency": 0.65
  }
}
```

**Error responses:** Return HTTP 400/404 with `{"error": "...", "detail": "..."}` — never 500 for bad input.

### 6. DOCUMENTATION (10 pts)
README.md must include:
- Project title and one-paragraph description
- Architecture diagram (text-based)
- How to install and run (3 commands max)
- How to run tests (with expected output)
- How to run the demo script
- API endpoint reference with curl examples for all endpoints
- 3+ detailed example scenarios with full request/response
- Design decisions section explaining: why Decimal, why JSON config, fee engine architecture, how to add a new country
- Trade-offs section
- How to modify fee rules (guide for non-engineers)

## EXECUTION INSTRUCTIONS

1. **Create ALL files** listed in the architecture above. Every single one.
2. **Install dependencies** and verify imports work.
3. **Run ALL tests** — fix any failures until 100% pass.
4. **Run the demo script** — verify output is correct and well-formatted.
5. **Start the server** and test at least 3 curl requests manually.
6. **Verify edge cases**: small amounts, large amounts, tier boundaries, missing fields, bad country codes.
7. **Copy final project to /mnt/user-data/outputs/** so user can download.

## KEY IMPLEMENTATION DETAILS

### Fee Calculation Algorithm (fee_engine.py)
```
1. Look up country config from fee_rules.json
2. Look up payment method config within that country
3. Calculate processor_fee:
   - If type="percentage_plus_fixed": amount * percentage/100 + fixed
   - If type="fixed": just the fixed amount
   - If type="tiered": find matching tier by amount, then percentage + fixed
   - If type="none": 0
4. Calculate payment_method_fee (same logic as above)
5. Calculate tax:
   - sum = 0
   - For each fee_component in tax.applies_to:
     - sum += calculated value of that component
   - tax_amount = sum * tax.rate_percent / 100
6. Calculate total_fees = processor_fee + payment_method_fee + tax_amount
7. If settlement_currency != transaction_currency:
   - Look up FX pair
   - effective_rate = mid_rate * (1 - spread/100)  [for selling local currency]
   - fx_spread_cost = amount * spread/100 * mid_rate (in settlement currency terms)
   - converted_amount = (amount - fees_if_merchant_bears) * effective_rate
8. Determine customer_pays and merchant_receives based on fee_bearer
```

### FX Conversion Logic
- The spread REDUCES the effective rate when converting from local to USD (merchant gets less USD per local unit)
- `effective_rate = mid_market_rate * (1 - spread_percent / 100)`
- The FX spread cost should appear as a line item in the breakdown
- `spread_cost_in_settlement = amount_in_original * mid_rate - amount_in_original * effective_rate`

### Fee Bearer Logic
- If `fee_bearer = "merchant"`: customer_pays = transaction_amount (no extra charge), merchant_receives = amount - all_fees (converted to settlement currency)
- If `fee_bearer = "customer"`: customer_pays = transaction_amount + fees_passed_to_customer, merchant_receives = transaction_amount (converted, minus FX spread)

### Rounding Rules
- Use `Decimal` with `quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)` for all final amounts
- Round each line item individually, then sum (not the other way around)

## FINAL CHECKLIST BEFORE DELIVERY
- [ ] `pip install -r requirements.txt` works
- [ ] `pytest tests/ -v` — ALL tests pass (25+ tests)
- [ ] `python scripts/demo.py` — Shows 8+ scenarios with correct math
- [ ] `python main.py` starts server on port 8000
- [ ] `curl POST /api/v1/calculate` returns correct breakdown
- [ ] `curl POST /api/v1/compare` returns ranked payment methods
- [ ] `curl GET /api/v1/audit` returns logged calculations
- [ ] `curl GET /health` returns OK
- [ ] Invalid input returns 400 with error message, not 500
- [ ] README.md is complete and professional
- [ ] All files copied to /mnt/user-data/outputs/afya-fee-calculator/

**BUILD EVERYTHING NOW. Do not ask questions. Do not stop until fully tested and working.**