"""GLaDOS is a project to integrate TestRail with Robot Framework.
Test plans and runs are created using Testrail, and GLaDOS will execute
any tests from a given run or runs, using Robot Framework.

The results of each test will be posted back to TestRail. The results
include test status, browser used, execution time, and any comments
that were set in the test.
"""
from __future__ import print_function
from __future__ import absolute_import
from builtins import str
import argparse
import os
import re
import subprocess
import sys
import time
import yaml
from datetime import datetime
from multiprocessing.dummy import Pool

import testrail_api_glados

from functools import partial

VERSION = '5.0.0'
# 0.0.X bug fixes
# 0.X.0 minor new features/changes
# X.0.0 major features/changes

def setup_argparse():
    """Sets up the medium for storing data using the argparse module.

    Notes:
    - Input validation should be done utilizing the argparse module whenever
      possible
    """
    # keys are the number from TestRail, values are the text. ie. {5:'fail'}
    test_status_dictionary = testrail_api_glados.get_status_dictionary()
    test_category_dictionary = testrail_api_glados.get_test_categories()

    # the values for test categories contain problem characters, so we must
    # sanitize them
    test_category_dictionary = {key:re.sub(r'[^a-zA-Z0-9]', '_', value.lower())
                                for key, value
                                in list(test_category_dictionary.items())}

    # Default values
    default_browser = ''
    default_platform = 'windows'
    default_version = '7'
    default_test_category_filter = []
    default_not_test_categories = [] 
    default_environment = 'staging'
    default_jenkins_url = ''
    default_merge_output = False
    default_pool_size = 4
    default_remote_url = ''
    default_test_status_filter = []
    default_search_path = '.' + os.sep + '..'
    default_tag = None
    default_command = "robot"

    # Choices
    choices_test_status_filter = list(test_status_dictionary.values())
    choices_test_category_filter = list(test_category_dictionary.values())
    choices_commands = ['robot', 'pytest']

    # Help text
    txt_automation_only = "Only run tests by automation user"
    txt_browser = "Sets the browser to use if one cannot be determined from a test run configuration."
    txt_platform = "Sets the platform to use if one cannot be determined from a test run configuration."
    txt_version = "Sets the platform version to use if one cannot be determined from a test run configuration."
    txt_test_run_ids = "Sets the test plan or test run IDs to execute test scripts from."
    txt_environment = "Sets the environment variable in Robot Framework."
    txt_pool_size = "Determines how many concurrent Pybot commands to execute."
    txt_developer_mode = "Toggles developer mode on."
    txt_test_status_filter = "Run only tests that match one of given test status filters."
    txt_test_category_filter = "Run only tests that match one or more of the given test category filters."
    txt_remote_url = "Sets the remote variable in Robot Framework."
    txt_jenkins_url = "URL of the Jenkins box to use."
    txt_merge_output = "Set to True if you want to merge the output into one file after all tests are run. Default: False"
    txt_variable = "Creates a variable in Robot Framework.  Syntax is name:value"
    #5385 add search path 
    txt_search_path = "Assign Search path for glados to search"
    #Set Tags For all executing Test Cases
    txt_set_tags = "Sets the mentioned tags to all executing test cases"
    txt_command = "Choose if you are running robot or pytest commands. Options: robot, pytest"
    txt_not_test_categories = "Sets test categories that you do NOT want to test."
    
    # Arguments
    parser = argparse.ArgumentParser()

    # Can probably delete these notes after a few iterations of Glados
    # changes from previous version (before 3.0.0)
    # --filters changed to --test_status_filter
    # --test_categories changed to --test_category_filter
    # removed -v, --variable_file argument
    # --dev_mode changed to --developer_mode
    # removed -s, --save_config argument
    # -x changed to -v
    # added -b, --browser
    # no longer need to set the jenkins project/job name

    # keep in alphabetical order based on shorthand syntax
    parser.add_argument("-a", "--automation_only", help=txt_automation_only, default=False, action='store_true')
    parser.add_argument("-b", "--browser", help=txt_browser, nargs='?', default=default_browser)
    parser.add_argument("-c", "--test_category_filter", help=txt_test_category_filter, nargs='?',
                        default=default_test_category_filter, action='append', choices=choices_test_category_filter)
    parser.add_argument("-d", "--developer_mode", help=txt_developer_mode, default=False, action='store_true')
    parser.add_argument("-e", "--environment", help=txt_environment, nargs='?', default=default_environment)
    parser.add_argument("-f", "--test_status_filter", help=txt_test_status_filter, nargs='?', default=default_test_status_filter,
                        action='append', choices=choices_test_status_filter)
    parser.add_argument("-G", "--settag", help=txt_set_tags, nargs='?', default=default_tag)
    parser.add_argument("-j", "--jenkins_url", help=txt_jenkins_url, nargs='?', default=default_jenkins_url) 
    parser.add_argument("-m", "--merge_output", help=txt_merge_output, nargs='?', default=default_merge_output) 
    parser.add_argument("-n", "--not_test_categories", help=txt_not_test_categories, nargs='?', default=default_not_test_categories, 
                        action='append', choices=choices_test_category_filter) 
    parser.add_argument("-p", "--pool_size", help=txt_pool_size, nargs='?', default=default_pool_size, type=int)
    parser.add_argument("-pf", "--platform", help=txt_platform, nargs='?', default=default_platform)
    parser.add_argument("-r", "--remote_url", help=txt_remote_url, nargs='?', default=default_remote_url)
    parser.add_argument("-s", "--search_path", help=txt_search_path, nargs='?', default=default_search_path)
    parser.add_argument("-t", "--test_run_ids", help=txt_test_run_ids, nargs='+', type=int, required=True)
    parser.add_argument("-v", "--variable", help=txt_variable, nargs='?', default=[], action='append')
    parser.add_argument("-ver", "--version", help=txt_version, nargs='?', default=default_version, type=int)
    parser.add_argument("-x", "--command", help=txt_command, nargs='?', default=default_command, choices=choices_commands)


    args = parser.parse_args()
    return args

def remove_duplicates(input_list):
    """Given a list, returns the list with duplicate values removed.
    """
    unique_items = set()
    for item in input_list:
        if item not in unique_items:
            unique_items.add(item)

    return list(unique_items)

def translate_test_statuses(input_list):
    """Given a list of test statuses as strings, returns a list of numbers
    corresponding to the status on TestRail. ie. ['passed', 'failed', 'retest']
    becomes ['1', '5', '3']
    """
    test_status_dictionary = testrail_api_glados.get_status_dictionary()
    output_list = [status_id for status_id, status_name
                   in list(test_status_dictionary.items())
                   if status_name in input_list]

    # if output is empty, set it to all
    if not output_list:
        output_list = list(testrail_api_glados.get_status_dictionary().keys())

    return output_list

def translate_test_categories(input_list, use_empty=False):
    """Given a list of test categories as strings, returns a list of numbers
    corresponding to the category on TestRail.
    ie. ['no_label', 'design_ui', 'seo'] becomes ['0', '5', '10']
    """
    test_category_dictionary = testrail_api_glados.get_test_categories()
    output_list = [category_id for category_id, category_name
                   in list(test_category_dictionary.items())
                   if re.sub(r'[^a-zA-Z]', '_', category_name.lower().strip()) in input_list]

    # if output is empty, set it to all
    if not output_list and not use_empty:
        output_list = list(testrail_api_glados.get_test_categories().keys())

    return output_list

def extract_run_ids_from_plan_id(test_plan_id):
    """Given a test plan id, returns a list of the test run IDs found in that
    test plan. If the input is not recognized as a plan ID, a list is returned
    of just the input.
    """
    test_run_ids = []

    try:
        testrail_api_glados.get_plan(test_plan_id)
    except:
        test_run_ids.append(test_plan_id)
    else:
        test_run_ids = testrail_api_glados.get_run_nums_from_plan(test_plan_id)

    return test_run_ids

def format_arguments(args):
    """Formats arguments from an argument parser object into data usable by the
    program.

    This is mostly for arguments that could not be formatted using argparse.
    For instance we allow the user to specify test statuses by name
    (ie. 'passed', 'blocked', etc.), but TestRail does not recognize these
    names, only their ID's. Thus, we have to change the names into the IDs that
    TestRail uses.
    """
    # Change the list of test category names into a list of test category IDs
    args.test_category_filter = translate_test_categories(args.test_category_filter)
    args.not_test_categories = translate_test_categories(args.not_test_categories, use_empty=True)

    # Change the list of test status names into a list of test status IDs
    args.test_status_filter = translate_test_statuses(args.test_status_filter)

    # Change the list into a list of just test run IDs
    run_ids = []
    for id in args.test_run_ids:
        run_ids = run_ids + extract_run_ids_from_plan_id(id)

    # Remove duplicates from lists
    args.test_category_filter = remove_duplicates(args.test_category_filter)
    args.not_test_categories = remove_duplicates(args.not_test_categories)
    args.test_status_filter = remove_duplicates(args.test_status_filter)
    args.test_run_ids = remove_duplicates(run_ids)

    # Convert numbers to integers
    args.test_category_filter = [int(category_id) for category_id in args.test_category_filter]
    args.not_test_categories = [int(category_id) for category_id in args.not_test_categories]
    args.test_status_filter = [int(status_id) for status_id in args.test_status_filter]
    args.test_run_ids =[int(run_id) for run_id in args.test_run_ids]

    return args

def match_test_filters(test_data, test_statuses, test_categories, not_test_categories):
    """Given data on a test case as returned by TestRail and test statuses and
    categories to filter by, returns True or False if the test data satisfied
    the filters.
    """
    filters = {
        'test_status': False,
        'test_category': False
    }

    # Check that test statuses are matched
    if(test_data['status_id'] in test_statuses):
        filters['test_status'] = True

    # Check that test categories are matched
    for test_category in test_data['custom_test_category']:
        if test_category in test_categories:
            filters['test_category'] = True
            break

    # Check if any categories for the test are categores from not_test_categories
    for test_category in test_data['custom_test_category']:
        if test_category in not_test_categories:
            filters['test_category'] = False
            break 
    # Check if any categories for the test are categores from not_test_categories
    for test_category in test_data['custom_test_category']:
        if test_category in not_test_categories:
            filters['test_category'] = False
            break 

    # Return True/False
    if False in list(filters.values()):
        result = False
    else:
        result = True

    return result

def determine_browser(test_run_id):
    """Given a test run ID, attempts to determine the browser for the given
    test run based on the test run's configuration.

    If no browser can be determined, None is returned.
    """
    run_info = testrail_api_glados.get_run(test_run_id)
    run_config = run_info['config']
    
    if not run_config:
        # if config is None or empty set it to empty string to avoid errors
        run_config = ''
    
    run_config = run_config.lower()  
    if(re.search(r'\bchrome\b', run_config) or
            re.search(r'\bgooglechrome\b', run_config) or
            re.search(r'\bgc\b', run_config)):
        browser = 'chrome'
    elif(re.search(r'\bfirefox\b', run_config) or
            re.search(r'\bff\b', run_config)):
        browser = 'firefox'
    elif(re.search(r'\bie\b', run_config) or
            re.search(r'\binternet explorer\b', run_config)):
        browser = 'internetexplorer'
    elif(re.search(r'\bphantomjs\b', run_config)):
        browser = 'phantomjs'
    elif(re.search(r'\bsafari\b', run_config)):
        browser = 'safari'
    elif(re.search(r'\bedge\b', run_config)):
        browser = 'edge'
    else:
        browser = None
    
    return browser

def determine_platform_version(test_run_id, browser, args):
    """Given a test run ID, attempts to determine the platform for the given
    test run based on the test run's configuration.

    Note: Browser is used to determine if it needs firefox version of platform
    Yes, could remove browser to use args.browser, but just left it there since browser was already defined
    If no platform or version can be determined, None is returned.
    """
    run_info = testrail_api_glados.get_run(test_run_id)
    print(run_info)
    print(run_info['config'])
    run_config = run_info['config']
    
    # Default platform and version defined
    if not run_config:
        # if config is None or empty set it to empty string to avoid errors
        run_config = ''

    # Set the default platform and version
    if args.platform is None:
        platform = 'windows' # Avoid errors
    else:
        platform = args.platform.lower()
        
    if args.platform is None: 
        version = ''
    else:
        version = args.version # Set to arg version by default
    
    run_config = run_config.lower()

    if(re.search(r'\bwindows7\b', run_config) or
            re.search(r'\bwin7\b', run_config) or
            re.search(r'\bvista\b', run_config) or
            re.search(r'\bwindows 7\b', run_config)):
        platform = 'windows'
        version = 7
    elif(re.search(r'\bwindows10\b', run_config) or
            re.search(r'\bwin10\b', run_config) or
            re.search(r'\bwindows 10\b', run_config)):
        platform = 'windows'
        version = 10
    elif(re.search(r'\bwindows\b', run_config)):
        platform = 'windows'
    elif(re.search(r'\bmac\b', run_config)):
        platform = 'mac'
    elif(re.search(r'\bios(\d*)?\b', run_config) 
        or re.search(r'\biphone(\s?(\d|x)s?)?(\s?max)?\b', run_config)
        or re.search(r'\bipad\s?(air|pro)?\s?\d?\b', run_config)):
        platform = 'ios'
    elif(re.search(r'\bandroid\b', run_config)
        or re.search(r'\bandroid(\s?emulator)?(\s?\d*(.\d)*)\b', run_config)):
        platform = 'android'

    return platform, version

def determine_device(test_run_id):
    """Given a test run ID, attempts to determine the device for the given
    test run based on the test run's configuration.

    If no device can be determined, None is returned.
    """
    run_info = testrail_api_glados.get_run(test_run_id)
    run_config = run_info['config']
    
    if not run_config:
        # if config is None or empty set it to empty string to avoid errors
        run_config = ''
    
    run_config = run_config.lower()
    
    # Set the regex of the string
    regex_iphone = r'\biphone(\s?(\d|x)s?)?(\s?max)?\b'
    regex_ipad = r'\bipad\s?(air|pro)?\s?\d?\b'
    regex_android = r'\bandroid(\s?emulator)?(\s?\d*(.\d)*)\b'
    
    # Get the device of the testcase
    if re.search(regex_iphone, run_config):
        device = re.search(regex_iphone, run_config).group(0)
    elif re.search(regex_ipad, run_config):
        device = re.search(regex_ipad, run_config).group(0)
    elif re.search(regex_android,run_config):
        device = re.search(regex_android, run_config).group(0)
    # Automotive's version of default iphone
    elif re.search(r'\bphone.*ios(\d*)?\b',run_config):
        device = 'iphone'
    else:
        device = None
    print("Device: " + str(device))
    
    # Remove any whitespace if device text if not none
    if device is not None:
        device = device.replace(' ','')
    
    return device
    
def determine_landscape_mode(test_run_id):
    """Given a test run ID, attempts to determine if the browser for the given
    test run based on the test run's configuration needs to be in landscape mode.
    
    Returns True or False if the testrun should be in landscape mode.
    """  
    run_info = testrail_api_glados.get_run(test_run_id)
    run_config = run_info['config']
    
    if not run_config:
        # if config is None or empty set it to empty string to avoid errors
        run_config = ''
    
    # Determine if the configuration contains landscape option    
    return re.search('landscape', run_config, re.IGNORECASE) is not None

def sanitize_input_for_robot(input):
    """Given a string, sanitizes the string so that it should not cause any
    problems being part of a robot command.
    """
    input = re.sub(r'[^a-zA-Z0-9]', '_', input)
    input = re.sub(r'_+', '_', input)
    input = input.strip('_')

    return input

def get_tests_to_run(args, test_run_id, no_suite_key):
    # no_suite_key = "_no_suite"            ### ???
    tests_to_run = {no_suite_key: []}  
        
    #Grab all results tests where the final result is by a manual user
    if (args.automation_only):
        manual_final_results = testrail_api_glados.get_manually_tested_final_results(test_run_id)
            
    # POPULATE tests_to_run DICTIONARY
    test_cases = testrail_api_glados.get_tests(test_run_id)
    for test in test_cases:
        # Skip over tests that does not match the input filter
        if not match_test_filters(test, args.test_status_filter, args.test_category_filter, args.not_test_categories):
            continue
        # skip over tests that are not automated
        # logic: skip unless there is an automation test name, and
        #        Type is set to Automated or Developer Mode is True
        if( not (test['custom_automation_test_name'] and (test['type_id'] == 1 or args.developer_mode))):
            continue
            
        #Skip tests that have a final status set by a manual user
        if (args.automation_only and test['id'] in manual_final_results):
            continue

        #Skip tests where the environment you try to run with does not match the Testrail category ('Staging Test Only' or "Release Test Only"), and update testrail with NA
        prod_envs = ['prod', 'preprd2', 'preprd3', 'preprd4', 'prd', 'www']
        stg_envs = ['stg1', 'stg2', 'stg3', 'stg4', 'stg5', 'stg6', 'stg7', 'stg8', 'stg9', 'stg10', 'qa1']
        ## if((int(translate_test_categories('staging_test_only')[0]) in test['custom_test_category']) and ('staging' not in args.environment and 'stg' not in args.environment)):
        if((int(translate_test_categories('staging_test_only')[0]) in test['custom_test_category']) and (args.environment not in stg_envs)):
            comment = 'This is a staging only test, but someone tried to run it on ' + str(args.environment) + "." 
            status_id = 6    # N/A
            testrail_api_glados.add_test_result(test_run_id, test['case_id'], status_id, comment, elapsed=1, browser=args.browser, browser_version='', environment=args.environment)
            print("updating testrail with: testrail_api_glados.add_test_result(" + str(test_run_id) + ", " + str(test['case_id']) + " , " + str(status_id) + ", " + str(comment) + ", elapsed=1, browser=" + str(args.browser) + ", browser_version='', environment=" + str(args.environment) + ")")
            continue 
        elif((int(translate_test_categories('release_test_only')[0]) in test['custom_test_category']) and (args.environment not in prod_envs)):
            comment = 'This is a release (prod) only test, but someone tried to run it on ' + str(args.environment) + "." 
            status_id = 6    # N/A
            testrail_api_glados.add_test_result(test_run_id, test['case_id'], status_id, comment, elapsed=1, browser=args.browser, browser_version='', environment=args.environment)
            print("updating testrail with: testrail_api_glados.add_test_result(" + str(test_run_id) + ", " + str(test['case_id']) + " , " + str(status_id) + ", " + str(comment) + ", elapsed=1, browser=" + str(args.browser) + ", browser_version='', environment=" + str(args.environment) + ")")
            continue 

        #Sort tests based on sub suite name or lack of
        #Case 1 - sub suite field is empty: Append test to no_suite_key
        if(('custom_automation_sub_suite_name' not in test) or (not test['custom_automation_sub_suite_name'])):
            tests_to_run[no_suite_key].append(test)
        #Otherwise - automation_sub_suite_name is not empty: add automation_sub_suite_name to correct key
        else:
            #a: Add test to run dictionary under the sub_suite_name key if it already exists
            if(test['custom_automation_sub_suite_name'] in tests_to_run):
                tests_to_run[test['custom_automation_sub_suite_name']].append(test)
            #b: Otherwise create key and add test under the sub_suite_name
            else:
                tests_to_run[test['custom_automation_sub_suite_name']] = [test]  
    return tests_to_run 

def create_robot_commands(args):
    """Creates a list of Pybot commands to run tests based on data from the
    ArgumentParser object.
    """
    robot_commands = []
    all_output_paths = [] 
    slash = os.sep
    date_string = datetime.now().strftime("%m%d%Y_%H%M%S")
    base_robot_command = ("robot" + "{test_name_vars_ph}" + "{suite_name_ph}" + " {base_variables_ph}" + "{case_id_vars_ph}" + " -d {output_dir_ph}" + " {search_path_ph}")

    more_variables = ""
    default_device = ""
    for custom_var in args.variable:
        var_name, var_value = custom_var.split(':', 1)
        if var_name.lower() == "device":
            default_device = var_value
        else:
            more_variables += " -v " + var_name + ":" + var_value 
    #Set Tags
    if args.settag is not None:
        more_variables += " -G " + args.settag 

    for test_run_id in args.test_run_ids:
        # create a dictionary whose keys are Robot Framework (RF) suite names
        # and values are a list of test cases in that suite using the data from
        # TestRail tests on TestRail that have no suite name specified have the
        # key set by no_suite_key
        no_suite_key = "_no_suite" 
        tests_to_run = get_tests_to_run(args, test_run_id, no_suite_key)    ### NEW ### 
        # CREATE PYBOT COMMANDS
        run_info = testrail_api_glados.get_run(test_run_id)
        run_name = sanitize_input_for_robot(run_info['name']) 
        # use default browser set in args if one cannot be determined
        browser = determine_browser(test_run_id)
        if not browser:
            browser = args.browser
        # use default platform & version set in args if one cannot be determined
        platform, version = determine_platform_version(test_run_id, browser, args)
        device = determine_device(test_run_id)
        if not device:
            device = default_device
        landscape_mode = determine_landscape_mode(test_run_id) 
        base_variables = (
            " -v browser:" + browser +
            " -v environment:" + args.environment +
            " -v run_id:" + str(test_run_id) +
            " -v run_name:" + run_name +
            " -v remote:" + args.remote_url +
            " -v jenkins_url:" + args.jenkins_url +
            " -v landscape_mode:" + str(landscape_mode) +
            " -v platformname:" + platform +
            " -v device:" + device + more_variables
        )
        
        template_string_partial = ''
        if version is not None:
            base_variables += " -v version:" + str(version)
            template_string_partial = str(version)
        if device is not None and device != '':
            template_string_partial = template_string_partial + "_" + str(device)
        output_dir_template = ("logs" + slash + str(test_run_id) + "_" + platform + template_string_partial + "_" + browser + "_" + date_string + slash + "{suite_test_name_ph}") 
        for suite in tests_to_run:
            # create robot commands for no_suite_key tests
            suite_name = ""
            suite_name_var = ""
            if suite == no_suite_key:
                for test_data in tests_to_run[suite]:
                    # removed base_robot_command and base_variables from here 
                    ## Get the suite name if exist, set the log output location as well
                    test_name = test_data['custom_automation_test_name']
                    test_name = test_name.replace(" ", "_")
                    if (test_data['custom_automation_suite_name']):
                        suite_name = str(test_data['custom_automation_suite_name'].replace(" ", "_"))
                        suite_name_var = " -s " + suite_name
                        suite_and_test_name = suite_name + "_" + test_name
                    else:
                        suite_name = str(test_data['custom_automation_suite_name'].replace(" ", "_"))
                        suite_name_var = " -s " + suite_name
                        suite_and_test_name = suite_name + "_" + test_name
                    output_dir = output_dir_template.format(suite_test_name_ph=suite_and_test_name)
                    case_id_var =  (test_name + "_case_id:" + str(test_data['case_id'])) 
                    all_output_paths.append(output_dir) 
                    robot_command = base_robot_command.format(
                        suite_test_name_ph=suite_and_test_name,
                        suite_name_ph=suite_name_var,
                        test_name_vars_ph=" -t " + test_name,
                        base_variables_ph=base_variables,
                        case_id_vars_ph=" -v " + case_id_var,
                        output_dir_ph=output_dir,
                        slash_ph=slash,
                        search_path_ph = args.search_path
                    )
                    robot_commands.append(robot_command) 
            else:
                # create robot commands for the rest
                # removed base_robot_command and base_variables from here 
                # Get suite and sub suite name from tests
                suite_name = "no_suite"
                sub_suite_name = "no_sub_suite"
                if (tests_to_run[suite][0]['custom_automation_suite_name']):
                    suite_name = tests_to_run[suite][0]['custom_automation_suite_name'].replace(" ", "_")
                if (('custom_automation_sub_suite_name' in tests_to_run[suite][0]) and (tests_to_run[suite][0]['custom_automation_sub_suite_name'])):
                    sub_suite_name = tests_to_run[suite][0]['custom_automation_sub_suite_name'].replace(" ", "_") 
                # Set default variables
                test_name_vars = ""
                case_id_vars = "" 
                
                for test_data in tests_to_run[suite]:
                    test_name = test_data['custom_automation_test_name']
                    test_name = test_name.replace(" ", "_")
                    test_name_vars += " -t " + test_name
                    case_id_var = (" -v " + test_name + "_case_id:" + str(test_data['case_id']))
                    case_id_vars += case_id_var
                 
                # Create output directory
                output_dir = output_dir_template.format(suite_test_name_ph=sub_suite_name)
                all_output_paths.append(output_dir) 
                robot_command = base_robot_command.format(
                    suite_name_ph=" -s " + suite_name,
                    test_name_vars_ph=test_name_vars,
                    base_variables_ph=base_variables,
                    case_id_vars_ph=case_id_vars,
                    output_dir_ph=output_dir,
                    slash_ph=slash,
                    search_path_ph = args.search_path
                )
                robot_commands.append(robot_command)

    # return list of commands and a list of output directories
    return (robot_commands, all_output_paths)

def create_pytest_commands(args):
    pytest_commands = []
    all_output_paths = [] 
    no_suite_key = "_no_suite"
    tests_to_run = {no_suite_key: []}
    date_string = datetime.now().strftime("%m%d%Y_%H%M%S")
    slash = os.sep
    for test_run_id in args.test_run_ids:
        tests_to_run = get_tests_to_run(args, test_run_id, no_suite_key)
        run_info = testrail_api_glados.get_run(test_run_id)
        run_name = sanitize_input_for_robot(run_info['name'])
        # platform = determine_platform(test_run_id)
        # if not platform:
        #     platform = args.platform
        browser = determine_browser(test_run_id)
        if not browser:
            browser = args.browser 
        if browser:
            browser = " --browser=" + browser 

        landscape_mode = determine_landscape_mode(test_run_id)

        for suite in tests_to_run:
            # create robot commands for no_suite_key tests
            if suite == no_suite_key:
                for test_data in tests_to_run[suite]:
                    base_pytest_command = ("python -m pytest " + "{suite_name_ph}" + ".py::" + "{suite_name_ph}" + "::" + "{test_name_ph}" + " " +  "{base_variables_ph}")
                    base_variables = (
                            " --test_run_id " + str(test_run_id) +
                            " --test_case_id " + str(test_data['case_id']) +
                            " --capture=sys --tb=native --env " + args.environment +  
                            browser
                    )
                    print("variables = " + str(args.variable))
                    for custom_var in args.variable:
                        print("custom_var = " + str(custom_var))
                        var_name, var_value = custom_var.split(':', 1)
                        base_variables += " --vars " + var_name + "=" + var_value


                    test_name = test_data['custom_automation_test_name']
                    test_name = test_name.replace(" ", "_")
                    case_id_var = (test_name + "_case_id:" + str(test_data['case_id']))

                    ## Get the suite name if exist, set the log output location as well 
                    suite_name_var = ""
                    if (test_data['custom_automation_suite_name']):
                        suite_name = str(test_data['custom_automation_suite_name'].replace(" ", "_"))
                        # changed for pytest
                        ### suite_name_var = suite_name + ".py"
                        #add for folders
                        ### path_var = suite_name.split('_')[1]
                        output_dir = ("logs" + slash + str(test_run_id) + "_" + date_string + slash + suite_name + "_" + test_data['custom_automation_test_name'])
                    else:
                        output_dir = ("logs" + slash + str(test_run_id) + "_" + date_string + slash + test_data['custom_automation_test_name'])
                    all_output_paths.append(output_dir)

                    robot_command = base_pytest_command.format(
                        suite_name_ph=suite_name,
                        test_name_ph=test_name,
                        base_variables_ph=base_variables,
                        case_id_var_ph=case_id_var,
                        output_dir_ph=output_dir,
                        slash_ph=slash,
                        search_path_ph=args.search_path,
                        runId=test_run_id
                    )
                    pytest_commands.append(robot_command)

            else: 
                base_pytest_command = ("python -m pytest -k " + "{test_name_ph} " + "tests")
                base_variables = (
                        " --test_run_id " + str(test_run_id) +
                        # test for case id
                        " --test_case_id " + str(test_data['case_id']) +
                        #" --output_dir " + str(output_dir) +
                        " --capture=sys --tb=native"

                )
                for custom_var in args.variable:
                    var_name, var_value = custom_var.split(':', 1)
                    base_variables += " -v " + var_name + ":" + var_value

                # Get suite and sub suite name from tests
                suite_name = "no_suite"
                sub_suite_name = "no_sub_suite"
                if (tests_to_run[suite][0]['custom_automation_suite_name']):
                    suite_name = tests_to_run[suite][0]['custom_automation_suite_name'].replace(" ", "_")
                if (('custom_automation_sub_suite_name' in tests_to_run[suite][0]) and (
                tests_to_run[suite][0]['custom_automation_sub_suite_name'])):
                    sub_suite_name = tests_to_run[suite][0]['custom_automation_sub_suite_name'].replace(" ", "_")

                # Set default variables
                test_name_vars = ""
                case_id_vars = ""

                for test_data in tests_to_run[suite]:
                    test_name = test_data['custom_automation_test_name']
                    test_name = test_name.replace(" ", "_")
                    test_name_vars = test_name
                    case_id_var = (" -v " + test_name + "_case_id:" +
                                   str(test_data['case_id']))
                    case_id_vars += case_id_var

                # Create output directory
                output_dir = ("logs" + slash + str(test_run_id) + "_" + browser + "_" + date_string + slash + sub_suite_name)
                all_output_paths.append(output_dir)

                pytest_command = base_pytest_command.format(
                    suite_name_ph=suite_name,
                    test_name_vars_ph=test_name_vars,
                    base_variables_ph=base_variables,
                    case_id_vars_ph=case_id_vars,
                    output_dir_ph=output_dir,
                    slash_ph=slash,
                    search_path_ph=args.search_path
                )
                pytest_commands.append(robot_command)

    return (pytest_commands, all_output_paths)


def run_command(command, cmd_cwd):
    """Run a given command.
    """
    result = subprocess.Popen(command, shell=True, cwd=cmd_cwd).wait() 
    test_name_pattern = r"^.*-t\s([.a-zA-Z0-9_-]*)\s.*$"
    try:
        test_name = re.match(test_name_pattern,command).groups()[0]
    except:
        test_name = command
    if result:
        print("FAILURE: " + test_name)
    else:
        print("SUCCESS: " + test_name)
    return(result)

def run_rebot_merge(all_output_paths):
    """ Run rebot --merge with output paths created from the robot commands """
    rebot_commands = "rebot --merge --output output.xml "
    for outp in all_output_paths:
        output_dir_a,output_dir_b = outp.split(os.sep, 1)
        rebot_commands += output_dir_b + os.sep + "output.xml "
    print("rebot_commands = " + str(rebot_commands))
    os.chdir("logs") 
    rebot_result = subprocess.Popen(rebot_commands, shell=True).wait()
    print("rebot_result = " + str(rebot_result)) 

def main():
    # Setup argparse
    args = setup_argparse()

    # Format argparse
    args = format_arguments(args)
    cwd = "." 
    if args.command == 'pytest': 
        (command_list, all_output_paths) = create_pytest_commands(args)
        cwd = "../../tests"
    else:     ### "=== robot ==="
        (command_list, all_output_paths) = create_robot_commands(args)
        cwd = "."
    
    # Run the commands
    pool = Pool(args.pool_size) # Number of allowed concurrent processes
    total_failures = 0
    print(" --- --- --- --- --- --- --- --- --- --- --- ---")
    print("cwd: " + str(cwd))
    for jgdebug1 in command_list:
        print(jgdebug1)
    print(" --- --- --- --- --- --- --- --- --- --- --- ---") 

    ### processes = pool.map(run_command, command_list, cwd)
    processes = pool.map(partial(run_command, cmd_cwd=cwd), command_list)

    if args.merge_output:
        run_rebot_merge(all_output_paths)

    total_failures = sum([1 for result in processes if result])

    # Print out results
    print("\nFORMATTED ARGPARSE DATA")
    print(args)
    print("\nPYBOT COMMANDS EXECUTED")
    print("\n\n".join(command_list))

    results_message = ("\nFINAL RESULT:  {failure_count_ph}/{test_count_ph}"
                       + " tests failed.\n")
    results_message = results_message.format(
                        failure_count_ph=total_failures,
                        test_count_ph=len(command_list))
    print(results_message)

    # Raise error if any failures.  This will trigger a failure on Jenkins.
    if(int(total_failures) > 0):
        raise AssertionError("One or more failures occurred.")

    return total_failures


if __name__ == "__main__":
    main()
