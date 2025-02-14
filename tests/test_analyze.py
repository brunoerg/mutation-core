import unittest
import tempfile
import os
import shutil
from src.analyze import analyze
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
    def setUp(self):
        """Set up test environment with temporary directory and files"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create original_file.txt with target path
        self.target_file_path = os.path.join(self.test_dir, "test/functional/feature_addrman.py")
        with open(os.path.join(self.test_dir, "original_file.txt"), "w") as f:
            f.write(self.target_file_path)
        
        # Create directory structure if needed
        os.makedirs(os.path.dirname(self.target_file_path), exist_ok=True)
        
        # Create mock target file
        with open(self.target_file_path, "w") as f:
            f.write("# Original content")

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_normal_execution(self):
        """Test normal execution where mutants are analyzed"""
        # Create test mutant files
        mutant_contents = {
            "mutant1.py": "# Mutant 1 content",
            "mutant2.py": "# Mutant 2 content",
            "mutant3.py": "# Mutant 3 content",
            "mutant4.py": "# Mutant 4 content",
            "mutant5.py": "# Mutant 5 content",
            "mutant6.py": "# Mutant 6 content",
            "mutant7.py": "# Mutant 7 content",
            "mutant8.py": "# Mutant 8 content",
            "mutant9.py": "# Mutant 9 content",
            "mutant10.py": "# Mutant 10 content"
        }
        
        for name, content in mutant_contents.items():
            with open(os.path.join(self.test_dir, name), "w") as f:
                f.write(content)

        # Run analysis with a simple command that always "kills" mutants
        killed, not_killed = analyze(
            self.test_dir,
            command="exit 1",  # Command that always fails, thus "killing" mutants
            timeout=10,
            survival_threshold=0.3
        )
        
        self.assertEqual(len(killed), 10)
        self.assertEqual(len(not_killed), 0)

    def test_early_termination(self):
        """Test early termination with high survival rate"""
        # Create test mutant files
        mutant_contents = {
            "mutant1.py": "# Mutant 1 content",
            "mutant2.py": "# Mutant 2 content",
            "mutant3.py": "# Mutant 3 content",
            "mutant4.py": "# Mutant 4 content",
            "mutant5.py": "# Mutant 5 content",
            "mutant6.py": "# Mutant 6 content",
            "mutant7.py": "# Mutant 7 content",
            "mutant8.py": "# Mutant 8 content",
            "mutant9.py": "# Mutant 9 content",
            "mutant10.py": "# Mutant 10 content"
        }
        
        for name, content in mutant_contents.items():
            with open(os.path.join(self.test_dir, name), "w") as f:
                f.write(content)

        # Run analysis with a command that always "survives"
        killed, not_killed = analyze(
            self.test_dir,
            command="exit 0",  # Command that always succeeds, thus mutants "survive"
            timeout=1,
            survival_threshold=0.3,
        )
        
        self.assertLess(len(killed), len(mutant_contents))
        self.assertGreater(len(not_killed), 0)

    def test_empty_folder(self):
        """Test behavior with empty input directory"""
        with self.assertRaises(Exception) as context:
            analyze(self.test_dir)

        self.assertEqual(
           str(context.exception),
            f'No mutants on the provided folder path ({self.test_dir})'
        )

if __name__ == '__main__':
    unittest.main()