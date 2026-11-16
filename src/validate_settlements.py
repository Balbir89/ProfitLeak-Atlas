"""Exercise production SQL on separately generated synthetic settlement histories."""
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import random
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
INSERT_PAYMENT = '''INSERT INTO fact_payment (
    payment_id,invoice_ref,purchase_order,vendor_id,payment_month,cost_center,quantity,
    billed_unit_price_eur,received_qty,paid_early,discount_taken_pct,fx_spread_pct,
    paid_amount_eur,approval_tier,invoice_authorized_cents
) VALUES (?,?,?,'V1',?,'Finance',1,100,1,0,0,0,?,'Approved',?)'''


def settlement_db():
    conn = sqlite3.connect(':memory:')
    for name in ('01_schema.sql', '02_detection.sql'):
        conn.executescript((ROOT / 'sql' / name).read_text())
    conn.execute("INSERT INTO dim_vendor VALUES ('V1','Sample supplier','Services','Germany','Core')")
    conn.execute("INSERT INTO dim_contract VALUES ('V1','C1',100,0,500,0.005,0.05)")
    return conn


def run(seed=12761, repetitions=150):
    rng = random.Random(seed)
    inputs = []
    truth = {}
    invoice_id = 0
    for _ in range(repetitions):
        face = rng.randrange(5_000, 250_000)
        first = rng.randrange(face // 5, face // 2)
        second = rng.randrange(500, (face - first) // 2)
        extra = rng.randrange(100, face // 5)
        # Truth reflects the simulated obligation and scenario intent. It is never
        # passed to the detector. Unknown authorization is evaluated separately.
        histories = (
            [(face, face, 0)],
            [(first, face, 0), (face - first, face, 0)],
            [(first, face, 0), (second, face, 0), (face - first - second, face, 0)],
            [(face, face, 0), (face, face, face)],
            [(first, face, 0), (face - first + extra, face, extra)],
            [(face, face, 0), (extra, face, extra), (second, face, second)],
            [(first, None, 0), (face - first, None, None)],
            [(first, face, 0), (face - first, face + extra, None)],
        )
        for history in histories:
            invoice_id += 1
            invoice = f'I{invoice_id:06d}'
            for sequence, (payment, authorized, excess) in enumerate(history, 1):
                payment_id = f'{invoice}-{sequence}'
                inputs.append((payment_id, invoice, invoice, f'2026-{sequence:02d}', payment / 100, authorized))
                truth[payment_id] = (excess, payment if sequence > 1 else 0)

    with closing(settlement_db()) as conn:
        conn.executemany(INSERT_PAYMENT, inputs)
        outcomes = list(conn.execute('SELECT payment_id,issue_type,estimated_gross_loss_eur FROM vw_cases'))

    baseline = Counter(tp=0, fp=0, fn=0)
    authorized = Counter(tp=0, fp=0, fn=0)
    unresolved = Counter(reviews=0, exposure_cents=0)
    error_cents = Counter(baseline=0, authorized=0)
    for payment_id, issue, gross in outcomes:
        actual, legacy = truth[payment_id]
        cents = round(gross * 100)
        if actual is None:
            unresolved['reviews'] += issue == 'Invoice repeat review'
            unresolved['exposure_cents'] += cents
            continue
        for counts, prediction in ((baseline, legacy), (authorized, cents)):
            counts['tp'] += prediction > 0 and actual > 0
            counts['fp'] += prediction > 0 and actual == 0
            counts['fn'] += prediction == 0 and actual > 0
        error_cents['baseline'] += abs(legacy - actual)
        error_cents['authorized'] += abs(cents - actual)

    return {
        'method': 'Separate synthetic settlement histories with known invoice obligations',
        'seed': seed,
        'invoices': invoice_id,
        'settlements': len(inputs),
        'known_outcome_settlements': len(inputs) - 2 * repetitions,
        'ambiguous_follow_up_settlements': 2 * repetitions,
        'ambiguous_follow_up_reviews': unresolved['reviews'],
        'ambiguous_exposure_eur': unresolved['exposure_cents'] / 100,
        'repeat_only_baseline': {**baseline, 'absolute_exposure_error_eur': error_cents['baseline'] / 100},
        'authorization_aware_rule': {**authorized, 'absolute_exposure_error_eur': error_cents['authorized'] / 100},
        'scope': 'Targeted invoice settlement checks on simulated data. Real-world false positive rates are unknown.',
    }


if __name__ == '__main__':
    result = json.dumps(run(), indent=2) + '\n'
    (ROOT / 'data/marts/settlement_validation.json').write_text(result, encoding='utf-8')
    print(result, end='')
