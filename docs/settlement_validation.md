# Settlement controls and pipeline performance

## Invoice exposure

The source records the authorized total in euro cents. For repeat payments to the same vendor and invoice, the detector orders settlements by month and payment ID. It compares total paid to date with the invoice authorization and caps any above-budget amount at the current payment. This ensures the current row contributes only its own incremental excess.

The rule requires a positive, consistent authorization on all rows in the repeated invoice. Older CSVs without the column still load. Missing or conflicting authorization generates an invoice repeat review with zero assigned exposure when no other independent financial rule applies. The detector covers positive disbursements. Reversals, credits, and exact intramonth settlement order require a richer source.

### Targeted comparison

`python src/validate_settlements.py` constructs 1,200 separate fictional invoices and runs the SQL detector on 2,550 settlements. Scenarios include ordinary payments, approved installments, full duplicates, partial excess, multiple excess payments and ambiguous authorization. Scenario outcomes are retained separately from input rows.

| Result on 2,250 settlements with known outcomes | Original repeat rule | Revised rule |
|---|---:|---:|
| Correctly identified excess payments | 600 | 600 |
| Legitimate payments flagged as excess | 450 | 0 |
| Excess payments missed | 0 | 0 |
| Total absolute exposure error | €370,638.06 | €0.00 |

The revised rule also sent all **300** ambiguous follow-ups to review and assigned **€0** to them. These results establish that the specified controls work for the tested scenarios. Real-world accuracy still requires adjudicated invoice, contract and settlement evidence. The amount-only anomaly challenge in the model card measures a separate screening method.

Machine-readable results are in [`settlement_validation.json`](../data/marts/settlement_validation.json).

## Runtime benchmark

| Input | Baseline | Revised pipeline |
|---|---:|---:|
| 220,000 payments, three runs per version | 8.22 s median | 6.59 s median |
| 1,000,000 payments, one run | — | 30.18 s |

Timings include CSV import, SQLite rule evaluation, materialization and financial mart export. Both 220,000-payment builds used equivalent scenario inputs and produced identical headline totals. The updated pipeline performs invoice windows only for repeated invoices and computes purchase order totals only for orders with an unapproved payment. Measurements are local; machine and data characteristics affect duration.

Reproduce with `python src/benchmark_pipeline.py --runs 3`. To compare against the prior ZIP, extract it separately and add `--baseline /path/to/original/ProfitLeak-Atlas`. The benchmark rebuilds the SQL database and financial marts in both working directories. Raw inputs must be present in both. Full measurements are in [`pipeline_benchmark.json`](pipeline_benchmark.json).

## Try the investigation workflow

After the analytical rebuild, create the local investigation queue and get a financial case ID from `data/marts/audit_casebook.csv`. Substitute that ID for `PAYMENT_ID` below. The sample credit is fictional.

```bash
python src/case_workflow.py init
python src/case_workflow.py assign PAYMENT_ID Analyst --actor Supervisor
python src/case_workflow.py status PAYMENT_ID 'In Review' --actor Analyst --reason 'Triage completed'
python src/case_workflow.py evidence PAYMENT_ID demo://bank/123 'Simulated bank statement' --actor Analyst
python src/case_workflow.py status PAYMENT_ID Verified --actor Supervisor --reason 'Statement reviewed'
python src/case_workflow.py cash PAYMENT_ID 1.00 demo://credit/456 --actor Analyst
python src/case_workflow.py cash PAYMENT_ID 1.00 demo://credit/456 --actor Analyst
python src/case_workflow.py export
```

The two credit submissions produce one €1 credit and one credit event for that case. An existing reference with a different amount is rejected. The workflow serializes writes and keeps case updates and events in the same transaction. Calculation and audit history use SQLite locally. Production deployment would require authenticated actors and access controls.
