# Portfolio story · ProfitLeak Atlas Expert

**Business challenge:** A fictional multi-country enterprise has €157.68 million in procurement payments over 22 months. Finance suspects duplicate settlements, deviations from agreed prices, missing goods receipts, lost discounts, and unjustified FX spreads. A simple spend dashboard does not create a reviewable audit trail.

**My role:** Designed a reproducible end-to-end analytical case study with 220,000 payments, contract reference data, SQL controls, Python risk prioritization, reviewable cases, Excel decision support, offline mobile dashboard, and Power BI source.

**Outcome in synthetic simulation:** €9.84 million flagged as **potential** gross exposure; €6.88 million modeled risk-adjusted recovery; 52,371 rule-flagged payments, including 11,890 control-only approval-fragmentation flags with **€0 assigned loss**. Actual recovered cash: **€0**.

**Distinctive decisions:**
- Separate policy violations and monetary exposures to avoid inflating savings.
- Explain each case with its rule, vendor, invoice and proposed follow-up action.
- Build a 200-case ownership/evidence/status audit workflow with append-only trail.
- Introduce a historical 2025 baseline and temporal holdout rather than random splitting across time.
- Test the amount-only outlier screen using 1,500 designed examples. It returns 48% precision and 49% recall.
- Verify that authorized installments clear the repeat check and repeated credits are counted once. In 2,550 separate synthetic settlements, the authorization-aware rule eliminates 450 false excess flags.
- Verify the automated rebuild with 66 passing tests. The core SQL build handles 220,000 payments in a 6.59-second median and one million in a 30.18-second local run.

**Interview pitch (30 seconds):** “I built a financial-forensics analytics console that traces fictional invoice and supplier exceptions to a review workflow, instead of claiming all anomalies are fraud. It processes 220k payments with SQL and Python, layers explainable statistical prioritization, quantifies potential financial exposure, and documents real limitations through an out-of-sample challenge. I delivered Excel, an offline mobile dashboard, a Power BI source project, and automated tests.”

**Next steps for actual deployment:** Integrate bank/ERP source, temporal contract addenda, role-based access control, authenticated evidence storage, external alert calibration, supplier dispute/reversal processes, and Power BI Desktop validation.
