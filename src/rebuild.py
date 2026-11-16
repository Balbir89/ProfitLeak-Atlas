"""Regenerate the analytical outputs and demos without modifying an investigator's case database."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(script, *arguments):
    subprocess.run([sys.executable, str(ROOT / 'src' / script), *map(str, arguments)],
                   cwd=ROOT, check=True)


def rebuild(rows, seed):
    run('generate_data.py', '--rows', rows, '--seed', seed)
    run('build_pipeline.py')
    run('risk_layer.py')
    run('challenge_suite.py')
    run('validate_settlements.py')
    with tempfile.TemporaryDirectory(prefix='atlas-release-') as folder:
        case_db = Path(folder) / 'case_demo.db'
        run('case_workflow.py', '--db', case_db, 'init')
        run('case_workflow.py', '--db', case_db, 'export')
    run('build_pbip.py')
    run('public_data_validation.py')
    run('verify_powerbi_source.py')
    run('build_dashboard.py')
    run('build_expert_mobile.py')
    run('build_external_validation_page.py')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows', type=int, default=220_000)
    parser.add_argument('--seed', type=int, default=20261115)
    args = parser.parse_args()
    rebuild(args.rows, args.seed)
