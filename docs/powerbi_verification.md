# Power BI source verification

**Verified offline:** `python src/verify_powerbi_source.py` executed **84 structural/semantic-reference checks** on the project's PBIP, PBIR and TMDL source. All passed. The validator checks:

- valid JSON parsing and expected PBIP, PBIR project references;
- three report pages, 10 visuals and canvas positions;
- every visual's referenced model table, column or measure exists;
- `cardVisual` uses the required `Data` binding role;
- the TMDL imports and table refs exist;
- financial snapshot totals and payment counts reconcile to the original synthetic SQL marts.

Machine-readable report: [`powerbi_source_validation.json`](powerbi_source_validation.json).

**NOT verified:** Windows **Power BI Desktop** runtime execution, native visual rendering, import/refresh, publishing or a `.pbix` file. This environment cannot run Windows Power BI Desktop. Microsoft documents PBIP as a source project, and says Desktop validates the PBIR changes on opening. Source checks do **not** substitute for that runtime check.

**Final manual Desktop acceptance step (only if you need native Power BI):** open `powerbi/ProfitLeak_Atlas_PBIP/ProfitLeak_Atlas.pbip` in Windows Power BI Desktop; confirm all 3 pages render, all cards/charts load and measures agree with `data/marts/metrics.json`; then save as `.pbix`. If an error appears, repair it in Desktop before claiming verification or publishing.

**Public test does not load into the current PBIP:** The native source model uses a *synthetic snapshot*; the independent Chicago pilot lives separately in `data/public/`. Do not label Power BI visuals as real-data validated.

References: [Microsoft PBIP documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview) and [PBIR report definition](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report).
