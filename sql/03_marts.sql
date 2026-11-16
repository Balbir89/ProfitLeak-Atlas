DROP VIEW IF EXISTS mart_monthly;
DROP VIEW IF EXISTS mart_root_causes;
DROP VIEW IF EXISTS mart_vendors;
CREATE VIEW mart_monthly AS
SELECT payment_month,COUNT(*) AS payments,
 ROUND(SUM(paid_amount_eur),2) AS spend_eur,
 SUM(CASE WHEN issue_type<>'No exception' THEN 1 ELSE 0 END) AS flagged_payments,
 ROUND(SUM(estimated_gross_loss_eur),2) AS gross_loss_eur,
 ROUND(SUM(estimated_gross_loss_eur*recovery_probability*(1-recovery_haircut_pct)),2) AS modeled_recovery_eur
FROM vw_cases GROUP BY payment_month ORDER BY payment_month;
CREATE VIEW mart_root_causes AS
SELECT issue_type,COUNT(*) AS flagged_payments,
 ROUND(SUM(estimated_gross_loss_eur),2) AS gross_loss_eur,
 ROUND(SUM(estimated_gross_loss_eur*recovery_probability*(1-recovery_haircut_pct)),2) AS modeled_recovery_eur,
 ROUND(AVG(rule_confidence),3) AS rule_confidence
FROM vw_cases WHERE issue_type<>'No exception' GROUP BY issue_type ORDER BY gross_loss_eur DESC;
CREATE VIEW mart_vendors AS
SELECT vendor_id,vendor_name,country,category,COUNT(*) AS payments,
 ROUND(SUM(paid_amount_eur),2) AS spend_eur,
 SUM(CASE WHEN issue_type<>'No exception' THEN 1 ELSE 0 END) AS flagged_payments,
 ROUND(SUM(estimated_gross_loss_eur),2) AS gross_loss_eur,
 ROUND(SUM(estimated_gross_loss_eur*recovery_probability*(1-recovery_haircut_pct)),2) AS modeled_recovery_eur
FROM vw_cases GROUP BY vendor_id ORDER BY gross_loss_eur DESC;
