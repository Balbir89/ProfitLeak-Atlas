# Power BI implementation guide (Power BI Desktop)

> **Artifact status:** This folder contains real data exports, DAX measures, a theme, and a report blueprint. It does **not** contain a `.pbix` file, which requires Power BI Desktop to author.

1. In Power BI Desktop (Windows), **Get data → Text/CSV**. Import `data/marts/cases.csv` as `cases`; import `data/marts/monthly.csv` as `monthly`; import `data/marts/vendors.csv` as `vendors`. Load all numeric columns as **Decimal number**, all month columns as **Text**.
2. In `cases` create **MonthDate** calculated column: `DATE(VALUE(LEFT('cases'[payment_month],4)),VALUE(RIGHT('cases'[payment_month],2)),1)`. In `monthly`, create the equivalent column. Set month labels to `MMM yyyy` but sort by MonthDate.
3. Link `vendors[vendor_id]` 1 → many `cases[vendor_id]` and cross-filter direction **Single**. Do not directly connect `monthly` to the cases fact (it has separate aggregated grain).
4. Copy measures from `MEASURES.dax` (one definition per New measure). The last measure requires a disconnected `Recovery Scenario` table created with `GENERATESERIES(0, 1, 0.05)`; rename its `Value` column to `Factor`.
5. Import theme from `theme.json`. Add four report pages:
   - **01 CEO / CFO cockpit:** Gross Exposure, Risk Adjusted Recovery, Cases Flagged, Cause Share, line graph monthly, root-cause bar graph.
   - **02 Detection forensics:** Table by invoice, vendor, issue, estimated loss, recovery, confidence and action. Slicers: month, vendor, issue type.
   - **03 Vendor risk:** Vendor exposure and geography/category matrix with drill-through for selected vendor.
   - **04 Recovery simulation:** `Recovery Scenario` factor slicer + `Scenario Realized Recovery EUR` KPI + waterfall by root cause.
6. For total spend and loss-rate KPIs use `monthly[spend_eur]` from the aggregated monthly table, never sum case-only spend since `cases` excludes unflagged payments.
7. Show a permanent **SYNTHETIC DATA / NOT VERIFIED LOSSES** caption on all pages.

**Caution:** DAX percentages, recoverability ratios, and rule confidence here demonstrate *business logic*, not calibrated fraud probabilities or actual collections. Validate with source records before claims.
