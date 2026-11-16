DROP VIEW IF EXISTS vw_cases;
DROP VIEW IF EXISTS vw_detection_rules;
DROP VIEW IF EXISTS vw_enriched;
CREATE VIEW vw_enriched AS
WITH repeated_invoices AS (
 SELECT vendor_id,invoice_ref FROM fact_payment
 GROUP BY vendor_id,invoice_ref HAVING COUNT(*)>1
), invoice_history AS (
 SELECT p.payment_id,
  ROW_NUMBER() OVER chronology AS duplicate_sequence,
  CAST(ROUND(p.paid_amount_eur*100) AS INTEGER) AS settlement_cents,
  SUM(CAST(ROUND(p.paid_amount_eur*100) AS INTEGER)) OVER chronology AS paid_to_date_cents,
  CASE WHEN COUNT(p.invoice_authorized_cents) OVER invoice=COUNT(*) OVER invoice
    AND MIN(p.invoice_authorized_cents) OVER invoice=MAX(p.invoice_authorized_cents) OVER invoice
    THEN MIN(p.invoice_authorized_cents) OVER invoice END AS authorized_cents
 FROM repeated_invoices r JOIN fact_payment p USING(vendor_id,invoice_ref)
 WINDOW invoice AS (PARTITION BY p.vendor_id,p.invoice_ref),
  chronology AS (invoice ORDER BY p.payment_month,p.payment_id ROWS UNBOUNDED PRECEDING)
), approval_candidates AS (
 SELECT DISTINCT vendor_id,purchase_order FROM fact_payment WHERE approval_tier='Unapproved'
), purchase_totals AS (
 SELECT a.vendor_id,a.purchase_order,COUNT(*) AS po_payment_count,SUM(p.paid_amount_eur) AS po_paid_total_eur
 FROM approval_candidates a JOIN fact_payment p USING(vendor_id,purchase_order)
 GROUP BY a.vendor_id,a.purchase_order
)
SELECT p.*, v.vendor_name,v.category,v.country,v.vendor_tier,
 c.contract_id,c.contract_unit_price_eur,c.early_discount_pct,c.approval_threshold_eur,
 c.allowed_fx_spread_pct,c.recovery_haircut_pct,
 h.duplicate_sequence,h.authorized_cents,h.paid_to_date_cents,
 CASE WHEN h.duplicate_sequence>1 AND h.authorized_cents IS NOT NULL
  THEN MIN(h.settlement_cents,MAX(0,h.paid_to_date_cents-h.authorized_cents)) ELSE 0 END AS repeat_exposure_cents,
 a.po_payment_count,a.po_paid_total_eur
FROM fact_payment p JOIN dim_vendor v USING(vendor_id)
 JOIN dim_contract c USING(vendor_id)
 LEFT JOIN invoice_history h ON h.payment_id=p.payment_id
 LEFT JOIN purchase_totals a ON a.vendor_id=p.vendor_id AND a.purchase_order=p.purchase_order;

CREATE VIEW vw_detection_rules AS
SELECT e.*,
 CASE
  WHEN repeat_exposure_cents>0 THEN 'Duplicate payment'
  WHEN received_qty=0 AND paid_amount_eur>0 THEN 'Undelivered goods'
  WHEN billed_unit_price_eur>contract_unit_price_eur*1.045 THEN 'Contract price variance'
  WHEN paid_early=1 AND discount_taken_pct+0.0001<early_discount_pct THEN 'Missed early discount'
  WHEN fx_spread_pct>allowed_fx_spread_pct+0.015 THEN 'FX spread excess'
  WHEN duplicate_sequence>1 AND authorized_cents IS NULL THEN 'Invoice repeat review'
  WHEN po_payment_count>=2 AND po_paid_total_eur>approval_threshold_eur
       AND paid_amount_eur<approval_threshold_eur AND approval_tier='Unapproved'
       THEN 'Approval fragmentation'
  ELSE 'No exception'
 END AS issue_type
FROM vw_enriched e;

CREATE VIEW vw_cases AS
SELECT d.*,
 ROUND(CASE issue_type
  WHEN 'Duplicate payment' THEN repeat_exposure_cents/100.0
  WHEN 'Undelivered goods' THEN paid_amount_eur
  WHEN 'Contract price variance' THEN MAX(0,(billed_unit_price_eur-contract_unit_price_eur)*quantity)
  WHEN 'Missed early discount' THEN MAX(0,quantity*billed_unit_price_eur*(early_discount_pct-discount_taken_pct))
  WHEN 'FX spread excess' THEN MAX(0,quantity*billed_unit_price_eur*(1-discount_taken_pct)*(fx_spread_pct-allowed_fx_spread_pct))
  ELSE 0 END,2) AS estimated_gross_loss_eur,
 CASE issue_type
  WHEN 'Duplicate payment' THEN 0.9
  WHEN 'Undelivered goods' THEN 0.7
  WHEN 'Contract price variance' THEN 0.55
  WHEN 'Missed early discount' THEN 0.3
  WHEN 'FX spread excess' THEN 0.65
  ELSE 0 END AS recovery_probability,
 CASE issue_type
  WHEN 'Duplicate payment' THEN 0.98
  WHEN 'Undelivered goods' THEN 0.94
  WHEN 'Contract price variance' THEN 0.88
  WHEN 'Missed early discount' THEN 0.78
  WHEN 'FX spread excess' THEN 0.83
  WHEN 'Approval fragmentation' THEN 0.65
  WHEN 'Invoice repeat review' THEN 0.55
  ELSE 0 END AS rule_confidence,
 CASE issue_type
  WHEN 'Duplicate payment' THEN 'Reconcile authorized invoice total, installments and bank settlements'
  WHEN 'Undelivered goods' THEN 'Obtain goods-receipt proof; dispute unfulfilled charge'
  WHEN 'Contract price variance' THEN 'Compare effective contract revision and invoice line'
  WHEN 'Missed early discount' THEN 'Verify payment date, discount eligibility, and terms'
  WHEN 'FX spread excess' THEN 'Inspect bank FX pricing and supplier currency terms'
  WHEN 'Approval fragmentation' THEN 'Review purchase-order approval trail; no loss presumed'
  WHEN 'Invoice repeat review' THEN 'Obtain consistent invoice authorization and reconcile installments'
  ELSE 'No action' END AS recommended_action
FROM vw_detection_rules d;
