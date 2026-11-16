import json
from html.parser import HTMLParser
from pathlib import Path
import unittest
from xml.etree import ElementTree
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


class ProjectPage(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.payload = None
        self.reading_payload = False
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'script' and attrs.get('id') == 'payload':
            self.reading_payload = True

    def handle_data(self, data):
        if self.reading_payload:
            self.payload = json.loads(data)

    def handle_endtag(self, tag):
        if tag == 'script':
            self.reading_payload = False


class TestReleaseArtifacts(unittest.TestCase):
    def setUp(self):
        self.metrics = json.loads((ROOT / 'data/marts/metrics.json').read_text())

    def test_public_navigation_has_all_three_demos(self):
        docs = ROOT / 'docs'
        self.assertEqual(ProjectPage(docs / 'index.html').links, ['explore.html', 'public-data.html'])
        for name in ('explore.html', 'public-data.html'):
            self.assertIn('index.html', ProjectPage(docs / name).links)

    def test_explorer_uses_current_outputs(self):
        for path in ('docs/explore.html', 'dashboard/atlas_executive.html'):
            payload = ProjectPage(ROOT / path).payload
            self.assertEqual(payload['metrics'], self.metrics)
            self.assertAlmostEqual(sum(float(m['gross_loss_eur']) for m in payload['monthly']),
                                   self.metrics['gross_estimated_loss_eur'], delta=0.12)

    def test_static_snapshot_uses_current_data(self):
        settlement = json.loads((ROOT / 'data/marts/settlement_validation.json').read_text())
        for path in ('docs/index.html', 'dashboard/ProfitLeak_Atlas_Expert_iPhone.html'):
            content = (ROOT / path).read_text()
            self.assertIn(f"{self.metrics['payments']:,}", content)
            self.assertIn(f"{settlement['settlements']:,} separately simulated settlements", content)

    def test_workbook_snapshot_reconciles_to_full_release(self):
        if self.metrics['payments'] != 220_000:
            self.skipTest('Excel is the checked-in, full-size release snapshot')
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        with ZipFile(ROOT / 'excel/ProfitLeak_Atlas_Expert.xlsx') as workbook:
            root = ElementTree.fromstring(workbook.read('xl/worksheets/sheet1.xml'))
        for cell, key in [('A7', 'spend_eur'), ('F7', 'gross_estimated_loss_eur'),
                          ('K7', 'modeled_recoverable_eur')]:
            value = root.find(f'.//main:c[@r="{cell}"]/main:v', ns)
            self.assertAlmostEqual(float(value.text), self.metrics[key], delta=0.01)
