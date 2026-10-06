import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'configuration', Path(__file__).parents[1] / 'supvan_t50pro/configuration.py'
)
configuration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configuration)


class ConfigurationTests(unittest.TestCase):
    def load(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'printers.json'
            path.write_text(json.dumps(data))
            return configuration.load_printers(path)

    def test_multiple_independent_entries(self):
        printers = [
            {'id': 'supvan-workbench', 'name': '工作台', 'uri': 'ipp://one.local:8631/ipp/print/a'},
            {'id': 'supvan-storage', 'name': '储物间', 'uri': 'ipp://two.local:8631/ipp/print/b'},
        ]
        self.assertEqual(self.load(printers), printers)

    def test_invalid_configuration_is_rejected(self):
        valid = {'id': 'supvan-one', 'name': '工作台', 'uri': 'ipp://one.local/ipp/print/a'}
        cases = [[], {}, [valid, valid], [{**valid, 'id': 'BAD ID'}],
                 [{**valid, 'name': ''}], [{**valid, 'uri': 'http://one.local'}],
                 [{**valid, 'uri': None}], ['printer']]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.load(data)

    def test_missing_explicit_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                configuration.load_printers(Path(directory) / 'missing.json')


if __name__ == '__main__':
    unittest.main()
