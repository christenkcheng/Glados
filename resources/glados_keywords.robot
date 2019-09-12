*** Settings ***
Library           Collections
Library           String
Library           OperatingSystem
Library           testrail_api_glados.py
Library           glados_helper_functions.py
Resource          rf_Shinigami_AppEyes/applitools.robot

*** Variables ***
${PLATFORMLIBRARY_DESKTOP}    SeleniumLibrary    # Desktop Library    
${PLATFORMLIBRARY_MOBILE}    ${CURDIR}/../mobile_resources/SpartanLibrary.py    # Mobile library
*** Keywords ***
-- GLADOS --

glados setup
    ${UTC_TIME_START} =    get time    epoch    UTC
    # Make sure required variables are set
    ${ENVIRONMENT} =    get variable value    ${ENVIRONMENT}    staging
    ${BROWSER} =    get variable value    ${BROWSER}    chrome
    ${PLATFORM}=    get variable value    ${PLATFORM.upper()}    WINDOWS
    ${PLATFORMNAME}=    get variable value    ${PLATFORMNAME.upper()}    ${PLATFORM}
    ${VERSION} =    get variable value    ${VERSION}    ${EMPTY}
    # Make sure optional variables exist
    ${JENKINS_URL} =    get variable value    ${JENKINS_URL}    ${EMPTY}
    ${REMOTE} =    get variable value    ${REMOTE}    ${EMPTY}
    ${MULTI_REPO_TEST}=    get variable value    ${MULTI_REPO_TEST}    ${False}
    ${DEVICE}=    get variable value    ${DEVICE}    ${EMPTY}
    # Set all to global variables
    set global variable    ${UTC_TIME_START}
    set global variable    ${ENVIRONMENT}
    set global variable    ${BROWSER}
    set global variable    ${JENKINS_URL}
    set global variable    ${REMOTE}
    set global variable    ${PLATFORMNAME}
    set global variable    ${PLATFORM}
    set global variable    ${VERSION}
    set global variable    ${MULTI_REPO_TEST}
    set global variable    ${DEVICE}
    platform library setup
    Register Keyword To Run On Failure    NOTHING

platform library setup
    [Documentation]    Switches between desktop "selenium2library" and mobile "spartan" library. 
    ...    Checks if a "DEVICE" variable is declared, if not then it will use Desktop library.
    ${PLATFORMLIBRARY}=    set variable if    '${device}' != '${EMPTY}'    ${PLATFORMLIBRARY_MOBILE}    ${PLATFORMLIBRARY_DESKTOP}
    Import Library    ${PLATFORMLIBRARY}

update testrail
    [Arguments]    ${override_run_id}=${EMPTY}    ${override_case_id}=${EMPTY}
    [Documentation]    Updates the test case on Testrail.
    ...
    ...    This keyword only works in a test case teardown.
    ...
    ...    When adding this to a test teardown keyword, be sure to place it before browsers are closed.
    ...
    ...    The following values are valid for status and correspond to: 1 - Pass, 2 - Blocked, 3 - Untested, 4 - Retest, 5 - Fail, 6 - N/A, 7 - Script Error
    ...
    ...    If any testrail comments were set using 'set testrail comment' they will be added to that test case. If "${skipUpdateTestRail}" set in the yaml config file is set to 'True' this keyword will not update. Set to 'False' to update.
    # Determine time elapsed
    ${time_elapsed}    ${time_started}    ${time_ended} =    determine time elapsed
    # Prepare comments to be sent
    ${TESTRAIL_COMMENTS} =    prepare testrail comments
    log    ${TESTRAIL_COMMENTS}
    # Set test result to use for updating testrails
    ${testresult} =    set variable if    "${TEST STATUS}" == "PASS"    1    5
    ${override_result_exist} =    run keyword and return status    variable should exist    ${OVERRIDE_TEST_RESULT}
    ${testresult} =    set variable if    '${override_result_exist}' == 'True'    ${OVERRIDE_TEST_RESULT}    ${testresult}    # set to test result override variable if it was created
    # Setup Block if test failed during setup and no other override
    ${failed_setup}=    Run Keyword And Return Status    Should Contain    ${TESTRAIL_COMMENTS}    Setup failed:
    ${testresult} =    set variable if    ${failed_setup} and not ${override_result_exist}    2    ${testresult}
    # Get Browser version
    ${browserIsOpen} =    is a browser open
    ${browser_version} =    Run Keyword If    ${browserIsOpen}    get browser version
    # Update test case result on TestRail
    ${RUN_ID} =    get variable value    ${RUN_ID}    ${EMPTY}
    ${CASE_ID} =    get variable value    ${${TEST NAME}_CASE_ID}    ${EMPTY}
    ${RUN_ID} =    set variable if    "${override_run_id}" != "${EMPTY}"    ${override_run_id}    ${RUN_ID}
    ${CASE_ID} =    set variable if    "${override_case_id}" != "${EMPTY}"    ${override_case_id}    ${CASE_ID}
    run keyword if    "${RUN_ID}" != "${EMPTY}" and "${CASE_ID}" != "${EMPTY}"    Wait Until Keyword Succeeds    60    3    add_test_result    ${RUN_ID}    ${CASE_ID}    ${testresult}    ${TESTRAIL_COMMENTS}
    ...    ${time_elapsed}    ${BROWSER}    ${browser_version}    ${environment}

get browser name
    [Documentation]    Returns the browser name that the test uses. (ie. ff -> firefox)
    ${lib}=    Set Variable If    '${DEVICE}' != '${EMPTY}'    SpartanLibrary    ${PLATFORMLIBRARY_DESKTOP}
    ${driver} =    get library instance    ${lib}
    # Check if a browser is open
    ${browser_open} =    run keyword and return status    wait until keyword succeeds    5s    1s    get title
    Return from keyword If    '${browser_open}' == 'False'    "Browser is not open."
    ${caps} =    Set Variable If    '${DEVICE}' != '${EMPTY}'    ${driver._current_application().capabilities}    ${driver._current_browser().capabilities}
    ${browser_name} =    Get Variable Value    ${caps['browserName']}
    return from keyword    ${browser_name}

get browser version
    [Documentation]    Returns the browser's version number.
    ...
    ...    Since this gets the library instance of the Selenium2Library, this will fail if that library is not an import. This is the case if Appium is being used.
    ...
    ...    If no browser is open when the keyword runs, the browser version will be 'Browser was not open, could not get browser version.'
    # Check to make sure selenium2library is being used
    ${is_selenium}=    is using seleniumlibrary
    # Return device if present else version (from SpartanLibrary) if not selenium2library
    Return From Keyword If    '${is_selenium}'=='False' and '${DEVICE}'!=''    ${DEVICE}
    Return From Keyword If    '${is_selenium}'=='False'    ${VERSION}
    # Get Browser version
    ${s2l} =    get library instance    ${PLATFORMLIBRARY_DESKTOP}
    # Check if a browser is open
    ${browser_open} =    run keyword and return status    wait until keyword succeeds    5s    1s    get title
    ${caps} =    set variable if    '${browser_open}' == 'True'    ${s2l._current_browser().capabilities}
    # Check that browser version variable is selenium 3 variety
    ${selenium_version}=    get selenium version
    Return From Keyword If    '${browser_open}' == 'False'    Browser was not open, could not get browser version.
    ${browser_version}=    Get Variable Value    ${caps['browserVersion']}    ${caps['version']}
    Return From Keyword    ${browser_version}

create url to log folder
    [Documentation]    Returns a string that can be pasted into the address bar of the browser that will
    ...    take the user to log folder of the test case/suite.
    ${local_computer} =    evaluate    r"file:////${OUTPUT DIR}"    # if ran locally, this is the string needed
    # Creating the string when running from Jenkins takes more work
    ${from_jenkins} =    run keyword if    "${JENKINS_URL}" != ""    create_jenkins_url_to_log_folder    ${JENKINS_URL}    ${OUTPUT DIR}
    # Decide which to use
    ${url} =    set variable if    "${from_jenkins}" == "None"    ${local_computer}    ${from_jenkins}
    return from keyword    ${url}

get platform name
    [Documentation]    Returns the platform name that the selenium2library uses. (ie. windows, mac, ios, android)
    ${s2l} =    get library instance    ${PLATFORMLIBRARY_DESKTOP}
    ${platform_name} =    set variable    ${s2l._current_browser().capabilities['platformName']}
    return from keyword    ${platform_name}

get selenium version
    [Documentation]    Returns the selenium version being used. (ex: 2 or 3)
    ...
    ...    Useful for determining if using selenium3 or selenium2.
    # Check to make sure selenium2library is being used
    ${is_selenium}=    is using seleniumlibrary
    Return From Keyword If    '${is_selenium}'=='False'    None
    # Get Browser version
    ${selenium}=    get library instance    ${PLATFORMLIBRARY_DESKTOP}
    # Check if a browser is open
    ${browser_open} =    run keyword and return status    get window titles
    ${caps} =    set variable if    '${browser_open}' == 'True'    ${selenium._current_browser().capabilities}
    # Check that browser version variable is selenium 3 variety
    ${is_selenium_3_browser}=    Run Keyword And Return Status    Dictionary Should Contain Key    ${caps}    browserVersion
    ${selenium_version}=    Set Variable If    ${is_selenium_3_browser}    3    2
    Return From Keyword    ${selenium_version}

-- TESTRAIL --

set testrail comment
    [Arguments]    ${comment}    ${clear_previous}=False    # If ${clear_previous} is set to 'True'. The existing ${TESTRAIL_COMMENTS} string is cleared, before adding a comment.
    [Documentation]    Appends to ${comment} to string ${TESTRAIL_COMMENTS}.
    ...
    ...    If ${TESTRAIL_COMMENTS} does not exist, it is created as a suite level variable with the value of ${comment}.
    ${status} =    run keyword and return status    variable should exist    ${TESTRAIL_COMMENTS}
    # Option 1: If no previous comments, create one
    run keyword if    '${status}' == 'False'    set test variable    ${TESTRAIL_COMMENTS}    ${comment}
    # Option 2: Clear comments before adding
    run keyword if    '${status}' == 'True' and '${clear_previous}' == 'True'    set test variable    ${TESTRAIL_COMMENTS}    ${comment}
    # Option 3: Add comment to existing
    run keyword if    '${status}' == 'True' and '${clear_previous}' == 'False'    set test variable    ${TESTRAIL_COMMENTS}    ${TESTRAIL_COMMENTS}\n${comment}

override test result to blocked
    [Arguments]    ${msg}="Test is blocked"
    [Documentation]    If used, Testrail will update the result of the test case with "BLOCKED" regardless of Robot Framework result. Then fails the test to stop further execution of test steps.
    ...
    ...    The following values are valid for status and correspond to: 1 - Pass, 2 - Blocked, 3 - Untested, 4 - Retest, 5 - Fail, 6 - N/A, 7 - Script Error
    set test variable    ${OVERRIDE_TEST_RESULT}    2
    Run Keyword If    ${MULTI_REPO_TEST}    Append To File    ${MULTI_REPO_DATA_FILE}    TESTRAIL_RESULT = [2, "${msg}"]${\n}
    fail    ${msg}

override test result to retest
    [Arguments]    ${msg}=Test needs retest
    [Documentation]    If used, Testrail will update the result of the test case with "RETEST" regardless of Robot Framework result.
    ...
    ...    The following values are valid for status and correspond to: 1 - Pass, 2 - Blocked, 3 - Untested, 4 - Retest, 5 - Fail, 6 - N/A, 7 - Script Error
    ...
    ...    *Argument(s):*
    ...    - ${msg} - The message that you set to explain why the case is set as retest or what should be done the next
    set test variable    ${OVERRIDE_TEST_RESULT}    4
    Set Test Message    ${msg}
    Run Keyword If    ${MULTI_REPO_TEST}    Append To File    ${MULTI_REPO_DATA_FILE}    TESTRAIL_RESULT = [4, ""]${\n}

override test result to na
    [Arguments]    ${msg}="Test is N/A"
    [Documentation]    If used, Testrail will update the result of the test case with "N/A" regardless of Robot Framework result. Then fails the test to stop further execution of test steps.
    ...
    ...    The following values are valid for status and correspond to: 1 - Pass, 2 - Blocked, 3 - Untested, 4 - Retest, 5 - Fail, 6 - N/A, 7 - Script Error
    set test variable    ${OVERRIDE_TEST_RESULT}    6
    Run Keyword If    ${MULTI_REPO_TEST}    Append To File    ${MULTI_REPO_DATA_FILE}    TESTRAIL_RESULT = [6, "${msg}"]${\n}
    fail    ${msg}

override test result to script error
    [Arguments]    ${msg}="Test has an Error"
    [Documentation]    If used, Testrail will update the result of the test case with "Script Error" regardless of Robot Framework result. Then fails the test to stop further execution of test steps.
    ...
    ...    The following values are valid for status and correspond to: 1 - Pass, 2 - Blocked, 3 - Untested, 4 - Retest, 5 - Fail, 6 - N/A, 7 - Script Error
    set test variable    ${OVERRIDE_TEST_RESULT}    7
    Run Keyword If    ${MULTI_REPO_TEST}    Append To File    ${MULTI_REPO_DATA_FILE}    TESTRAIL_RESULT = [7, "${msg}"]${\n}
    fail    ${msg}
    
-- SCREENSHOTS --

capture page screenshot in sections
    [Arguments]    ${image_name}
    [Documentation]    Since the Chrome and IE browsers only takes screenshots of the viewable portion in a browser window, multiple screenshots may be necessary.
    ...
    ...    Depending on the browser height and height of the page content, determines how many screenshots are needed to capture the entire height of the pages and takes the screenshots.
    ...
    ...    NOTE: If the browser window is not wide enough to capture all the page content, this keyword will not capture the width that is cut off.
    ...
    ...    Returns a list of the screenshot names.
    # Scroll to the top
    execute javascript    window.scrollTo(0,0);
    # Determine length of page content
    ${pixel length} =    execute javascript    var length = document.body.scrollHeight; return length;
    # Determine how much the browser window can display at once
    ${viewport height} =    execute javascript    var viewport_len = window.innerHeight; return viewport_len;
    # Determine number of screenshots needed
    ${screenshots} =    evaluate    math.ceil(float(${pixel length}) /float(${viewport height}))    math
    ${y axis} =    set variable    0
    ${names} =    create list
    # Take the screenshots
    : FOR    ${index}    IN RANGE    ${screenshots}
    \    execute javascript    window.scrollTo(0,${y axis});
    \    sleep    0.5
    \    capture page screenshot    ${image_name}_${index}.png
    \    ${y axis} =    evaluate    ${y axis} + ${viewport height}
    \    append to list    ${names}    ${image_name}_${index}.png
    # Return a list of the names
    return from keyword    ${names}

capture page screenshot and return url
    [Arguments]    ${image_name}    ${set as comment}=True
    [Documentation]    Takes a screenshot and returns a list of URLs where the file is hosted.
    ...
    ...    Multiple urls can be given if multiple screenshots had to be taken to capture the whole pages, as is the case when using the Chrome browser.
    ...
    ...    An image name needs to be given as an argument. Do not include the extension.
    ...
    ...    By default it will automatically set the TestRail comment using the correct syntax so the image will appear inline on TestRail.
    @{file urls} =    create list
    # Take screenshots depending on browser
    ${browser_name} =    get browser name
    ### Create list for single screenshot browsers
    @{single screenshot browsers} =    Create List    internet explorer    ie
    ## Add firefox to the single screenshot list if on selenium 2
    ${selenium_version}=    get selenium version
    Run Keyword If    '${browser_name}'=='firefox' and '${selenium_version}'=='2'    Append To List    ${single screenshot browsers}    firefox    ff
    ### determine if browser is single screenshot or multi screenshot
    ${lowercase browser name} =    Evaluate    "${browser_name}".lower()
    ${only need one screenshot} =    Run Keyword And Return Status    List Should Contain Value    ${single screenshot browsers}    ${lowercase browser name}
    @{images} =    run keyword unless    ${only need one screenshot}    capture page screenshot in sections    ${image_name}
    run keyword if    ${only need one screenshot}    capture page screenshot    ${image_name}.png
    @{image} =    run keyword if    ${only need one screenshot}    create list    ${image_name}.png
    @{screenshots} =    set variable if    not ${only need one screenshot}    ${images}    ${image}
    # Determine location
    ${dir_url} =    create url to log folder
    # For each image uploaded, create a url/path and add it to the list
    : FOR    ${screenshot}    IN    @{screenshots}
    \    ${screenshot} =    evaluate    r"${screenshot}" if "${JENKINS_URL}" == "" else urllib.quote("${screenshot}", "/:")    urllib    # make the image name friendly if the path is a URL
    \    ${file url} =    set variable    ${dir url}/${screenshot}
    \    ${comment_syntax} =    set variable if    "${JENKINS_URL}" == ""    Paste the following URL into the address bar to view the image.\n${file url}    ![${image_name}] (${file url})
    \    run keyword if    '${set as comment}' == 'True'    set testrail comment    ${comment_syntax}
    \    append to list    ${file urls}    ${file url}
    return from keyword    @{file urls}

get node name
    [Documentation]    Returns the name of the node that is running the opened browser. \ Returns the IP if the name cannot be resolved. Returns a message if the test was ran locally.
    # Determine Session ID
    ${hostname} =    evaluate    socket.gethostname()    socket
    ${driver}=    Set Variable If    '${DEVICE}' != '${EMPTY}'    SpartanLibrary    ${PLATFORMLIBRARY_DESKTOP}
    ${driver_library}    get library instance    ${driver}
    ${session_id} =    Set Variable If    '${DEVICE}' != '${EMPTY}'    ${driver_library._current_application().session_id}    ${driver_library._current_browser().session_id}
    # Extract Hub URL from REMOTE variable
    run keyword if    "${REMOTE}" == "${EMPTY}"    return from keyword    ${hostname}
    ${port} =    set variable    4444
    ${hubURL} =    evaluate    "${REMOTE}".split("${port}")[0] + "${port}"
    ${testSessionURL} =    set variable    ${hubURL}/grid/api/testsession?session=${session_id}    # api call will return info about the session
    # Query Hub using Session ID to determine IP
    ${response} =    evaluate    requests.get("${testSessionURL}").json()    requests
    ${port_ext}=    Set Variable If    '${DEVICE}' != '${EMPTY}'    ":4750"    ":5555"
    ${ip} =    evaluate    "${response['proxyId']}".replace(${port_ext}, "").replace("http://", "")
    # Get name of IP address
    ${status}    ${msg} =    run keyword and ignore error    evaluate    socket.gethostbyaddr("${ip}")[0]    socket    # fails when executed from Jenkins.
    ...    # Won't be able to return a name, only IP.
    ${node} =    set variable if    "${status}" == "FAIL"    ${ip}    ${msg}
    # Return node name
    return from keyword    ${node}

determine time elapsed
    [Documentation]    Returns the time elapsed, time started, and time ended. \ Relies on the \ global variable 'UTC_TIME_START' to exist which should be set in the 'glados setup' keyword.
    ${UTC_TIME_END} =    get time    epoch    UTC
    ${time_elapsed} =    evaluate    1 if int(${UTC_TIME_END}) - int(${UTC_TIME_START}) < 1 else int(${UTC_TIME_END}) - int(${UTC_TIME_START})    # Set to 1 second if less than 1, other wise TestRail API throws an error for values < 1
    ${time_started} =    get time    timestamp    ${UTC_TIME_START}
    ${time_started} =    evaluate    '${time_started}'.split(' ')[1]
    ${time_ended} =    get time    timestamp    ${UTC_TIME_END}
    ${time_ended} =    evaluate    '${time_ended}'.split(' ')[1]
    return from keyword    ${time_elapsed}    ${time_started}    ${time_ended}

prepare testrail comments
    [Documentation]    Formats the TestRail comment output. \ Returns the markup string of all TestRail comments.
    # Determine time elapsed
    ${time_elapsed}    ${time_started}    ${time_ended} =    determine time elapsed
    # Determine the name of the computer the browser was ran on
    ${browser_open} =    is a browser open
    ${computer_name} =    run keyword if    ${browser_open}    get node name
    # Format comments
    ${TESTRAIL_COMMENTS} =    get variable value    ${TESTRAIL_COMMENTS}    No comments were set.
    ${test_msg_len} =    get length    ${TEST MESSAGE}
    ${TEST MESSAGE} =    set variable if    ${test_msg_len} > 0    ${TEST MESSAGE}    No error messages from Robot Framework.
    ${log_url} =    create url to log folder
    ${test_header_info} =    set variable    The log file can be viewed [here](${log_url}/log.html).\n\nROBOT FRAMEWORK MESSAGE:\n${TEST MESSAGE}\n\nTest Start: ${time_started} UTC/GMT\nTest End: ${time_ended} UTC/GMT\n\nTest was executed on: ${computer_name}\n- - - -\n
    ${test_header_info} =    set variable if    "${TEST STATUS}" == "FAIL"    ![](index.php?/attachments/get/114459)\n${test_header_info}    ${test_header_info}
    ${TESTRAIL_COMMENTS} =    set variable    ${test_header_info}${TESTRAIL_COMMENTS}
    return from keyword    ${TESTRAIL_COMMENTS}

is using seleniumlibrary
    [Documentation]    Returns True if the SeleniumLibrary is in use, False otherwise. \ Useful when needing to determine if SeleniumLibrary is in use instead of Appium.
    ${using_selenium} =    run keyword and return status    get library instance    ${PLATFORMLIBRARY_DESKTOP}
    return from keyword    ${using_selenium}


