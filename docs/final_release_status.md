# ProfitLeak Atlas Expert Release

| Check | Verified result |
|---|---|
| Full rebuild and regression suite | 66 passing tests over the 220,000-payment release |
| Core pipeline benchmark | Median 6.59 s at 220,000 rows vs 8.22 s for the original package, with matching headline totals |
| Scale check | 30.18 s for 1 million rows in a single local run |
| Invoice settlement controls | In 2,550 designed settlements, the revised SQL kept all 600 true excess cases, cleared 450 false flags, and routed 300 ambiguous follow-ups to manual review with zero assigned exposure |
| Case workflow | Duplicate and concurrent credit retries record one credit and one event per case reference |
| Excel workbook | Saved headline values reconcile to the package's SQL results |
| Web demos | Local navigation and data tested. Explorer search, issue filter, and slider logic checked |
| Public-data compatibility | 44 curated Chicago entries screened, including 5 year-only records |
| Power BI project source | 84 offline source checks passed |
| Power BI Desktop execution | Pending a Windows Desktop run |
| Real-world detection performance | Pending trusted outcomes from real invoice, banking and audit systems |

The **€9.84M** figure is simulated potential gross exposure. The **€6.88M** figure is a modeled scenario, with **€0** real-world recovery.

See [settlement controls and benchmark methods](settlement_validation.md) and the [Power BI Desktop acceptance steps](powerbi_verification.md).
