PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS dim_vendor (
 vendor_id TEXT PRIMARY KEY, vendor_name TEXT NOT NULL, category TEXT NOT NULL,
 country TEXT NOT NULL, vendor_tier TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_contract (
 vendor_id TEXT PRIMARY KEY REFERENCES dim_vendor(vendor_id), contract_id TEXT NOT NULL,
 contract_unit_price_eur REAL NOT NULL, early_discount_pct REAL NOT NULL,
 approval_threshold_eur REAL NOT NULL, allowed_fx_spread_pct REAL NOT NULL,
 recovery_haircut_pct REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_payment (
 payment_id TEXT PRIMARY KEY, invoice_ref TEXT NOT NULL, purchase_order TEXT NOT NULL,
 vendor_id TEXT NOT NULL REFERENCES dim_vendor(vendor_id),payment_month TEXT NOT NULL,
 cost_center TEXT NOT NULL,quantity INTEGER NOT NULL,billed_unit_price_eur REAL NOT NULL,
 received_qty INTEGER NOT NULL,paid_early INTEGER NOT NULL,discount_taken_pct REAL NOT NULL,
 fx_spread_pct REAL NOT NULL,paid_amount_eur REAL NOT NULL,approval_tier TEXT NOT NULL,
 invoice_authorized_cents INTEGER CHECK(invoice_authorized_cents>0)
);
CREATE INDEX IF NOT EXISTS idx_payment_vendor_invoice ON fact_payment(vendor_id,invoice_ref);
CREATE INDEX IF NOT EXISTS idx_payment_po ON fact_payment(vendor_id,purchase_order);
CREATE INDEX IF NOT EXISTS idx_payment_unapproved_po ON fact_payment(vendor_id,purchase_order)
 WHERE approval_tier='Unapproved';
CREATE INDEX IF NOT EXISTS idx_payment_month ON fact_payment(payment_month);
