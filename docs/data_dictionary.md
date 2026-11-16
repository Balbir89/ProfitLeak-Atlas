# Data dictionary and model grain

| Table / file | Grain | Key | Purpose |
|---|---|---|---|
| `data/master/vendors.csv` | One vendor | vendor_id | Vendor name, industry, geography, tier |
| `data/master/contracts.csv` | One contract per vendor | vendor_id | Benchmark prices, discounts, FX guardrail, approval ceiling |
| `data/raw/payments.csv` | One disbursement event | payment_id | Observed payment and invoice fields |
| `data/truth/injected_labels.csv` | One payment | payment_id | Synthetic benchmark labels, **never used by detector** |
| `database/atlas.db : case_mart` | One payment | payment_id | Joined evidence, issue type, exposure and recovery model |
| `data/marts/cases.csv` | One flagged payment | payment_id | Power BI / audit export with evidence and recommended action |
| `data/marts/monthly.csv` | One calendar month | payment_month | Total spend, flags and potential exposure |
| `data/marts/vendors.csv` | One vendor | vendor_id | Ranked supplier exposure |
| `data/marts/root_causes.csv` | One exception type | issue_type | Issue contribution and modeled recovery |

## Raw payment fields

- `payment_id`: unique synthetic settlement event ID.
- `invoice_ref`: supplier invoice identifier; repeated values can indicate multiple payments.
- `purchase_order`: PO reference used to assess approval fragmentation.
- `vendor_id`: vendor dimension foreign key.
- `payment_month`: ISO month key `YYYY-MM`.
- `cost_center`: synthetic internal operating owner.
- `quantity`, `billed_unit_price_eur`, `received_qty`: paid quantity, invoiced unit price, goods received.
- `paid_early`, `discount_taken_pct`: simplified early-settlement eligibility and discount taken.
- `fx_spread_pct`: incremental payment spread, not a spot FX conversion rate.
- `paid_amount_eur`: settled invoice amount, EUR.
- `invoice_authorized_cents`: optional positive integer invoice authorization in euro cents, repeated consistently across that invoice's settlement rows. Older files omit it. Missing or conflicting values prevent a repeated invoice from creating duplicate-payment exposure.
- `approval_tier`: workflow state; not proof of authorization.

## Important differences

- `gross_loss_eur`: modeled financial exposure **before** case validation.
- `modeled_recovery_eur`: modeled expected recovery **after** issue recovery factor and vendor haircut.
- `rule_confidence`: deliberately chosen diagnostic score, **not** trained statistical probability.
- `Approval fragmentation`: control exception, **not** a financially quantified loss.
- `Invoice repeat review`: follow-up when authorization is incomplete or inconsistent, with €0 assigned exposure from the repeat rule.
- `invoice_paid_to_date_cents`: cumulative settled amount across a repeated vendor invoice in month and payment ID order. `verified_invoice_authorized_cents` in the case export is populated when authorization values are present and consistent across the source records.
