"""GLaDOS specific Python functions to interact with Testrail
using the Testrail API.
"""

from __future__ import print_function
from __future__ import absolute_import
from builtins import str
import re
import pprint
import sys
import os

if sys.version_info < (3,0):
    from testrail_py2 import APIClient, APIError
else:
    from testrail_py3 import APIClient, APIError

client = APIClient('https://testrail.internetbrands.com/testrail/')
client.user = 'qatest@internetbrands.com'
client.password = '909SepulvedaApiUser'
project_id = 1  # project 1 is Auto E-Commerce

# TestRail Information
def get_users():
    """Returns a a list of dictionaries. Each dictionary is a user.
    Dictionary keys are:
        email
        id
        is_active
        name
    """
    request = 'get_users/'
    result = client.send_get(request)
    return result
    
def get_result_fields():
    """Returns a list of available test result custom fields.
    """
    request = 'get_result_fields'
    result = client.send_get(request)
    return result
    
def get_browsers():
    """Returns a dictionary of the browsers TestRail allows a user
    to set in a test result.
    Key is a browser's TestRail ID, as a string
    Value is the name of the browser from by TestRail.
    """
    result_fields = get_result_fields()
    browser_field = {}
    browsers = {}
    # Check the result fields for the browser field
    for result_field in result_fields:
        if result_field['system_name'] == 'custom_browser':
            browser_field = result_field
            # The browsers are stored as a string, so we need to parse them out into a list
            browsers_string = browser_field['configs'][0]['options']['items']
            browsers_list = browsers_string.split('\n')
            for browser in browsers_list:
                key_value_pair = browser.split(',')
                browsers[key_value_pair[0]] = key_value_pair[1]
            break
    else:
        print("Browsers could not be obtained from TestRail.")
    return browsers
    
def get_test_environments():
    """Returns a dictionary of the custom test environments
    TestRail allows a user to set in a test result.
    Key is an environment's TestRail ID, as a string.
    Value is the name of the environment from by TestRail.
    """
    result_fields = get_result_fields()
    test_env_field = {}
    test_envs = {}
    for result_field in result_fields:
        if result_field['system_name'] == 'custom_test_env':
            test_env_field = result_field
            # The environments are stored as a string, so we need to parse them out into a list
            test_env_string = test_env_field['configs'][0]['options']['items']
            test_env_list = test_env_string.split('\n')
            for test_env in test_env_list:
                key_value_pair = test_env.split(',')
                test_envs[key_value_pair[0]] = key_value_pair[1]
            break
    else:
        print("Test environments could not be obtained from TestRail.")
    return test_envs
    
def get_statuses():
    """Returns a list of dictionaries about available test statuses.
    This returns more information than needed
    (just want test status id, and the name of the status)
    Created function, get_status_dictionary to return just that
    """
    request = 'get_statuses'
    result = client.send_get(request)
    return result
    
def get_status_dictionary():
    """Returns a dictionary where a key is a test status' TestRail ID, as a string
    and a value is the name of the test status from by TestRail.
    """
    status_dict = {}
    for status in get_statuses():
        status_dict[str(status['id'])] = status['name']
    return status_dict
    
def get_case_fields():
    """Returns a list of available test case custom fields.
    This returns more information than needed.
    Created function, get_test_categories, that returns just
    a test category and its TestRail ID.
    """
    request = 'get_case_fields'
    result = client.send_get(request)
    return result
    
def get_test_categories():
    """Returns a dictionary of the custom test categories
    TestRail allows a user to classify tests as.
    Key is the test category's TestRail ID, as a string.
    Value is the name of the test category from TestRail.
    """
    case_fields = get_case_fields()
    # case_fields is a list of dictionaries, each dictionary corresponds to a custom category
    # since these can change, go through each dictionary and check if it is the one for test categories
    test_category_field = {}
    test_categories = {}
    for field in case_fields:
        if field['system_name'] == 'custom_test_category':
            test_category_field = field
            categories_string = test_category_field['configs'][0]['options']['items']
            categories_list = categories_string.split('\n')
            for category in categories_list:
                key_value = category.split(',')
                test_categories[str(int(key_value[0]))] = key_value[1] # Explanation: String shows, 0004, but when we need the ID to check, it has to be a string of, '4'.
            break
    else:
        print("Test categories could not be obtained from TestRail.")
    return test_categories
    
# Interpreter Functions (Extract usable TestRail compatible info from inputs)
def normalize_input_string(input):
    """Performs following actions on input, then returns the input:
    - make all characters lowercase
    - strip leading and trailing whitespace
    - replace underscores with spaces
    - substitute one or more whitespaces with a space
    """
    input = input.lower().strip()
    input = input.replace('_', ' ')
    input = re.sub(r'\s+', ' ', input)
    return input
    
def map_browser_to_testrail(browser):
    """Given a browser, try and match it to a browser that TestRail
    recognizes. Return the browser's TestRail ID if a match is found
    Otherwise, return the browser ID TestRail uses for 'Other'.
    """
    # Cleanse the browser interpret
    browser = normalize_input_string(browser)
    # Browser aliases (using aliases from Robot Framework's documentation)
    aliases = [
        ('firefox', ['ff']),
        ('chrome', ['googlechrome', 'google chrome']),
        ('internet explorer', ['internetexplorer', 'ie'])
    ]
    # Run our own interpretation for specific browsers before comparing with TestRail
    for alias in aliases:
        if browser in alias[1]:
            browser = alias[0]
            break
    # Check if browser matches anything from TestRail
    for key, value in list(get_browsers().items()):
        if browser == value.lower() or browser == key:
            browser = key
            break
    else:
        browser = '0' # 0 == 'Other'
    return browser
    
def map_test_env_to_testrail(test_env):
    """Given a test environment, try and match it to a test environment that TestRail
    recognizes. If nothing matches then mark it with TestRail's test environment option, Other.
    Returns the corresponding test environment id TestRail uses.
    """
    # Cleanse test_env input
    test_env = normalize_input_string(test_env)
    # Environment aliases
    aliases = [
        ('production', ['prod', 'prd', 'www', 'preprd2', 'preprd3', 'preprd4']),
        ('staging', ['stg', 'stage', 'staging', 'stg1', 'stg2', 'stg3', 'stg4', 'stg5', 'stg6', 'stg7', 'stg8', 'stg9', 'stg10']),
        ('qa', ['qatest', 'quality assurance', 'qualityassurance', 'bf', 'bug fixes', 'bugfixes', 'bug fix', 'bugfix', 'qa1']),
        ('dev', ['developer'])
    ]
    # Check if any aliases match
    for alias in aliases:
        if test_env in alias[1]:
            test_env = alias[0]
            break
    # Check if test environment matches anything from TestRail
    for key, value in list(get_test_environments().items()):
        if test_env == value.lower() or test_env == key:
            test_env = key
            break
    else:
        test_env = '4' # 4 == 'Other'
    return test_env
    
def map_test_status_to_testrail(test_status):
    """Given a test status, try and match it to a test status that TestRail
    recognizes. If nothing matches then leave it as is
    Returns the corresponding test environment id TestRail uses.
    """
    # Cleanse Input
    test_status = normalize_input_string(test_status)
    # Test Status Aliases
    aliases = [
        ('passed', ['p', 'pass']),
        ('blocked', ['b', 'block']),
        ('untested', ['u', 'untest']),
        ('retest', ['r']),
        ('failed', ['f', 'fail']),
        ('not_applicable', ['n', 'n/a', 'na', 'not applicable', 'notapplicable'])
    ]
    # Check if it Matches an Alias
    for alias in aliases:
        if test_status in alias[1]:
            test_status = alias[0]
            break
    # Return the Status ID if matched
    for key, value in list(get_status_dictionary().items()):
        if test_status == value.lower():
            test_status = key
            break
    return test_status
    
def map_test_category_to_testrail(category):
    """Given a test category, try and match it to a test category that TestRail
    recognizes.  If nothing matches then return the input.
    Returns the corresponding test category ID TestRail uses.
    """
    # Cleanse Input
    category = normalize_input_string(category)
    # Test Category Aliases
    aliases = [
        ('no label', ['nolabel']),
        ('smoke test', ['smoketest']),
        ('compatibility', []),
        ('data/content', ['data content', 'datacontent', 'data', 'content']),
        ('design/ui', ['design ui', 'designui', 'design', 'ui']),
        ('functional', []),
        ('logic', []),
        ('performance', []),
        ('security', []),
        ('seo', []),
        ('user scenarios', ['userscenarios']),
        ('tracking code/metrics', ['trackingcodemetrics', 'tracking code metrics', 'tracking code', 'tracking', 'metrics']),
        ('light regression', ['lightregression'])
    ]
    # Check if it Matches an Alias
    for alias in aliases:
        if category in alias[1]:
            category = alias[0]
            break
    # Return the Status ID if matched
    for key, value in list(get_test_categories().items()):
        if category == value.lower():
            category = key
            break
    return category
    
# Results
def add_test_result(run_id, case_id, status_id, comment='No comments.', elapsed='', browser='', browser_version='', environment=''):
    """Given a test run ID, test case ID, and status ID,
    updates the corresponding test case in the given run with
    the status ID.
    Optional Arguments:
    - comment: sets a comment in the test result
    - elapsed: sets the given number as the elapsed time in seconds, in the test result
    - browser: sets the browser used in the test result
    - browser_version: sets the browser version in the test result
    - environment: sets the environment in the test result
    """
    # Format elapsed time
    elapsed = str(elapsed) + 's'
    # Map browser to TestRail number
    browser = map_browser_to_testrail(browser)
    # Map environment to TestRail number
    environment = map_test_env_to_testrail(environment)
    field_dict = {
        'status_id': status_id,
        'comment': comment,
        'elapsed': elapsed,
        'custom_browser': browser,
        'custom_browser_version': browser_version,
        'custom_test_env': environment,
    }
    result = client.send_post('add_result_for_case/' + str(run_id) + '/' + str(case_id), field_dict)
    return(result)
    
def get_manually_tested_final_results(run_id):
    tests = client.send_get("get_results_for_run/" + str(run_id))
    final_tests = {}
    manually_tested_results = []
    #Stores latest result of each test into a dictionary with the test number as a key, and user it was ran by, status, and ran date as a list of values
    #Logic: if the test doesn't exist in the dictionary "final_tests", then add it. Otherwise, check if current result is more recent and if so, update it
    for test in tests:
        if test['test_id'] not in final_tests:
            final_tests[test['test_id']] = [test['created_by'], test['status_id'], test['created_on']]
        else:
            if test['created_on'] > final_tests[test['test_id']][2]:
                final_tests[test['test_id']] = [test['created_by'], test['status_id'], test['created_on']]
            
    #Copy all final entries not by api user (user 42)
    for test in final_tests:
        if final_tests[test][0] != 42:
            manually_tested_results.append(test)
             
    return manually_tested_results
    
# Cases
def get_test_case(case_id):
    """Given a test case ID, returns a Python dictionary with information of
    the case
    """
    result = client.send_get('get_case/' + str(case_id))
    return(result)
    
def get_test_cases(suite_id, section_id=''):
    """Given a project ID (assumed to be Auto E-Com; change above), a suite ID,
    and a section ID (optional), returns a list of Python dictionaries for each
    case in the suite
    """
    request = 'get_cases/' + str(project_id) + '&suite_id=' + str(suite_id) +\
            '&section_id=' + str(section_id)
    result = client.send_get(request)
    return(result)
    
# Tests
def get_test(test_id):
    """Given a test_id, return a Python dictionary with information about the
    test (NOT results of the test)
    """
    request = 'get_test/' + str(test_id)
    result = client.send_get(request)
    return(result)
    
def get_tests(run_id):
    """Given a test run ID, returns a list of dictionaries for each test in the
    run as would be returned from get_test()
    """
    request = 'get_tests/' + str(run_id)
    result = client.send_get(request)
    return(result)
    
# Runs
def get_run(run_id):
    """Given a run ID, returns a dictionary of its information and status
    """
    request = 'get_run/' + str(run_id)
    result = client.send_get(request)
    return(result)
    
def get_runs():
    """Using the project ID set above, returns a list of dictionaries for each
    run in the project
    """
    request = 'get_runs/' + str(project_id)
    result = client.send_get(request)
    return(result)
    
# Plans
def get_plan(plan_id):
    """Return a dictionary with information about the given plan_id.
    """
    request = 'get_plan/' + str(plan_id)
    result = client.send_get(request)
    return result
    
def get_run_nums_from_plan(plan_id):
    """Given a test plan number, returns a list
    of the test run numbers (as strings) in that plan.
    """
    test_plan = get_plan(plan_id)
    entries = test_plan['entries']
    test_run_nums = []
    for entry in entries:
        runs_in_entry = entry['runs']
        for run in runs_in_entry:
            test_run_nums.append(str(run['id']))
    return test_run_nums
    
