# ReLiCGameMaster Commerce Model

Status: **IMPLEMENTATION BASELINE / NOT A REVENUE FORECAST**  
Updated: 2026-09-20.

This document records the commerce facts currently encoded on the active
`live-alpha-rist-blazor-world` branch. It separates implemented facts from
unknowns. Numbers below are gross billing arithmetic only; they are not claims
about demand, adoption, valuation, profit, or future performance.

## Current monthly plan prices

| Plan | Monthly price (USD) | Current server entitlement family |
| --- | ---: | --- |
| Dedicated Roleplayer | $0 | Online roleplayer access |
| Standard Roleplayer | $5 | Online roleplayer access |
| GameMaster | $10 | Roleplayer + GameMaster access |
| Storyteller | $15 | Roleplayer + GameMaster + Storyteller access |
| Worldbuilder | $20 | Roleplayer + GameMaster + Storyteller + Worldbuilder access |

These prices are encoded in
`infra/aws/rist-platform-authority/app.py::COMMERCE_PLANS`.

The Dedicated Roleplayer eligibility rules are not published here. Do not infer
labor, attendance, employment, volunteer, or other obligations from the $0
price. Any such program requires separate policy and legal review before public
use.

## Subscription projection math

For paid monthly subscribers:

```text
MRR = ($5 × StandardRoleplayers)
    + ($10 × GameMasters)
    + ($15 × Storytellers)
    + ($20 × Worldbuilders)

ARR run-rate = MRR × 12
```

Examples are arithmetic scenarios, not forecasts:

| Scenario | Gross MRR | Gross annual run-rate |
| --- | ---: | ---: |
| 100 Standard Roleplayers | $500 | $6,000 |
| 100 GameMasters | $1,000 | $12,000 |
| 100 Storytellers | $1,500 | $18,000 |
| 100 Worldbuilders | $2,000 | $24,000 |
| 25 of each paid plan (100 paid accounts total) | $1,250 | $15,000 |
| 250 of each paid plan (1,000 paid accounts total) | $12,500 | $150,000 |

These figures are gross billing before payment processing, refunds, taxes,
chargebacks, discounts, creator revenue share, infrastructure, payroll, support,
marketing, insurance, legal/accounting costs, or other expenses.

## Private / sandbox world testing allowance

During the current public-alpha testing period, each authenticated account includes
up to **5 owned private/sandbox worlds** without an additional world-slot
entitlement. The canonical Shaelvien MMO world does **not** consume one of these
five testing slots. A sixth owned private/sandbox world still requires a
server-granted world-slot entitlement unless the account has an unlimited or
platform-owner override.

This is a temporary testing allowance, not a published long-term pricing
commitment. Each included private/sandbox world still starts with the currently
implemented 2048 × 2048 pixel surface allowance unless a larger-surface
entitlement or override applies.

## Shaelvien Tokens

Implemented facts:

- completing a RIST profile creates one genesis Shaelvien Token;
- a token is held by one authenticated account and is spent server-side when
  claiming eligible Shaelvien property space;
- current property-space claims are 2048 × 2048 pixels with a maximum height of
  100 layers;
- the server binds the token and property record atomically;
- token secret halves are not returned by the public API;
- additional tokens can be minted only through server-authorized commerce
  fulfillment;
- complimentary access links can include additional tokens;
- there is currently no public token transfer-for-cash function.

**No paid Shaelvien Token price is currently encoded.** Revenue projections for
token sales must remain omitted until a price and fulfillment policy are
approved.

Shaelvien Tokens are application access/property entitlements. This document
does not describe them as cryptocurrency, securities, investments, or assets
with an expected increase in value.

## Complimentary access

The authority service now supports:

- platform-owner-created one-use access links;
- plan-scoped complimentary access;
- optional expiration;
- revocation;
- optional Shaelvien Token quantity;
- direct server-side access grants to an authenticated user ID;
- audit and user notification records.

Only the hash of the invite secret is stored. Redeeming a link creates the
server entitlement; changing browser state cannot create access.

## Payment status

A recurring-payment processor has **not** been connected in the repository.
No page should claim that a subscription or Shaelvien Token can currently be
purchased until provider checkout, signed webhook verification, refund/
cancellation handling, tax treatment, and the applicable legal/policy updates
are implemented.


## AI agent commerce v0

The public Agent Commerce front is a **manual-verification payment intake**, not
an automatic entitlement system. Its current rules are:

- an AI service charge is calculated as the **ReLiC-verified service cost ×
  1.80** (an 80% markup), rounded to the nearest cent;
- a client-entered amount never establishes the cost basis by itself. The cost
  reference and service cost must first be supplied or verified by ReLiC;
- the purchaser provides its Shaelvien/ReLiC account ID and a generated purchase
  reference;
- the initial payment methods are the existing ReLiC PayPal donation link or
  native Bitcoin sent to the published ReLiC BTC receiving address;
- PayPal payments require the generated payment note. Bitcoin payments require
  the account ID, purchase reference, and transaction ID for manual
  reconciliation;
- payment does not automatically grant an entitlement, AI admission, a
  Shaelvien Token, a world slot, or an exception to permissions;
- external AI capacity is bounded at **one external AI slot per complete ten
  connected humans**, with human access taking priority;
- AI-created or AI-operated content defaults to the all-audiences content level.
  A higher content level requires explicit ReLiC company authorization;
- AI operation remains subject to server throttling, resource-yield controls,
  the existing UTC session limit, and any stricter runtime limit applied by the
  authoritative service;
- paid/self-service Shaelvien Token sales remain disabled until explicit
  per-account human and AI token caps plus a paid Token price are approved and
  encoded server-side;
- the intended policy is no discretionary refunds after a manually verified
  service payment, except where applicable law or a payment-provider rule
  requires otherwise.

The current public BTC receiving address is
`bc1q8r5vscvdc0t7rxch056wjs7hstpndcs80jflwe` on the native Bitcoin network.
The public machine-readable commerce manifest is
`/.well-known/relic-ai-commerce.json`, which points to
`/ai-purchase/commerce.json`.

This v0 flow deliberately preserves the existing authority rule: **payment is
evidence for later fulfillment review, never permission by itself.**

## Kickstarter facts used by the public campaign preparation page

For U.S. projects, Kickstarter currently states that a successfully funded
campaign pays a 5% Kickstarter fee. Its U.S. fee page currently lists payment
processing at 3% + $0.30 per pledge for ordinary pledges and a separate
micropledge schedule for pledges under $10. Kickstarter also states that it
does not take equity in projects and describes the platform as rewards-based
crowdfunding rather than financial investment.

Sources checked 2026-09-19:

- https://www.kickstarter.com/help/fees?region=united-states
- https://updates.kickstarter.com/how-crowdfunding-works-a-guide-for-creators/

A Kickstarter funding goal, launch date, reward tiers, expected backer count,
conversion rate, and campaign revenue are **not yet established facts** in the
repository and must not be presented as forecasts.

## Investor/backer reporting rule

When showing projections:

1. show the formula and the user-supplied assumptions;
2. label the result as gross arithmetic, not a forecast;
3. never invent subscriber counts, conversion rates, churn, token sales,
   campaign totals, valuation, margins, or profitability;
4. distinguish implemented product facts from planned features;
5. identify material unknowns rather than filling them with optimistic
   estimates.
