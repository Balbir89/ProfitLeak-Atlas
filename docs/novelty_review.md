# Originality review — conducted 15 November 2026

**No guarantee of global uniqueness.** Public repositories already study profit leakage using SQL, Excel and Power BI. Originality should be described as a specific implementation, set of synthetic data, and transparent audit design — not as an unprecedented general concept.

Examples reviewed:

- https://github.com/Shaarif-Mohammed/Retail-Profit-Leakage-Analysis — retailer discount, region, and margin-loss reporting using SQL / Power BI.
- https://github.com/KarolBukowski94/Superstore_Analysis — layered SQL + Power BI profitability and customer economics.
- https://github.com/ali-pervanoglu/pricing-revenue-intelligence-dashboard — pricing anomalies, FX exposure and profit-leakage analytics.
- https://github.com/in-bhosale/excel-operational-performance-profitability-analysis — Excel-based operational dashboard and returns analysis.

## Differentiation in this case study

1. An invented 220k-row procurement *payment* population with five financial-exposure exception classes plus one explicitly nonfinancial governance class.
2. Deterministic synthetic ground truth held in a separate source file, not referenced by any detection SQL.
3. Traceable supplier/contract/payment evidence cases, recommended manual validation actions, and no presumption of fraud.
4. A financial model that separates exposure, modeled recoverability and realized cash (zero).
5. Multiple consumable modes: self-contained HTML console, spreadsheet financial controls, reproducible SQLite/Python pipeline and Power BI implementation assets.

This combination is designed to be distinctive **within this specific portfolio case**, not objectively proven unique across all work in the world.
