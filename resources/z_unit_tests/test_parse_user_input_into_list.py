import unittest
import sys
sys.path.insert(0, './..')
import glados

class ParseUserInputIntoList(unittest.TestCase):
    """Test the function '_parse_user_input_into_list' from
    glados.py
    """

    def test_empty(self):
        """Test that empty input returns an empty list.
        """
        self.input = ''
        self.parsed = glados._parse_user_input_into_list(self.input)
        self.expected = []
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))

    def test_whitespace_and_commas(self):
        """Test that different types of white space or commas act as delimiters.
        """
        self.input = 'a p        b u \t r f, n any, passed blocked, untested retest failed, not_available'
        self.parsed = glados._parse_user_input_into_list(self.input)
        self.expected = ['a', 'p', 'b', 'u', 'r', 'f', 'n', 'any', 'passed', 'blocked', 'untested', 'retest', 'failed', 'not_available']
        self.assertListEqual(sorted(self.parsed), sorted(self.expected))


if __name__ == '__main__':
    unittest.main()
