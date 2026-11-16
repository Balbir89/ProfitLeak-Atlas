-- All queries should return zero for a passing dataset.
SELECT 'orphan_vendor' AS test, COUNT(*) AS failures FROM fact_payment p LEFT JOIN dim_vendor v USING(vendor_id) WHERE v.vendor_id IS NULL;
SELECT 'orphan_contract' AS test, COUNT(*) AS failures FROM fact_payment p LEFT JOIN dim_contract c USING(vendor_id) WHERE c.vendor_id IS NULL;
SELECT 'non_positive_paid' AS test, COUNT(*) AS failures FROM fact_payment WHERE paid_amount_eur<=0;
SELECT 'negative_loss' AS test, COUNT(*) AS failures FROM vw_cases WHERE estimated_gross_loss_eur <0;
