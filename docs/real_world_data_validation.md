# Real-world data compatibility pilot — Chicago Payments

## Scope and source

Official publisher: **City of Chicago Data Portal**, [Payments dataset](https://data.cityofchicago.org/Administration-Finance/Payments/s4vu-giwb), resource `s4vu-giwb`. The dataset contains vendor payments, check dates, contract and voucher references. Importantly, **many old rows are rolled-up annual totals and are not itemized transactions**.

For this release, `data/public/chicago_vendor_payments_observed.json` contains **44 manually selected institutional/vendor records transcribed from the official API's first 165 public records** on 15 November 2026. It is a small, **non-random and non-representative selection**, NOT a full dataset export. The `source_line` field points to the record index in the API's observed first response. Source values are in USD and remain **completely separate** from the fictional 220,000-row, EUR case study.

## Actual run

Running `python src/public_data_validation.py` produced:

| Check | Observed |
|---|---:|
| Real public records screened | 44 |
| With complete day-level dates | 39 |
| Year-only historical rollups | 5 |
| Invalid / missing core data | 0 |
| Direct-voucher records | 7 |
| Distinct vendors in selected sample | 42 |
| Repeated identical source row candidates | 0 |
| Reused voucher with differing details candidates | 0 |
| Confirmed fraudulent transactions | **Unknown** |
| Validated fraud detection accuracy | **Not measurable** |
| Financial losses / recovered cash | **Not measurable** |

The mixed-year gross sum is **not presented as total city procurement or as monetary leakage**, because these rows are a selectively chosen mix of aggregate and itemized records. A zero count of duplicate candidates in 44 rows is **not** evidence that the City has no duplicates.

## Reproduce on a broader live public sample

The validator supports the official API via:

```bash
python src/public_data_validation.py --live --limit 5000
python -m unittest discover -s tests -v
```

This calls the public API at execution time, and requires network access. The network-accessible source could be retrieved for inspection using a web search service, but **the code execution environment could not access the network**, so the live CLI was not executed here. The included source-observed 44-row fixture was evaluated offline; the CI tests also exercise deliberately repeated, malformed, aggregated, and voucher-reused records.

## Why this is not real-world fraud accuracy validation

- The City payment table has no independent case outcomes or bank-confirmed duplicate-payment labels.
- Source fields cannot substantiate unit-price overcharges, missing goods receipts, missed discounts, or contractual FX spreads.
- The public amount field is in USD; the synthetic corporate project is in EUR. **Never combine them.**
- Validated predictive precision/recall and realized recovery require authorized real invoice, contract, settlement and audit-decision records from a partner organization.

**Meaningful validation achieved:** public-data ingestion/format checks, aggregate vs event separation, non-accusatory review criteria, adversarial tests and audit documentation. **Not achieved:** real-world fraud-detection performance or production certification.
