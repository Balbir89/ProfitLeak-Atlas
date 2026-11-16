# Model assumptions and limitations

## Scenario boundaries

- All vendors, contracts, payments, exceptions, amounts and recoverability probabilities are **synthetic** and not sourced from a real company.
- EUR is assumed throughout. Values approximate an EU group with 220,000 payment events between January 2025 and October 2026.
- Synthetic exceptions are introduced by an explicit generator. Detection code intentionally uses rules aligned with those assumptions; therefore apparent 100% precision/recall on the constructed dataset has **no external validity**.
- Purchase orders are payment-reference groups, not unique order-line records. Each source payment has one synthetic primary issue to avoid double-counting across the six classes.

## Loss vs controls

| Issue | Gross financial exposure | Evidence required |
|---|---|---|
| Duplicate payment | Incremental settlement amount above the consistent invoice authorization | Authorized invoice total, installments, ledger and bank settlement |
| Invoice repeat review | €0 assigned by this rule when authorization is missing or inconsistent | Obtain the authoritative invoice total and reconcile related settlements |
| Undelivered goods | Value paid without units received | GRN, invoice, supplier delivery dispute |
| Contract price variance | Billed minus baseline contract price, times quantity | Effective agreement, price addenda, invoice |
| Missed early discount | Eligible discount not taken | Terms, actual settlement date, clause |
| FX spread excess | Actual FX spread above contractual allowance | Payment FX quote, contract bank spread |
| Approval fragmentation | **€0** assumed | Purchase order approval trail, policy and controls |

All gross losses are **investigative estimates**, not proven fraud, confirmed overpayments or amounts legally recoverable.

## Recovery scenario

`modeled_recovery = gross_exposure × issue_recovery_factor × (1 - supplier_haircut)`

| Root cause | Assumed recovery factor |
|---|---:|
| Duplicate payment | 90% |
| Undelivered goods | 70% |
| Contract price variance | 55% |
| FX spread excess | 65% |
| Missed early discount | 30% |
| Approval fragmentation | 0% |

Supplier haircuts are deterministic 5%, 10% or 15%. They are modeling assumptions, **not calibrated probabilities**. The what-if slider is an additional *realization multiplier* applied to modeled recovery.

## What production deployment would require

Effective-dated contracts, vendor master reconciliation, currency conversion rates from an authoritative source, payment-settlement status, full audit logs, timestamps, approval workflow details, refunds/credits ledger, and a human case-closure process. Add a production backtest using independently verified historical resolutions before discussing real detection performance. Do not present synthetic figures as employer impact or real savings.
