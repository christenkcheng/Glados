import unittest
import sys
sys.path.insert(0, './..')
import testrail_api_glados

class TestInformationFromTestrail(unittest.TestCase):
    """Test functions that return information about TestRail fields from
    testrail_api_glados.py
    
    Primary goal is to find out when the dictionaries returned from TestRail
    change.
    """
    
    def test_browser_info(self):
        """Test that expected browsers and their ids, have not changed from TestRail.
        """
        self.current_browsers = testrail_api_glados.get_browsers()

        # Mappings as of 10/20/2014
        self.expected_browsers = {
            '0': 'Other',
            '1': 'Internet Explorer',
            '2': 'FireFox',
            '3': 'Chrome',
            '4': 'Safari',
            '5': 'Opera',
            '6': 'Webkit'
        }
        
        self.maxDiff = None
        self.assertDictEqual(self.expected_browsers, self.current_browsers)
        
    def test_environment_info(self):
        """Test that expected test environments and their ids, have not changed from TestRail.
        """
        self.current_environments = testrail_api_glados.get_test_environments()

        # Mappings as of 10/20/14
        self.expected_environments = {
            '0': 'Production',
            '1': 'Staging',
            '2': 'QA',
            '3': 'Dev',
            '4': 'Other'
        }
        
        self.maxDiff = None
        self.assertDictEqual(self.expected_environments, self.current_environments)
        
    def test_test_status_info(self):
        """Test that expected test statuses and their ids, have not changed from TestRail.
        """
        self.current_statuses = testrail_api_glados.get_status_dictionary()
        
        # Mappings as of 10/20/14
        self.expected_statuses = {
            '1': 'passed',
            '2': 'blocked',
            '3': 'untested',
            '4': 'retest',
            '5': 'failed',
            '6': 'not_applicable'
        }
        
        self.maxDiff = None
        self.assertDictEqual(self.expected_statuses, self.current_statuses)
        
    def test_test_category_info(self):
        """Test that expected test categories and their ids, have not changed from TestRail.
        """
        self.current_categories = testrail_api_glados.get_test_categories()

        # Mappings as of 10/20/14
        self.expected_categories = {
            '0': 'No Label',
            '1': 'Smoke Test',
            '3': 'Compatibility',
            '4': 'Data/Content',
            '5': 'Design/UI',
            '6': 'Functional',
            '7': 'Logic',
            '8': 'Performance',
            '9': 'Security',
            '10': 'SEO',
            '11': 'User Scenarios',
            '12': 'Tracking Code/Metrics',
            '13': 'Light Regression'
        }
        self.maxDiff = None
        self.assertDictEqual(self.expected_categories, self.current_categories)

if __name__ == '__main__':
    unittest.main()