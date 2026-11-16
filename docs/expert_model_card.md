# Expert Model Card · ProfitLeak Atlas v2

**Purpose:** Prioritize fictional procurement payment reviews, not predict legal fraud, infer intent, or assess individuals. Financial exposure is estimated solely by explicable contract/invoice SQL rules. The new statistical overlay can increase review priority but cannot create extra monetary loss claims.

**Data:** 220,000 synthetic payment rows; 22 simulated months; 280 vendors. Baseline fits on normal-rule payments in January–December 2025 (91,253 rows). Temporal holdout is January–October 2026. Synthetic seed labels are used only for diagnostics of the original rule engine and are not part of risk-layer predictors.

**Features:** Category log-payment-size robust Z using median and median absolute deviation (MAD), historical vendor exception rate, SQL rule category and heuristic rule confidence. Priority score is bounded to 0–100 with transparent weights. The score is **NOT** a probability and has not been empirically calibrated.

**Evaluation:** The original deterministic injection data produces 100% accuracy by construction; this is explicitly not an honest generalization metric. To challenge the statistical signal separately, a second generator produces 1,500 different synthetic cases: legitimate unusually high payments, subtle injected anomalies, overt anomalies and ordinary payments. At robust Z >4.5 it records 49 TP, 53 FP, 50 FN, 1,348 TN (precision 48.04%, recall 49.49%). These results are only valid for the constructed challenge generation process. No real-world benchmark is provided.

The challenge measures the amount-only screen. It does not measure the combined priority ranking. At the current threshold the statistical screen adds zero new reviews beyond SQL on the 220,000-row release. The separate [settlement benchmark](settlement_validation.md) measures the SQL overpayment rule.

**Drift checks:** Per-category population stability index (PSI) compares training-log payment values with temporal holdout values. PSI measures covariate distribution shift, not model accuracy. See `data/marts/risk_model_validation.json`.

**Failure modes:** Unusual legitimate purchases create false flags; subtle anomaly patterns are often missed; contract effective-date revisions and supplier credits are absent; payment refunds and receipt timing not modeled; vendor history may be affected by data-quality errors; heuristic weights not optimized on independent truth. Reviewing invoice, bank and terms evidence is necessary before any recovery.

**Governance:** Separate financial/control-only issues; zero-euro control-only exposure; cash credits never implied by indicative recoverability; case workflow requires actors, event history and evidence references for verification. Real deployments require access controls, retention, secret management, financial reconciliation, fraud investigations policy and legal review.
