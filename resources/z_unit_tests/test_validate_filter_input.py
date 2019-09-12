import unittest
import sys
sys.path.insert(0, './..')
import glados
import testrail_api_glados

class TestValidateFilterInput(unittest.TestCase):
    """Test the function '__validate_filter_input' from
    glados.py
    """

    VALID_FILTER_IDS = testrail_api_glados.get_status_dictionary()

    def test_all_keys(self):
        """Test that input of all keys returns unique keys.
        """
        self.input = ['a', 'p', 'b', 'u', 'r', 'f', 'n']
        self.parsed = glados._validate_filter_input(self.input)
        self.expected = list(self.VALID_FILTER_IDS.keys())
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

    def test_all_values(self):
        """Test that input of all key-values returns unique corresponding keys.
        """
        self.input = ['any', 'passed', 'blocked', 'untested', 'retest', 'failed', 'not_available']
        self.parsed = glados._validate_filter_input(self.input)
        self.expected = list(self.VALID_FILTER_IDS.keys())
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

    def test_keys_and_values(self):
        """Test that input of keys and key-values returns unique corresponding keys.
        """
        self.input = ['a', 'p', 'b', 'u', 'r', 'f', 'n', 'any', 'passed', 'blocked', 'untested', 'retest', 'failed', 'not_available']
        self.parsed = glados._validate_filter_input(self.input)
        self.expected = list(self.VALID_FILTER_IDS.keys())
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

    def test_empty(self):
        """Test that empty input returns an empty list.
        """
        self.input = ['']
        self.parsed = glados._validate_filter_input(self.input)
        self.expected = []
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

    def test_garbage(self):
        """Test that input that contains no valid matches returns an empty list.
        """
        self.input = ['hotdog', 'burger', 'pizza', 'pineapple', 'crab', 'cup']
        self.parsed = glados._validate_filter_input(self.input)
        self.expected = []
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

    def test_mixed_garbage(self):
        """Test that input that contains invalid and valid matches only returns valid
        unique corresponding keys.
        """
        self.input = ['hotdog', 'a', 'burger', 'p', 'b', 'pizza', ',', 'untested', 'pineapple', 'retest', 'crab', 'failed', 'n', 'any', 'cup']
        self.parsed = glados._validate_filter_input(self.input)
        self.expected = list(self.VALID_FILTER_IDS.keys())
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

    def test_case_sensitivity(self):
        """Test that the matching to valid keys or key-values is case insensitive.
        """
        self.input = ['A', 'p', 'b', 'u', 'r', 'f', 'n', 'any', 'paSsEd', 'blocked', 'UNTESTED', 'retest', 'failed', 'not_avaiLablE']
        self.parsed = glados._validate_filter_input(self.input)
        self.expected = list(self.VALID_FILTER_IDS.keys())
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))


if __name__ == '__main__':
    unittest.main()
