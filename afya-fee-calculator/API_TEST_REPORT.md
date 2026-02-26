# Afya Health Fee Calculator - Live API Test Report

**Date:** 2026-02-26
**Server:** `uvicorn main:app --host 0.0.0.0 --port 8000`
**Method:** All tests performed by starting the server and hitting endpoints with `curl`.

---

## Unit & Integration Tests (pytest)

```
$ python -m pytest tests/ -v

tests/test_api.py::TestCalculateEndpoint::test_calculate_ke_mobile_money PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_ng_card PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_gh_no_fx PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_za_tiered_card PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_has_breakdown PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_unsupported_country PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_unsupported_payment_method PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_currency_mismatch PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_negative_amount PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_zero_amount PASSED
tests/test_api.py::TestCalculateEndpoint::test_calculate_missing_fields PASSED
tests/test_api.py::TestCompareEndpoint::test_compare_ke_all_methods PASSED
tests/test_api.py::TestCompareEndpoint::test_compare_unsupported_country PASSED
tests/test_api.py::TestCompareEndpoint::test_compare_has_all_fields PASSED
tests/test_api.py::TestAuditEndpoint::test_audit_empty PASSED
tests/test_api.py::TestAuditEndpoint::test_audit_after_calculation PASSED
tests/test_api.py::TestAuditEndpoint::test_audit_get_by_id PASSED
tests/test_api.py::TestAuditEndpoint::test_audit_get_by_id_not_found PASSED
tests/test_api.py::TestAuditEndpoint::test_audit_filter_by_country PASSED
tests/test_api.py::TestAuditEndpoint::test_audit_filter_by_transaction_id_query PASSED
tests/test_api.py::TestHealthEndpoint::test_health_ok PASSED
tests/test_api.py::TestHealthEndpoint::test_health_has_timestamp PASSED
tests/test_config.py::TestConfigLoading::test_load_default_config PASSED
tests/test_config.py::TestConfigLoading::test_singleton_pattern PASSED
tests/test_config.py::TestConfigLoading::test_load_nonexistent_file PASSED
tests/test_config.py::TestConfigLoading::test_get_available_countries PASSED
tests/test_config.py::TestConfigLoading::test_get_country_valid PASSED
tests/test_config.py::TestConfigLoading::test_get_country_invalid PASSED
tests/test_config.py::TestConfigLoading::test_get_payment_method_valid PASSED
tests/test_config.py::TestConfigLoading::test_get_payment_method_invalid PASSED
tests/test_config.py::TestConfigLoading::test_get_fx_rate_valid PASSED
tests/test_config.py::TestConfigLoading::test_get_fx_rate_invalid PASSED
tests/test_config.py::TestConfigLoading::test_country_case_insensitive PASSED
tests/test_config.py::TestConfigLoading::test_payment_methods_for_country PASSED
tests/test_config.py::TestConfigValidation::test_missing_countries_key PASSED
tests/test_config.py::TestConfigValidation::test_missing_fx_rates_key PASSED
tests/test_config.py::TestConfigValidation::test_missing_country_currency PASSED
tests/test_config.py::TestConfigValidation::test_unknown_fee_type PASSED
tests/test_config.py::TestConfigValidation::test_valid_minimal_config PASSED
tests/test_fee_engine.py::TestRounding::test_round_half_up PASSED
tests/test_fee_engine.py::TestRounding::test_round_half_up_exact PASSED
tests/test_fee_engine.py::TestRounding::test_round_down PASSED
tests/test_fee_engine.py::TestRounding::test_round_already_two_places PASSED
tests/test_fee_engine.py::TestSingleFeeCalculation::test_percentage_plus_fixed PASSED
tests/test_fee_engine.py::TestSingleFeeCalculation::test_fixed_only PASSED
tests/test_fee_engine.py::TestSingleFeeCalculation::test_none_fee PASSED
tests/test_fee_engine.py::TestSingleFeeCalculation::test_tiered_below_threshold PASSED
tests/test_fee_engine.py::TestSingleFeeCalculation::test_tiered_above_threshold PASSED
tests/test_fee_engine.py::TestSingleFeeCalculation::test_tiered_at_exact_boundary PASSED
tests/test_fee_engine.py::TestSingleFeeCalculation::test_three_tier_pricing PASSED
tests/test_fee_engine.py::TestKenyaFees::test_ke_mobile_money_5000 PASSED
tests/test_fee_engine.py::TestKenyaFees::test_ke_card_5000 PASSED
tests/test_fee_engine.py::TestKenyaFees::test_ke_bank_transfer_5000 PASSED
tests/test_fee_engine.py::TestNigeriaFees::test_ng_mobile_money_below_tier PASSED
tests/test_fee_engine.py::TestNigeriaFees::test_ng_mobile_money_above_tier PASSED
tests/test_fee_engine.py::TestNigeriaFees::test_ng_card_customer_pays PASSED
tests/test_fee_engine.py::TestNigeriaFees::test_ng_bank_transfer_fixed PASSED
tests/test_fee_engine.py::TestGhanaFees::test_gh_card_500 PASSED
tests/test_fee_engine.py::TestGhanaFees::test_gh_mobile_money_merchant_absorbs PASSED
tests/test_fee_engine.py::TestGhanaFees::test_gh_no_fx_conversion PASSED
tests/test_fee_engine.py::TestSouthAfricaFees::test_za_card_small_500 PASSED
tests/test_fee_engine.py::TestSouthAfricaFees::test_za_card_large_15000 PASSED
tests/test_fee_engine.py::TestSouthAfricaFees::test_za_card_mid_tier PASSED
tests/test_fee_engine.py::TestSouthAfricaFees::test_za_no_tax_on_fees PASSED
tests/test_fee_engine.py::TestSouthAfricaFees::test_za_bank_transfer_fixed PASSED
tests/test_fee_engine.py::TestFXConversion::test_kes_to_usd_spread PASSED
tests/test_fee_engine.py::TestFXConversion::test_ngn_to_usd_spread PASSED
tests/test_fee_engine.py::TestFXConversion::test_ghs_no_conversion PASSED
tests/test_fee_engine.py::TestEdgeCases::test_very_small_amount PASSED
tests/test_fee_engine.py::TestEdgeCases::test_very_large_amount PASSED
tests/test_fee_engine.py::TestEdgeCases::test_amount_at_exact_tier_boundary_10000_ngn PASSED
tests/test_fee_engine.py::TestEdgeCases::test_amount_just_above_tier_boundary PASSED
tests/test_fee_engine.py::TestEdgeCases::test_breakdown_contains_expected_items PASSED
tests/test_fee_engine.py::TestEdgeCases::test_transaction_id_generated PASSED
tests/test_fee_engine.py::TestEdgeCases::test_timestamp_is_set PASSED

============================== 75 passed in 0.33s ==============================
```

**Result: 75/75 tests passed** (36 engine + 22 API + 17 config)

---

## Live API Tests

### 1. GET /health - Health Check

```bash
curl -s http://localhost:8000/health
```

**Response (200 OK):**
```json
{
    "status": "healthy",
    "config_loaded": true,
    "countries_available": [
        "KE",
        "NG",
        "GH",
        "ZA"
    ],
    "timestamp": "2026-02-26T07:28:58.796844Z"
}
```

**Verified:** Status is healthy, all 4 countries loaded, timestamp present.

---

### 2. POST /api/v1/calculate - Kenya Mobile Money 5,000 KES

Scenario: Merchant-absorbs fees, 16% VAT on both fee components, FX conversion KES to USD.

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "currency": "KES", "country_code": "KE", "payment_method": "mobile_money"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_1c08092d3f47",
    "timestamp": "2026-02-26T07:28:59.971961Z",
    "input": {
        "amount": 5000.0,
        "currency": "KES",
        "country_code": "KE",
        "payment_method": "mobile_money"
    },
    "customer_pays": {
        "amount": 5000.0,
        "currency": "KES"
    },
    "merchant_receives": {
        "amount": 30.85,
        "currency": "USD"
    },
    "total_fees": {
        "amount": 156.6,
        "currency": "KES"
    },
    "fee_bearer": "merchant",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "1.5% fee on 5000 KES",
            "amount": 75.0,
            "currency": "KES"
        },
        {
            "label": "Payment Method Fee",
            "description": "1.0% + 10.0 fee on 5000 KES",
            "amount": 60.0,
            "currency": "KES"
        },
        {
            "label": "VAT on Fees",
            "description": "16.0% on processor_fee + payment_method_fee",
            "amount": 21.6,
            "currency": "KES"
        },
        {
            "label": "FX Conversion",
            "description": "KES->USD at 0.006370 (mid: 0.0065, spread: 2.0%)",
            "amount": 0.65,
            "currency": "KES"
        }
    ],
    "currency_conversion": {
        "from_currency": "KES",
        "to_currency": "USD",
        "mid_market_rate": 0.0065,
        "spread_percent": 2.0,
        "effective_rate": 0.00637,
        "original_amount": 5000.0,
        "converted_amount": 30.85,
        "spread_cost_in_original_currency": 0.65
    }
}
```

**Math verification:**
- Processor Fee: 1.5% x 5000 = 75.00
- Payment Method Fee: 1.0% x 5000 + 10 = 60.00
- VAT: 16% x (75 + 60) = 21.60
- Total Fees: 75 + 60 + 21.60 = 156.60
- FX effective rate: 0.0065 x (1 - 0.02) = 0.006370
- Merchant receives: (5000 - 156.60) x 0.006370 = 30.85 USD
- Customer pays: 5000.00 KES (merchant absorbs fees)
- All amounts are JSON numbers (not strings)

---

### 3. POST /api/v1/calculate - Kenya Card 5,000 KES

Scenario: Customer-pays fees, 16% VAT, FX conversion.

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "currency": "KES", "country_code": "KE", "payment_method": "card"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_611571f30817",
    "timestamp": "2026-02-26T07:29:00.910136Z",
    "input": {
        "amount": 5000.0,
        "currency": "KES",
        "country_code": "KE",
        "payment_method": "card"
    },
    "customer_pays": {
        "amount": 5179.8,
        "currency": "KES"
    },
    "merchant_receives": {
        "amount": 31.85,
        "currency": "USD"
    },
    "total_fees": {
        "amount": 179.8,
        "currency": "KES"
    },
    "fee_bearer": "customer",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "2.9% + 10.0 fee on 5000 KES",
            "amount": 155.0,
            "currency": "KES"
        },
        {
            "label": "VAT on Fees",
            "description": "16.0% on processor_fee + payment_method_fee",
            "amount": 24.8,
            "currency": "KES"
        },
        {
            "label": "FX Conversion",
            "description": "KES->USD at 0.006370 (mid: 0.0065, spread: 2.0%)",
            "amount": 0.65,
            "currency": "KES"
        }
    ],
    "currency_conversion": {
        "from_currency": "KES",
        "to_currency": "USD",
        "mid_market_rate": 0.0065,
        "spread_percent": 2.0,
        "effective_rate": 0.00637,
        "original_amount": 5000.0,
        "converted_amount": 31.85,
        "spread_cost_in_original_currency": 0.65
    }
}
```

**Math verification:**
- Processor Fee: 2.9% x 5000 + 10 = 155.00
- Payment Method Fee: none = 0
- VAT: 16% x (155 + 0) = 24.80
- Total Fees: 155 + 0 + 24.80 = 179.80
- Customer pays: 5000 + 179.80 = 5179.80 (customer bears fees)
- Merchant receives: 5000 x 0.006370 = 31.85 USD

---

### 4. POST /api/v1/calculate - Kenya Bank Transfer 5,000 KES

Scenario: Fixed fee, merchant-absorbs, VAT, FX conversion.

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "currency": "KES", "country_code": "KE", "payment_method": "bank_transfer"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_1526596ec451",
    "timestamp": "2026-02-26T07:29:01.971480Z",
    "input": {
        "amount": 5000.0,
        "currency": "KES",
        "country_code": "KE",
        "payment_method": "bank_transfer"
    },
    "customer_pays": {
        "amount": 5000.0,
        "currency": "KES"
    },
    "merchant_receives": {
        "amount": 31.48,
        "currency": "USD"
    },
    "total_fees": {
        "amount": 58.0,
        "currency": "KES"
    },
    "fee_bearer": "merchant",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "Flat 50.0 fee on 5000 KES",
            "amount": 50.0,
            "currency": "KES"
        },
        {
            "label": "VAT on Fees",
            "description": "16.0% on processor_fee + payment_method_fee",
            "amount": 8.0,
            "currency": "KES"
        },
        {
            "label": "FX Conversion",
            "description": "KES->USD at 0.006370 (mid: 0.0065, spread: 2.0%)",
            "amount": 0.65,
            "currency": "KES"
        }
    ],
    "currency_conversion": {
        "from_currency": "KES",
        "to_currency": "USD",
        "mid_market_rate": 0.0065,
        "spread_percent": 2.0,
        "effective_rate": 0.00637,
        "original_amount": 5000.0,
        "converted_amount": 31.48,
        "spread_cost_in_original_currency": 0.65
    }
}
```

**Math verification:**
- Processor Fee: flat 50.00 KES
- Payment Method Fee: none = 0
- VAT: 16% x 50 = 8.00
- Total Fees: 50 + 0 + 8 = 58.00
- Merchant receives: (5000 - 58) x 0.006370 = 31.48 USD

---

### 5. POST /api/v1/calculate - Nigeria Mobile Money 8,000 NGN (Below Tier)

Scenario: Tiered pricing, amount below 10,000 NGN threshold, 7.5% VAT on processor fee only.

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 8000, "currency": "NGN", "country_code": "NG", "payment_method": "mobile_money"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_1d8187126989",
    "timestamp": "2026-02-26T07:29:03.156815Z",
    "input": {
        "amount": 8000.0,
        "currency": "NGN",
        "country_code": "NG",
        "payment_method": "mobile_money"
    },
    "customer_pays": {
        "amount": 8000.0,
        "currency": "NGN"
    },
    "merchant_receives": {
        "amount": 4.51,
        "currency": "USD"
    },
    "total_fees": {
        "amount": 487.68,
        "currency": "NGN"
    },
    "fee_bearer": "merchant",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "1.8% + 25.0 fee on 8000 NGN",
            "amount": 169.0,
            "currency": "NGN"
        },
        {
            "label": "Payment Method Fee",
            "description": "3.2% + 50.0 (tier: <=10000.0) on 8000 NGN",
            "amount": 306.0,
            "currency": "NGN"
        },
        {
            "label": "VAT on Fees",
            "description": "7.5% on processor_fee",
            "amount": 12.68,
            "currency": "NGN"
        },
        {
            "label": "FX Conversion",
            "description": "NGN->USD at 0.000601 (mid: 0.00062, spread: 3.0%)",
            "amount": 0.15,
            "currency": "NGN"
        }
    ],
    "currency_conversion": {
        "from_currency": "NGN",
        "to_currency": "USD",
        "mid_market_rate": 0.00062,
        "spread_percent": 3.0,
        "effective_rate": 0.000601,
        "original_amount": 8000.0,
        "converted_amount": 4.51,
        "spread_cost_in_original_currency": 0.15
    }
}
```

**Math verification:**
- Processor Fee: 1.8% x 8000 + 25 = 169.00
- Payment Method Fee (tier <=10K): 3.2% x 8000 + 50 = 306.00
- VAT: 7.5% on processor fee ONLY = 7.5% x 169 = 12.675 -> 12.68
- Total Fees: 169 + 306 + 12.68 = 487.68

---

### 6. POST /api/v1/calculate - Nigeria Mobile Money 25,000 NGN (Above Tier)

Scenario: Amount above 10,000 NGN threshold - lower rate kicks in.

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 25000, "currency": "NGN", "country_code": "NG", "payment_method": "mobile_money"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_0bd2ecff328e",
    "timestamp": "2026-02-26T07:29:04.190770Z",
    "input": {
        "amount": 25000.0,
        "currency": "NGN",
        "country_code": "NG",
        "payment_method": "mobile_money"
    },
    "customer_pays": {
        "amount": 25000.0,
        "currency": "NGN"
    },
    "merchant_receives": {
        "amount": 14.31,
        "currency": "USD"
    },
    "total_fees": {
        "amount": 1185.63,
        "currency": "NGN"
    },
    "fee_bearer": "merchant",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "1.8% + 25.0 fee on 25000 NGN",
            "amount": 475.0,
            "currency": "NGN"
        },
        {
            "label": "Payment Method Fee",
            "description": "2.5% + 50.0 (tier: above threshold) on 25000 NGN",
            "amount": 675.0,
            "currency": "NGN"
        },
        {
            "label": "VAT on Fees",
            "description": "7.5% on processor_fee",
            "amount": 35.63,
            "currency": "NGN"
        },
        {
            "label": "FX Conversion",
            "description": "NGN->USD at 0.000601 (mid: 0.00062, spread: 3.0%)",
            "amount": 0.48,
            "currency": "NGN"
        }
    ],
    "currency_conversion": {
        "from_currency": "NGN",
        "to_currency": "USD",
        "mid_market_rate": 0.00062,
        "spread_percent": 3.0,
        "effective_rate": 0.000601,
        "original_amount": 25000.0,
        "converted_amount": 14.31,
        "spread_cost_in_original_currency": 0.48
    }
}
```

**Math verification:**
- Processor Fee: 1.8% x 25000 + 25 = 475.00
- Payment Method Fee (tier >10K): 2.5% x 25000 + 50 = 675.00 (lower rate!)
- VAT: 7.5% x 475 = 35.625 -> 35.63
- Total Fees: 475 + 675 + 35.63 = 1185.63

---

### 7. POST /api/v1/calculate - Ghana Card 500 GHS (No FX Conversion)

Scenario: GHS settles in GHS, no currency conversion. 15% combined tax on all fees.

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 500, "currency": "GHS", "country_code": "GH", "payment_method": "card"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_dc12e3f6005d",
    "timestamp": "2026-02-26T07:29:05.391237Z",
    "input": {
        "amount": 500.0,
        "currency": "GHS",
        "country_code": "GH",
        "payment_method": "card"
    },
    "customer_pays": {
        "amount": 519.55,
        "currency": "GHS"
    },
    "merchant_receives": {
        "amount": 500.0,
        "currency": "GHS"
    },
    "total_fees": {
        "amount": 19.55,
        "currency": "GHS"
    },
    "fee_bearer": "customer",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "2.5% + 2.0 fee on 500 GHS",
            "amount": 14.5,
            "currency": "GHS"
        },
        {
            "label": "Payment Method Fee",
            "description": "0.5% fee on 500 GHS",
            "amount": 2.5,
            "currency": "GHS"
        },
        {
            "label": "Combined Tax (VAT + NHIL + GETFund) on Fees",
            "description": "15.0% on processor_fee + payment_method_fee",
            "amount": 2.55,
            "currency": "GHS"
        }
    ],
    "currency_conversion": null
}
```

**Math verification:**
- Processor Fee: 2.5% x 500 + 2 = 14.50
- Payment Method Fee: 0.5% x 500 = 2.50
- Tax: 15% x (14.50 + 2.50) = 2.55
- Total Fees: 14.50 + 2.50 + 2.55 = 19.55
- Customer pays: 500 + 19.55 = 519.55 GHS
- Merchant receives: 500.00 GHS (no FX conversion)
- `currency_conversion` is `null` (correct - same currency settlement)

---

### 8. POST /api/v1/calculate - South Africa Card 500 ZAR (Tier 1)

Scenario: 3-tier card pricing, amount <=1000 ZAR uses highest rate (3.5%), 0% tax.

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 500, "currency": "ZAR", "country_code": "ZA", "payment_method": "card"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_1c544ec42459",
    "timestamp": "2026-02-26T07:29:06.581063Z",
    "input": {
        "amount": 500.0,
        "currency": "ZAR",
        "country_code": "ZA",
        "payment_method": "card"
    },
    "customer_pays": {
        "amount": 522.5,
        "currency": "ZAR"
    },
    "merchant_receives": {
        "amount": 25.84,
        "currency": "USD"
    },
    "total_fees": {
        "amount": 22.5,
        "currency": "ZAR"
    },
    "fee_bearer": "customer",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "3.5% + 5.0 (tier: <=1000.0) on 500 ZAR",
            "amount": 22.5,
            "currency": "ZAR"
        },
        {
            "label": "FX Conversion",
            "description": "ZAR->USD at 0.051675 (mid: 0.053, spread: 2.5%)",
            "amount": 0.66,
            "currency": "ZAR"
        }
    ],
    "currency_conversion": {
        "from_currency": "ZAR",
        "to_currency": "USD",
        "mid_market_rate": 0.053,
        "spread_percent": 2.5,
        "effective_rate": 0.051675,
        "original_amount": 500.0,
        "converted_amount": 25.84,
        "spread_cost_in_original_currency": 0.66
    }
}
```

**Math verification:**
- Processor Fee (tier <=1000): 3.5% x 500 + 5 = 22.50
- Tax: 0% = 0
- Total Fees: 22.50
- Customer pays: 500 + 22.50 = 522.50

---

### 9. POST /api/v1/calculate - South Africa Card 5,000 ZAR (Tier 2)

Scenario: Amount in 1,001-10,000 range uses 2.8% rate.

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "currency": "ZAR", "country_code": "ZA", "payment_method": "card"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_795148507007",
    "timestamp": "2026-02-26T07:29:07.483916Z",
    "input": {
        "amount": 5000.0,
        "currency": "ZAR",
        "country_code": "ZA",
        "payment_method": "card"
    },
    "customer_pays": {
        "amount": 5145.0,
        "currency": "ZAR"
    },
    "merchant_receives": {
        "amount": 258.38,
        "currency": "USD"
    },
    "total_fees": {
        "amount": 145.0,
        "currency": "ZAR"
    },
    "fee_bearer": "customer",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "2.8% + 5.0 (tier: <=10000.0) on 5000 ZAR",
            "amount": 145.0,
            "currency": "ZAR"
        },
        {
            "label": "FX Conversion",
            "description": "ZAR->USD at 0.051675 (mid: 0.053, spread: 2.5%)",
            "amount": 6.63,
            "currency": "ZAR"
        }
    ],
    "currency_conversion": {
        "from_currency": "ZAR",
        "to_currency": "USD",
        "mid_market_rate": 0.053,
        "spread_percent": 2.5,
        "effective_rate": 0.051675,
        "original_amount": 5000.0,
        "converted_amount": 258.38,
        "spread_cost_in_original_currency": 6.63
    }
}
```

**Math verification:**
- Processor Fee (tier 1001-10000): 2.8% x 5000 + 5 = 145.00
- Customer pays: 5000 + 145 = 5145.00

---

### 10. POST /api/v1/calculate - South Africa Card 15,000 ZAR (Tier 3)

Scenario: Amount >10,000 ZAR uses lowest rate (2.2%).

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 15000, "currency": "ZAR", "country_code": "ZA", "payment_method": "card"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_176b998b551d",
    "timestamp": "2026-02-26T07:29:08.449557Z",
    "input": {
        "amount": 15000.0,
        "currency": "ZAR",
        "country_code": "ZA",
        "payment_method": "card"
    },
    "customer_pays": {
        "amount": 15335.0,
        "currency": "ZAR"
    },
    "merchant_receives": {
        "amount": 775.13,
        "currency": "USD"
    },
    "total_fees": {
        "amount": 335.0,
        "currency": "ZAR"
    },
    "fee_bearer": "customer",
    "breakdown": [
        {
            "label": "Processor Fee",
            "description": "2.2% + 5.0 (tier: above threshold) on 15000 ZAR",
            "amount": 335.0,
            "currency": "ZAR"
        },
        {
            "label": "FX Conversion",
            "description": "ZAR->USD at 0.051675 (mid: 0.053, spread: 2.5%)",
            "amount": 19.88,
            "currency": "ZAR"
        }
    ],
    "currency_conversion": {
        "from_currency": "ZAR",
        "to_currency": "USD",
        "mid_market_rate": 0.053,
        "spread_percent": 2.5,
        "effective_rate": 0.051675,
        "original_amount": 15000.0,
        "converted_amount": 775.13,
        "spread_cost_in_original_currency": 19.88
    }
}
```

**Math verification:**
- Processor Fee (tier >10000): 2.2% x 15000 + 5 = 335.00
- Customer pays: 15000 + 335 = 15335.00

---

### 11. POST /api/v1/compare - Kenya 5,000 KES (All Payment Methods)

Scenario: Compare all 3 payment methods for Kenya, sorted by customer cost.

```bash
curl -s -X POST http://localhost:8000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "currency": "KES", "country_code": "KE"}'
```

**Response (200 OK):**
```json
{
    "transaction_id": "cmp_e5e8e7f4e58f",
    "timestamp": "2026-02-26T07:29:09.585571Z",
    "input": {
        "amount": 5000.0,
        "currency": "KES",
        "country_code": "KE"
    },
    "comparisons": [
        {
            "payment_method": "mobile_money",
            "payment_method_name": "M-Pesa Mobile Money",
            "fee_bearer": "merchant",
            "customer_pays": {
                "amount": 5000.0,
                "currency": "KES"
            },
            "merchant_receives": {
                "amount": 30.85,
                "currency": "USD"
            },
            "total_fees": {
                "amount": 156.6,
                "currency": "KES"
            }
        },
        {
            "payment_method": "bank_transfer",
            "payment_method_name": "Bank Transfer (EFT)",
            "fee_bearer": "merchant",
            "customer_pays": {
                "amount": 5000.0,
                "currency": "KES"
            },
            "merchant_receives": {
                "amount": 31.48,
                "currency": "USD"
            },
            "total_fees": {
                "amount": 58.0,
                "currency": "KES"
            }
        },
        {
            "payment_method": "card",
            "payment_method_name": "Card Payment (Visa/Mastercard)",
            "fee_bearer": "customer",
            "customer_pays": {
                "amount": 5179.8,
                "currency": "KES"
            },
            "merchant_receives": {
                "amount": 31.85,
                "currency": "USD"
            },
            "total_fees": {
                "amount": 179.8,
                "currency": "KES"
            }
        }
    ]
}
```

**Verified:**
- All 3 methods returned with human-readable names
- Sorted by customer_pays ascending: 5000.0, 5000.0, 5179.8
- Fee bearer shown for each method (merchant vs customer)
- Input echo uses typed model (not bare dict)

---

### 12. GET /api/v1/audit - Query Audit Log

```bash
curl -s "http://localhost:8000/api/v1/audit?limit=2"
```

**Response (200 OK):**
```json
{
    "total": 12,
    "entries": [
        {
            "transaction_id": "txn_3e7975f9a9f8",
            "timestamp": "2026-02-26T07:29:09.585553Z",
            "country_code": "KE",
            "payment_method": "bank_transfer",
            "amount": 5000.0,
            "currency": "KES",
            "result": { "..." }
        },
        {
            "transaction_id": "txn_e9efc552bc40",
            "timestamp": "2026-02-26T07:29:09.585527Z",
            "country_code": "KE",
            "payment_method": "card",
            "amount": 5000.0,
            "currency": "KES",
            "result": { "..." }
        }
    ]
}
```

**Verified:**
- `total` shows total matching count (12)
- `entries` limited to 2 per `limit=2`
- Sorted by timestamp descending (most recent first)
- Each entry includes full `result` with breakdown

---

### 13. GET /api/v1/audit/{transaction_id} - Get Specific Entry

```bash
curl -s http://localhost:8000/api/v1/audit/txn_1c08092d3f47
```

**Response (200 OK):**
```json
{
    "transaction_id": "txn_1c08092d3f47",
    "country_code": "KE",
    "payment_method": "mobile_money",
    "amount": 5000.0,
    "currency": "KES",
    "result": { "..." }
}
```

**Verified:** Returns the specific entry matching the transaction ID.

---

### 14. GET /api/v1/audit/{transaction_id} - Not Found

```bash
curl -s http://localhost:8000/api/v1/audit/txn_nonexistent
```

**Response (404):**
```json
{
    "error": "not_found",
    "detail": "No audit entry found for transaction ID: txn_nonexistent"
}
```

**Verified:** Returns structured error with 404 status.

---

### 15. GET /api/v1/audit - Filter by Country

```bash
curl -s "http://localhost:8000/api/v1/audit?country_code=NG"
```

**Response:** `total: 4, entries_returned: 4` (all Nigeria entries)

### 16. GET /api/v1/audit - Filter by Payment Method with Pagination

```bash
curl -s "http://localhost:8000/api/v1/audit?payment_method=card&limit=2"
```

**Response:** `total: 7, entries_returned: 2` (7 card entries total, 2 returned per limit)

---

## Error Handling Tests

All error cases return structured `{"error": "...", "detail": "..."}` format. **No 500 errors for any bad input.**

### 17. Unsupported Country (400)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "EUR", "country_code": "FR", "payment_method": "card"}'
```

```json
{
    "error": "unsupported_country",
    "detail": "Country 'FR' is not supported. Available countries: ['KE', 'NG', 'GH', 'ZA']"
}
```

### 18. Unsupported Payment Method (400)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "currency": "KES", "country_code": "KE", "payment_method": "crypto"}'
```

```json
{
    "error": "unsupported_payment_method",
    "detail": "Unsupported payment method 'crypto' for country KE. Available: ['mobile_money', 'card', 'bank_transfer']"
}
```

**Verified:** No extra quotes wrapping the detail string (was a bug, now fixed).

### 19. Currency Mismatch (400)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "currency": "USD", "country_code": "KE", "payment_method": "card"}'
```

```json
{
    "error": "currency_mismatch",
    "detail": "Country KE expects currency KES, got USD"
}
```

### 20. Negative Amount (422)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": -100, "currency": "KES", "country_code": "KE", "payment_method": "card"}'
```

```json
{
    "error": "validation_error",
    "detail": "Input should be greater than 0"
}
```

### 21. Zero Amount (422)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 0, "currency": "KES", "country_code": "KE", "payment_method": "card"}'
```

```json
{
    "error": "validation_error",
    "detail": "Input should be greater than 0"
}
```

### 22. Missing Required Fields (422)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000}'
```

```json
{
    "error": "validation_error",
    "detail": "Field required; Field required; Field required"
}
```

### 23. Invalid Amount Type (422)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": "not_a_number", "currency": "KES", "country_code": "KE", "payment_method": "card"}'
```

```json
{
    "error": "validation_error",
    "detail": "Input should be a valid decimal"
}
```

### 24. Invalid JSON Body (422)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d 'not json'
```

```json
{
    "error": "validation_error",
    "detail": "JSON decode error"
}
```

---

## Edge Case Tests

### 25. Very Small Amount (Fixed Fee > Transaction Amount)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 10, "currency": "KES", "country_code": "KE", "payment_method": "bank_transfer"}'
```

**Response (200 OK):**
```json
{
    "customer_pays": { "amount": 10.0, "currency": "KES" },
    "merchant_receives": { "amount": -0.31, "currency": "USD" },
    "total_fees": { "amount": 58.0, "currency": "KES" },
    "fee_bearer": "merchant"
}
```

**Verified:** Fixed fee (50 KES) + VAT (8 KES) = 58 KES exceeds 10 KES transaction. Merchant receives negative (merchant absorbs all fees). System handles gracefully without errors.

### 26. Very Large Amount (Tiered Pricing)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000000, "currency": "ZAR", "country_code": "ZA", "payment_method": "card"}'
```

**Response (200 OK):**
```json
{
    "customer_pays": { "amount": 1022005.0, "currency": "ZAR" },
    "total_fees": { "amount": 22005.0, "currency": "ZAR" },
    "merchant_receives": { "amount": 51675.0, "currency": "USD" }
}
```

**Math verification:**
- Processor Fee (tier >10K): 2.2% x 1,000,000 + 5 = 22,005.00
- Customer pays: 1,000,000 + 22,005 = 1,022,005.00

### 27. Exact Tier Boundary (10,000 NGN)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 10000, "currency": "NGN", "country_code": "NG", "payment_method": "mobile_money"}'
```

**Result:** `total_fees = 590.38` (uses <=10K tier: 3.2% + 50)

### 28. Just Above Tier Boundary (10,001 NGN)

```bash
curl -s -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"amount": 10001, "currency": "NGN", "country_code": "NG", "payment_method": "mobile_money"}'
```

**Result:** `total_fees = 520.43` (uses >10K tier: 2.5% + 50, lower rate)

**Verified:** Fee drops from 590.38 to 520.43 when crossing the 10,000 NGN boundary - tiered pricing works correctly.

---

## Summary

| Category | Tests | Result |
|----------|-------|--------|
| **Pytest** | 75 tests | 75 passed |
| **Health endpoint** | 1 test | OK |
| **Calculate - Kenya (3 methods)** | 3 tests | All correct |
| **Calculate - Nigeria (tiered)** | 2 tests | Below/above tier correct |
| **Calculate - Ghana (no FX)** | 1 test | No conversion, 15% tax correct |
| **Calculate - South Africa (3 tiers)** | 3 tests | All 3 tiers correct |
| **Compare endpoint** | 1 test | Sorted, all fields present |
| **Audit log (query)** | 3 tests | Pagination, filtering work |
| **Audit log (get by ID)** | 2 tests | Found + 404 correct |
| **Error: unsupported country** | 1 test | 400 + structured error |
| **Error: unsupported payment method** | 1 test | 400 + clean detail string |
| **Error: currency mismatch** | 1 test | 400 + structured error |
| **Error: negative amount** | 1 test | 422 + structured error |
| **Error: zero amount** | 1 test | 422 + structured error |
| **Error: missing fields** | 1 test | 422 + structured error |
| **Error: invalid type** | 1 test | 422 + structured error |
| **Error: invalid JSON** | 1 test | 422 + structured error |
| **Edge: small amount** | 1 test | Handles gracefully |
| **Edge: large amount** | 1 test | Correct tier applied |
| **Edge: tier boundaries** | 2 tests | Exact + just-above correct |
| **Total live API tests** | **28** | **All passed** |

All amounts are JSON numbers (not strings). All errors return `{"error": "...", "detail": "..."}`. No HTTP 500 for any input.
