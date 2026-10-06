"""Ensure bad SAT evidence cannot be accepted as a checked coloring."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from check_model import check


class ModelEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.graph = self.root/'graph.json'
        self.cnf = self.root/'input.cnf'
        self.model = self.root/'model.log'
        self.graph.write_text(json.dumps(dict(vertices=[[0]*8, [1]*8], edges=[[0, 1]])))
        self.base = 'p cnf 4 6\n1 2 0\n-1 -2 0\n3 4 0\n-3 -4 0\n-1 -3 0\n-2 -4 0\n'
        self.cnf.write_text(self.base)
        self.model.write_text('s SATISFIABLE\nv 1 -2 -3 4 0\n')

    def tearDown(self):
        self.temp.cleanup()

    def verify(self):
        return check(self.graph, 2, self.model, self.cnf)

    def test_valid(self):
        self.assertEqual(self.verify(), ([1, 2], 6))

    def test_monochromatic(self):
        self.model.write_text('v 1 -2 3 -4 0\n')
        with self.assertRaises(ValueError):
            self.verify()

    def test_extra_unit_is_checked(self):
        self.cnf.write_text(self.base.replace('4 6', '4 7')+'-1 0\n')
        with self.assertRaises(ValueError):
            self.verify()

    def test_missing_variable(self):
        self.model.write_text('v 1 -2 -3 0\n')
        with self.assertRaises(ValueError):
            self.verify()

    def test_contradictory_literals(self):
        self.model.write_text('v 1 -2 -3 4 -1 0\n')
        with self.assertRaises(ValueError):
            self.verify()

    def test_bad_clause_count(self):
        self.cnf.write_text(self.base.replace('4 6', '4 5'))
        with self.assertRaises(ValueError):
            self.verify()

    def test_graph_is_checked_independently(self):
        self.cnf.write_text('p cnf 4 4\n1 2 0\n-1 -2 0\n3 4 0\n-3 -4 0\n')
        self.model.write_text('v 1 -2 3 -4 0\n')
        with self.assertRaises(ValueError):
            self.verify()


if __name__ == '__main__':
    unittest.main()
