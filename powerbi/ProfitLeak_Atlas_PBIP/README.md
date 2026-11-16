# Power BI Desktop source project (PBIP)

Open `ProfitLeak_Atlas.pbip` in Power BI Desktop **on Windows**. This is
source code (PBIR report + TMDL semantic model) with a *self-contained snapshot*
of monthly financial metrics, root causes, 40 suppliers and 200 audit queue cases.
The full 220k transaction mart remains in the parent repository and should be
loaded separately if further drill-through is required. No external credentials
or absolute file path needed for the embedded snapshot.

**Status:** JSON files have been structurally checked, but no Windows Power BI
Desktop execution is available in the authoring environment. Please open and
refresh in Desktop, then save a `.pbix` for deployment. This is NOT a verified
PBIX or guaranteed deployment-ready report.

Metrics are hypothetical and all data synthetic.
