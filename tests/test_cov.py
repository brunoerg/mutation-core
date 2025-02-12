import os
import unittest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.cov import parse_coverage_file


class TestCoverage(unittest.TestCase):
    def test_parse_coverage_file(self):
        res = parse_coverage_file(f'{os.path.dirname(os.path.abspath(__file__))}/total_coverage.info')
        self.assertEqual(res['/Users/fakeuser/projects/bitcoin-core/src/addrdb.cpp'],
                         [31, 95, 97, 99, 100, 102, 107, 110, 117, 131, 132, 133, 134,
                          135, 137, 139, 140, 141, 148, 150, 152, 156, 157, 160, 161,
                          163, 171, 172, 177, 178, 186, 188, 189, 305])

    def test_parse_wrong_coverage_file(self):
        with self.assertRaises(FileNotFoundError):
            parse_coverage_file('total_coverage_fake.info')


if __name__ == '__main__':
    unittest.main()