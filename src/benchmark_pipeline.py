"""Benchmark equivalent core builds in alternating order on the same machine."""
import argparse
import json
from pathlib import Path
import platform
import sqlite3
from statistics import median
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
FINANCIAL_FIELDS = ('payments', 'spend_eur', 'gross_estimated_loss_eur',
                    'modeled_recoverable_eur', 'flagged_payments')


def benchmark(projects, runs):
    elapsed = {name: [] for name in projects}
    totals = {}
    for index in range(runs):
        order = list(projects) if index % 2 == 0 else list(reversed(projects))
        for name in order:
            project = projects[name]
            started = perf_counter()
            subprocess.run([sys.executable, 'src/build_pipeline.py'], cwd=project,
                           check=True, stdout=subprocess.DEVNULL)
            elapsed[name].append(perf_counter() - started)
            metrics = json.loads((project / 'data/marts/metrics.json').read_text())
            observation = {field: metrics[field] for field in FINANCIAL_FIELDS}
            if name in totals and totals[name] != observation:
                raise RuntimeError(f'Financial outputs varied across {name} runs')
            totals[name] = observation
    if len(totals) == 2 and totals['baseline'] != totals['current']:
        raise RuntimeError('Benchmark versions produced different financial totals')
    return {
        'scope': 'Core SQLite build from pre-generated CSV through financial marts; excludes generation and risk scoring',
        'environment': {'platform': platform.system(), 'machine': platform.machine(),
                        'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version},
        'totals': totals['current'],
        'duration_seconds': {name: {'runs': [round(t, 3) for t in values],
                                     'median': round(median(values), 3)}
                             for name, values in elapsed.items()},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, help='Original extracted project with equivalent input CSVs')
    parser.add_argument('--runs', type=int, default=3)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error('--runs must be positive')
    projects = {'current': ROOT}
    if args.baseline is not None:
        projects = {'baseline': args.baseline.resolve(), **projects}
    print(json.dumps(benchmark(projects, args.runs), indent=2))
