# ProfitLeak Atlas — Recruiter summary

**Category:** Financial Forensics / Procurement Analytics Portfolio Case Study  
**Tools:** Python, SQLite/SQL, Advanced Excel, Power BI source (PBIP), offline HTML

**Business problem:** How can finance and internal audit teams identify and prioritize potential payment leaks across invoices, vendor contracts and procurement controls?

**Approach:** Built a reproducible 220,000-payment synthetic scenario with SQL controls, Python risk prioritization, an Excel recovery model, and a 200-case evidence workflow. Invoice controls distinguish authorized installments from excess payments. The workflow records a retried credit only once per case.

**Illustrative result:** €157.68M in fictional payment spend; €9.84M potential gross exposure; €6.88M scenario-based recoverable estimate; 52,371 flagged transactions, including nonfinancial control exceptions. **No real fraud, savings or recovered cash were established.**

**Quality evidence:** 66 local tests and 84 offline Power BI source checks passed. The core build went from 8.22 to 6.59 seconds at 220,000 rows and completed a one-million-payment run in 30.18 seconds. A separate synthetic settlement challenge reduced false overpayment flags from 450 to zero across 2,550 designed records. The 44-row Chicago pilot checked data-format compatibility.

**Notable design decisions:**
- Separate financial exposure from control-only risk (avoid overstating losses).
- Provide invoice and vendor context for explainable exception review.
- Include an assignable audit workflow with an append-only event history.
- Publish a static phone-compatible demo with embedded numbers and charts.
- Disclose the limitations of scenario-generated labels and unverified Windows Power BI Desktop rendering.

**Technical limits:** The PBIP source has not been opened in Windows Desktop, no native `.pbix` was built, and independent real-world fraud outcome labels were unavailable.
