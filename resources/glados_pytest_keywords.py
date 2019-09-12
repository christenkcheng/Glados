from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from glados.resources.testrail_api_glados import *
import datetime
import calendar
import os
import urllib.request, urllib.parse, urllib.error
import re
import time
import pytest
import sys

"""
Help Function
"""

#help function - should be in glados_pytest_keywords.py
def get_epoch_timestamp():
    time_utc = datetime.datetime.utcnow()
    time_epoch = calendar.timegm(time_utc.utctimetuple())
    return time_epoch

def glados_setup(request):
    print('START TEST')
    """
    Getting values from conftest.py
    """
    ## ${UTC_TIME_START} =    get time    epoch    UTC
    ## # Make sure required variables are set
    ## ${ENVIRONMENT} =    get variable value    ${ENVIRONMENT}    staging
    ## ${BROWSER} =    get variable value    ${BROWSER}    firefox
    ## ${PLATFORMNAME} =    get variable value    ${PLATFORMNAME.upper()}    WINDOWS
    ## ${VERSION} =    get variable value    ${VERSION}    ${EMPTY}
    ## # Make sure optional variables exist
    ## ${JENKINS_URL} =    get variable value    ${JENKINS_URL}    ${EMPTY}
    ## ${REMOTE} =    get variable value    ${REMOTE}    ${EMPTY}
    ## # Set all to global variables
    ## set global variable    ${UTC_TIME_START}
    ## set global variable    ${ENVIRONMENT}
    ## set global variable    ${BROWSER}
    ## set global variable    ${JENKINS_URL}
    ## set global variable    ${REMOTE}
    ## set global variable    ${PLATFORMNAME}
    ## set global variable    ${VERSION}

    # old stuff ---
    print(sys.argv)
    test_run_id = request.config.getoption("--test_run_id")
    print("Test run ID is %s." % test_run_id)
    test_case_id = request.config.getoption("--test_case_id")
    #output_dir = request.config.getoption("--output")
    test_start_time_epoch = get_epoch_timestamp()
    #test_result = ''
    jenkins_url = ''
    override_test_result = ''
    test_comments = ''

def update_testrail(request, override_run_id='', override_case_id=''):
    test_comments = ""
    if 'testrail_comments' in request.cls.base:
        comments_list = request.cls.base['testrail_comments']
        test_comments = "\n".join(comments_list)

    errorMessage = ""
    testPassed = True
    env = request.cls.base['env']

    browser = "none"
    if 'browser' in request.cls.base:
        browser = request.cls.base['browser']
    browser_version = "unknown browser version"
    if request.node.rep_setup.failed:
        errorMessage = "Test Setup failed. Method %s" % request.node.nodeid
        testPassed = False
    elif request.node.rep_setup.passed:
        if request.node.rep_call.failed:
            errorMessage = "Failure in test body. Method %s" % request.node.nodeid
            testPassed = False

    test_comments = test_comments + "\n" + errorMessage 

    if 'log_file_url' in request.cls.base:
        test_comments = test_comments + "\nThe log file is located [here](" + request.cls.base['log_file_url'] + ")"

    resultId = 5
    if testPassed: 
        resultId = 1
    if 'test_status' in request.cls.base:
        test_status = request.cls.base['test_status']
        print("---DEBUG--- test_status = " + str(test_status))
        resultId = test_status[0] 

    test_run_id = request.config.getoption("--test_run_id")
    test_case_id = request.config.getoption("--test_case_id")
    elapsed_time = 1 
    if 'elapsed_time ' in request.cls.base:
        elapsed_time = request.cls.base['elapsed_time']

    print("Current test run ID value is %s." % test_run_id)
    print("Current test case ID value is %s." % test_case_id) 
    print("Environment = " + env)
    print("Result STATUS = " + str(resultId))

    add_test_result(run_id=test_run_id, case_id=test_case_id, status_id=resultId, comment=test_comments, elapsed=elapsed_time, browser=browser, browser_version=browser_version, environment=env)


def create_url_to_log_folder():
    """
    Returns a string that can be pasted into the address of the browser that will take the user to log folder of the test case/suite.

    """
    #Todo: Is the  local_computer link can really linked to open local things
    local_computer = 'file://' + str(output_dir)
    # Creating the string when running from Jenkins takes more work
    from_jenkins = 'None'
    if jenkins_url != '':
        from_jenkins = create_jenkins_url_to_log_folder(jenkins_url, output_dir)
    # Decide which to use
    url = local_computer if from_jenkins == 'None' else from_jenkins
    return url


def override_test_result_to_retest():
    """
    """
    globals()['override_test_result'] = '4'


def override_test_result_to_blocked():
    """
    """
    globals()['override_test_result'] = '2'
    msg = 'Test is blocked'


def override_test_result_to_na():
    """
    """
    globals()['override_test_result'] = '6'
    msg = 'Test is N/A'

def determine_time_elapsed():
    """
    """
    test_end_time_epoch = get_epoch_timestamp()
    time_elapsed = test_end_time_epoch-test_start_time_epoch
    #todo
    #question, why the test_start_time_epoch can be used here but the override_test_result is not accessible?????
    if time_elapsed < 1:
        time_elapsed = 1

    test_start = time.strftime("%H:%M:%S", time.localtime(test_start_time_epoch))
    test_end = time.strftime("%H:%M:%S", time.localtime(test_end_time_epoch))
    return time_elapsed, test_start, test_end

#this function is used in update testrail
def prepare_testrail_comments():
    """
    Formats the TestRail comment output.
    :return: The markup string for all TestRail comments
    """
    time_elapsed, test_start, test_end = determine_time_elapsed()
    # format comments
    log_url = create_url_to_log_folder()
    print("log_url:" + str(log_url))

    if globals()['test_result'] == '5':
        test_message = 'Test failed, please check detailed report'
        test_header_info = "![](index.php?/attachments/get/114459)\nThe log file can be viewed [here](" + log_url + "/log.html).\n\nPytest Message: " + test_message + "\n\nTest Start:" + test_start + " UTC / GMT \nTest End  :" + test_end + " UTC / GMT\n- - - -\n"
    elif globals()['test_result'] == '1':
        test_message = 'No error messages from pytest.'
        test_header_info = "The log file can be viewed [here](" + log_url + "/log.html).\n\nPytest Message: " + test_message + "\n\nTest Start:" + test_start + " UTC / GMT \nTest End     :" + test_end + " UTC / GMT\n- - - -\n"
    #TODO USE THE PYTHON FORMATTING THING AND SEE IF IT WORKS
    #test_header_info = "The log file can be viewed [here](" + log_url + "/log.html).\n\nPytest Message: " + test_message + "\n\nTest Start:" + test_start + " UTC / GMT \nTest End  :" + test_end + " UTC / GMT "
    #test_header_info = "![](index.php? / attachments / get / 114459)\n" + test_header_info

    if globals()['test_comments'] == '':
        testrail_comments = test_header_info + '\nNo comments were set'
    else:
        testrail_comments = test_header_info + globals()['test_comments']

    return testrail_comments


def create_jenkins_url_to_log_folder(jenkins_url, output_dir):
    """
    To be used in the keyword, 'create url to log folder' to handle creation
    of the URL for Jenkins.
    """
    url_template = "{jenkins_url_ph}/job/{build_name_ph}/ws/{subfolder_ph}/glados/logs/{test_run_ph}/{test_folder_ph}"

    # The name of the Jenkins build will be the directory above 'glados'
    # IE.  C:\Jenkins\workspace\glados_PerformanceTesting\glados\logs\15049_chrome_1234\testFolder
    # To grab, 'glados_PerformanceTesting' we can split around 'glados\logs'
    # then split again and grab the last element.

    split_path = output_dir.split(os.sep + 'glados' + os.sep + 'logs' + os.sep)

    build_name = split_path[0]
    # Possible beginning of output_dir: "/var/www/jenkins/workspace/", "C:/Jenkins/workspace/"
    # remove everything from the beginning of the string to "/jenkins/workspace/" (case insensitive)
    build_name = re.sub(re.compile("^.*?[/\\\\]jenkins[/\\\\]workspace[/\\\\]", re.I), '', build_name)

    subfolder = ""
    if build_name.count(os.sep) > 0:
        build_name, subfolder = build_name.split(os.sep, 1)

    test_run, test_folder = split_path[1].split(
        os.sep)  # e.g. 15049_chrome_1234 as the test run, 'testFolder' as test folder

    log_folder_url = url_template.format(jenkins_url_ph=jenkins_url, build_name_ph=build_name, subfolder_ph=subfolder,
                                         test_run_ph=test_run, test_folder_ph=test_folder)

    # now do some clean up for special characters
    log_folder_url = urllib.parse.quote(log_folder_url, "/:")

    return log_folder_url

##-------------------------------------unused section-------------------------------------------------##
# this function was used in the capture page screenshot etc. in the glados_keywords.txt, so it maybe can be used later but not now
#todo need modify the try/except part
def set_testrail_comment(comment, clear_previous = 'False'):
    """
    Appends comment to string testrail_comments
    :param comment:
    :param clear_previous: If clear_previous is set to 'True'. The existing testrail_comments string is cleared, before adding a comment.
    :return:
    """
    try:
        test_comments
    except NameError:
        comment_exist = 'False'

    #option 1:
    if comment_exist =='False':
        testrail_comments = comment
    elif comment_exist == 'True' and clear_previous == 'True':
        testrail_comments = comment
    elif comment_exist == 'True' and clear_previous == 'False':
        testrail_comments = testrail_comments + '\n' + comment
