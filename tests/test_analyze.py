import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyze import get_command_to_kill

class TestAnalyze(unittest.TestCase):
    def test_get_command_to_kill(self):
        files_and_command = {
            'src/wallet/test/coinselector_tests.cpp': 'cmake --build build && ./build/src/test/test_bitcoin --run_test=coinselector_tests',
            'src/net_processing.cpp': 'cmake --build build && ./build/src/test/test_bitcoin && CI_FAILFAST_TEST_LEAVE_DANGLING=1 ./build/test/functional/test_runner.py -F',
            'test/functional/feature_addrman.py': './build/test/functional/feature_addrman.py'
        }
        for files, command in files_and_command.items():
            self.assertEqual(get_command_to_kill(files, jobs=0), command)


if __name__ == '__main__':
    unittest.main()