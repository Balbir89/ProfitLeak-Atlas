# ProfitLeak Atlas — GitHub publishing checklist

**Goal:** Publish a convincing, verifiable portfolio case study with a working public demonstration. The project includes an Excel workbook, Python and SQL code, report-source files, an audit trail and a reproducible test suite.

## A. Upload from Mac (recommended)

1. Download `ProfitLeak_Atlas_Expert_Release.zip`. On your Mac, double-click the ZIP. Open the new `ProfitLeak-Atlas` folder. **Upload the contents of this folder, not the ZIP file alone**, and avoid an unnecessary second nested folder.
2. Install and sign in to [GitHub Desktop](https://desktop.github.com/).
3. In GitHub Desktop choose **File → Add Local Repository → Choose**, and select the extracted `ProfitLeak-Atlas` directory. If asked because it is not a Git repository, use **Create a Repository Here**.
4. Set the local repo name to `ProfitLeak-Atlas`, keep the existing project files (including `README.md` and `.github/workflows/ci.yml`), review the `Changes` tab, then create an initial commit such as `Publish ProfitLeak Atlas portfolio case study`.
5. Click **Publish repository**, choose account `Balbir89`, name `ProfitLeak-Atlas`, and choose **Public** by unticking **Keep this code private**. Publish. This creates `github.com/Balbir89/ProfitLeak-Atlas` if the name is available.
6. Confirm the top level of the published repository contains `README.md`, `src/`, `sql/`, `data/`, `excel/`, `powerbi/`, `dashboard/`, `docs/`, and `.github/`.
7. Open the **Actions** tab and check the `ProfitLeak Atlas Python and SQL CI` workflow. Its run status only becomes verified after GitHub executes it.

Alternative browser method: go to [github.com/new](https://github.com/new) → create a public repo named `ProfitLeak-Atlas` **without initializing a new README** → **Add file → Upload files** → drag the *extracted project content* into the page and commit. GitHub web uploads have limits of 100 files at once and 25 MiB per file, so GitHub Desktop is more dependable for this project.

## B. Turn on an actual public demo

1. Open your published repo on GitHub.
2. Choose **Settings → Pages**.
3. Set **Build and deployment → Source: Deploy from a branch**.
4. Select branch **main**, folder **/docs**, then **Save**.
5. Once GitHub reports successful publication, verify the following links:
   - Executive dashboard: `https://balbir89.github.io/ProfitLeak-Atlas/`
   - Interactive case explorer: `https://balbir89.github.io/ProfitLeak-Atlas/explore.html`
   - Public data-quality pilot: `https://balbir89.github.io/ProfitLeak-Atlas/public-data.html`
6. Return to the main repo and check that the README's demo links now work. Add the executive demo URL to the repository's **About → Website** field.

The executive overview works without JavaScript. The explorer uses JavaScript for filters and the recovery slider. Audit outcomes are managed locally through the workflow CLI. These links will not work **until after** Pages is enabled successfully.

## C. Polish the listing so a recruiter can understand it quickly

**Repository name:** `ProfitLeak-Atlas`

**Description (copy and paste):**

> Financial forensics case study: 220K synthetic payments, explainable leakage detection, case management, Python, SQL, Excel and Power BI source.

**Topics:** `financial-forensics`, `data-analytics`, `sql`, `python`, `excel`, `power-bi`, `procurement`, `risk-analytics`, `audit-analytics`, `portfolio-project`.

**Suggested About website:** `https://balbir89.github.io/ProfitLeak-Atlas/` *(only after it is live)*.

**Pin to profile:** visit `https://github.com/Balbir89` → **Customize your pins** → select ProfitLeak-Atlas → Save.

**Optional LinkedIn / Upwork excerpt:**

> ProfitLeak Atlas is a financial-forensics portfolio case study combining SQL, Python, Excel and Power BI source. It analyzes 220,000 synthetic payment records to identify explainable procurement exceptions and estimate €9.84M of **hypothetical** gross exposure. The solution includes audit case management, scenario analysis, 66 passing tests and a publicly accessible demo dashboard. [Add your live project link.]

## D. Before sharing the URL

- [ ] Opening the repo immediately shows the screenshot and a readable README.
- [ ] Click the executive dashboard link from the README; check numbers appear on mobile.
- [ ] Open the Excel file; verify tabs including Executive, Scenario Lab, Risk Validation and Audit Workflow.
- [ ] Verify the CI job on the actual GitHub Actions page; don't repeat its local result as cloud verified unless green.
- [ ] Verify the 84 offline source checks; **do not** describe them as a Desktop-rendered `.pbix` verification.
- [ ] Review any GitHub secret-scan warnings before sharing.
- [ ] Clearly label the €9.84M as *fictional potential exposure*, not actual savings, discovered fraud or cash recovery.
- [ ] Make sure you personally understand and can reproduce the key methods; reflect your own work honestly.

## E. Common errors

- **Repo only contains one ZIP file:** extract the ZIP and publish the folder contents instead.
- **README image broken:** `README.md` must be at repository root; `docs/images/executive_dashboard_preview.png` must be present at the documented relative path.
- **Live demo gives 404:** enable GitHub Pages from `main` /docs, confirm the repo has exactly the name `ProfitLeak-Atlas`, and wait for the successful Pages deployment status.
- **Phone preview shows dashes instead of amounts:** use the static `/docs/index.html` or the GitHub Pages demo rather than the dynamic HTML file viewer.
- **Power BI won't open on Mac:** Power BI Desktop is a Windows application; the repo provides PBIP source, not a tested native `.pbix`.
- **Large CSV upload fails:** use GitHub Desktop or Git; the largest bundled CSV is about 21 MiB, under GitHub's 25 MiB browser-file limit, but several files make uploads cumbersome.

---

**Important:** A professional-looking project is valuable when its methods, results and limitations are presented accurately. Do not imply the project was developed entirely unaided if that is not accurate.
