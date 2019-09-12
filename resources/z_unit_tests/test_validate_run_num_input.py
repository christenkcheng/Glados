import unittest
import sys
sys.path.insert(0, './..')
import glados

class TestValidateRunNumInput(unittest.TestCase):
    """Test the function '_validate_run_num_input' from
    glados.py
    """

    def test_run_numbers(self):
        """Test that only the valid run numbers are returned
        """
        self.input = ['8161', 'r2d2', '8162', '8163', 'c3p0']
        self.parsed = glados._validate_run_num_input(self.input)
        self.expected = ['8161', '8162', '8163']
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

    def test_plan_numbers(self):
        """Test the run numbers associated with only the valid test plans are returned
        """
        self.input = ['8160', 'darkness', 'awesome']
        self.parsed = glados._validate_run_num_input(self.input)
        self.expected = ['8161', '8162', '8163', '8164']
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

        
    def test_run_and_plan_numbers(self):
        """Test that a unique list of valid test run numbers is returned, even
        if a given test run number is also part of a given test plan number.
        """
        self.input = ['8161', 'r2d2', '8162', '8163', 'c3p0', '8160', 'darkness', 'awesome']
        self.parsed = glados._validate_run_num_input(self.input)
        self.expected = ['8161', '8162', '8163', '8164']
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))
        
    def test_all_invalid(self):
        """Test that all invalid input returns an empty list.
        """
        self.input = ['alderaan', 'kashyyyk', 'hoth', 'mustafar']
        self.parsed = glados._validate_run_num_input(self.input)
        self.expected = []
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

if __name__ == '__main__':
    unittest.main()
