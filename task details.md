# BACKEND

## The Cross-Border Tax Trap: Build a Dynamic Fee Calculator for Afya Health

### The Scenario

Afya Health is a fast-growing telemedicine platform operating across Kenya, Nigeria, Ghana, and South Africa. They process over 15,000 patient payments per day for virtual consultations, prescription deliveries, and lab test bookings.

Last month, their finance team discovered a crisis: they've been under-collecting fees by ~$47,000/month and are out of compliance with local tax regulations in 3 of their 4 markets. The culprit? Their legacy payment fee calculation system was hardcoded for a single country and payment method. Now, with multiple countries, currencies, and payment methods (mobile money, card payments, bank transfers), the system can't handle:

- Variable processor fees by payment method and country
- Cascading taxes (some countries apply VAT on top of the processor fee, others don't)
- Dynamic currency conversion with spread calculations
- Threshold-based pricing (some processors charge different rates above/below certain transaction amounts)

The CFO has escalated this to Yuno. Afya needs a robust, configurable fee calculation engine that can accurately compute what the customer pays, what Afya nets, and what goes to processors, payment methods, and tax authorities — before the transaction is processed.

You've been tasked with building the backend service that solves this.

### Domain Background: Key Concepts

If you're new to payments, here's what you need to know:

#### Payment Processing Fees

When a customer pays for something, the merchant (Afya) doesn't receive 100% of that amount. Various parties take fees:

- **Processor fee:** The payment processor (the company that moves money between accounts) charges a percentage + fixed fee. Example: 2.9% + $0.30 per transaction.
- **Payment method fee:** Some payment methods have their own fees. For example, mobile money (M-Pesa, MTN Mobile Money) might charge 1.5%, while bank transfers might be flat-rate or free.
- **Interchange fee (optional for this challenge):** The fee that goes to the card-issuing bank. Usually baked into processor fees for simplicity.

#### Cross-Border & Multi-Currency Challenges

- **Settlement currency vs. transaction currency:** A customer in Kenya might pay in KES (Kenyan Shillings), but Afya's bank account might be in USD. Someone has to convert the currency.
- **FX spread:** When currency conversion happens, there's usually a markup (e.g., 1-3%) on top of the market exchange rate.
- **Local taxes:** Many countries require VAT, GST, or other taxes to be applied to payment processing fees. In some countries, the tax applies to the processor fee itself. In others, it applies to the full transaction amount.

#### What This Challenge Is About

You're building a fee calculation engine — a service that takes in transaction details (amount, currency, country, payment method) and returns a detailed breakdown:

- How much the customer pays (including any fees passed to them)
- How much the merchant (Afya) receives after all deductions
- Exactly where each cent goes (processor, payment method provider, tax authority, FX conversion, etc.)

This is not about actually processing payments. It's about modeling complex, nested, country-specific fee logic and making it easy to configure and extend.

---

## Your Mission

Build a backend fee calculation service that can:

1. Accept transaction input (amount, currency, country, payment method) and return a detailed fee breakdown
2. Support complex, configurable fee rules including:
   - Percentage + fixed fees
   - Tiered pricing (different rates for different transaction amounts)
   - Cascading taxes (tax on the processor fee vs. tax on the total)
   - Currency conversion with configurable FX spreads
3. Be extensible and maintainable — Afya's operations team (non-engineers) should be able to add a new country or update a fee rule without touching code

---

## Functional Requirements

### Core Requirement 1: Fee Calculation Engine

Build a service that accepts a transaction request and returns a structured breakdown of all fees.

**Input (at minimum):**

- Transaction amount (decimal)
- Transaction currency (e.g., KES, NGN, GHS, ZAR, USD)
- Country code (e.g., KE, NG, GH, ZA)
- Payment method (e.g., "mobile_money", "card", "bank_transfer")

**Output (at minimum):**

- **Customer pays:** Total amount debited from the customer
- **Merchant receives:** Net amount Afya gets after all deductions
- **Itemized breakdown:** Each fee component with label and amount (e.g., "Processor Fee: 2.9% + 0.30 USD = 1.87 USD", "VAT on Processor Fee: 16% = 0.30 USD", "FX Conversion Spread: 2% = 0.54 USD")
- **Currency information:** If conversion happened, show the original and settlement currencies

**Expected behaviors:**

- Handle at least 4 different fee rule types: percentage-based, fixed, tiered/threshold-based, and tax/VAT on fees
- Support currency conversion with a configurable FX spread
- Support tax rules that can apply to subsets of fees (e.g., "16% VAT on processor fee" vs. "5% tax on total transaction")
- Return errors for invalid input (unsupported country, missing payment method, etc.)

**Acceptance criteria:**

- A developer can send a request with transaction details and receive a detailed, accurate breakdown
- The calculation logic correctly handles edge cases like zero-amount transactions, very large amounts, and rounding

### Core Requirement 2: Configurable Fee Rules (Data-Driven)

Afya's operations team needs to update fee rules regularly (new processor contracts, tax law changes, etc.) without engineering support.

**What this means:**

- Fee rules, tax rates, FX spreads, and payment method fees should be stored as configuration/data, not hardcoded in business logic
- The service should load these rules dynamically (from a file, database, or in-memory store — your choice)
- The configuration format should be human-readable and easy to modify

**Example scenarios your config should support:**

- "In Kenya, mobile money transactions have a 1.5% fee, cards have 2.9% + 10 KES, and all processor fees are subject to 16% VAT"
- "In Nigeria, any transaction above 10,000 NGN gets a lower processor rate (2.5% instead of 3.2%)"
- "When converting from ZAR to USD, apply a 2.5% FX spread on top of the market rate"

**Acceptance criteria:**

- Fee rules are externalized (not hardcoded in if/else blocks)
- A non-engineer could reasonably add a new country or update a tax rate by editing the config
- The system loads and applies the correct rules based on the country/payment method in the request

### Stretch Goal 1: Fee Comparison Endpoint

Afya wants to show customers their options before they choose a payment method.

Build an endpoint that takes an amount, currency, and country — and returns the total cost to the customer for each available payment method in that country, sorted by cost.

**Example output:**

> Transaction: 5000 KES in Kenya
>
> 1. Bank Transfer: 5000 KES (no fees passed to customer)
> 2. Mobile Money: 5075 KES (1.5% fee)
> 3. Card Payment: 5155 KES (2.9% + 10 KES fee)

**Acceptance criteria:**

- Returns a ranked list of payment methods with customer-facing total cost
- Clearly indicates which fees are being passed to the customer vs. absorbed by the merchant

### Stretch Goal 2: Audit Log & Fee Breakdown History

Every fee calculation should be logged with a unique ID, timestamp, and full input/output for auditing and debugging.

Build a simple query interface to retrieve past calculations (e.g., by transaction ID, date range, or country).

**Acceptance criteria:**

- Each calculation is persisted with sufficient detail to reproduce the result
- A reviewer can query past calculations and see exactly what fees were applied

> **Note:** Partial or complete implementation of stretch goals is expected and welcomed. Prioritize the core requirements first.

---

## Test Data

Your solution should include realistic test data for development and demonstration. Generate or create:

- At least 4 countries with different fee structures (e.g., Kenya, Nigeria, Ghana, South Africa)
- At least 3 payment methods per country (mobile money, card, bank transfer, etc.)
- Fee rules that include:
  - At least one tiered/threshold-based rule (different rates above/below a certain amount)
  - At least one currency conversion scenario (e.g., paying in KES but settling in USD)
  - At least two different tax treatments (e.g., VAT on processor fee in one country, no tax in another)
- Sample transactions covering:
  - Small amounts (edge case for fixed fees)
  - Large amounts (edge case for tiered pricing)
  - Multiple currencies
  - Each payment method at least once

You may generate this data manually, with a script, or using AI tools. The goal is to have a realistic, varied dataset to demonstrate your solution.

---

## What "Done" Looks Like

A reviewer should be able to:

1. Run your service (with clear setup instructions)
2. Send API requests (or run a script/CLI) with transaction details and receive accurate, detailed fee breakdowns
3. Inspect your fee configuration and understand how rules are structured
4. See evidence of good engineering: clean code structure, handling of edge cases, basic error handling, and a README explaining your design choices
5. Optionally: Test stretch goal features (comparison endpoint, audit log)

---

## Deliverables

You will submit:

- Working backend service (API, CLI, or script — your choice of language/framework)
- Fee configuration data (JSON, YAML, database seed, or similar)
- Test data (sample countries, payment methods, and fee rules as described above)
- README with:
  - How to run your service
  - How to test it (example requests or test script)
  - Brief explanation of your design decisions (how you modeled fees, why you chose your data structure, trade-offs you made given the time constraint)
  - Example output showing at least 3 different fee calculation scenarios

### Deliverables Summary

- Working backend service (API, CLI, or script) that calculates payment fees based on transaction details
- Fee configuration data (JSON, YAML, database seed, or similar) covering at least 4 countries with different fee structures
- Test data including sample countries, payment methods, and realistic fee rules as described in the challenge
- README with setup instructions, testing guide, design decisions, and trade-offs made given the time constraint
- Example output showing at least 3 different fee calculation scenarios with detailed breakdowns

---

## Evaluation Criteria

| Criteria | Points |
|---|---|
| **Fee calculation accuracy:** Correct handling of percentage fees, fixed fees, tiered pricing, cascading taxes, and currency conversion with proper rounding | 25pts |
| **Configuration-driven design:** Fee rules are externalized and easily modifiable without code changes; clear, maintainable structure | 20pts |
| **Code quality and architecture:** Clean separation of concerns, appropriate abstractions, error handling, and extensibility | 20pts |
| **Completeness of test data and scenarios:** Realistic, varied dataset covering edge cases (small/large amounts, multiple currencies, different tax treatments) | 15pts |
| **API/interface design:** Clear, intuitive input/output format; detailed, structured fee breakdowns; appropriate error responses | 10pts |
| **Documentation and examples:** Clear README with setup instructions, design rationale, and runnable examples demonstrating the solution | 10pts |
| **Total** | **100pts** |
