*** Settings ***
Documentation     This resource contains keywords pertaining to Applitools.
Library           Collections
Library           String
Library           OperatingSystem
Resource          screenshots.robot
Library           rf_Shinigami_AppEyes.py

*** Variables ***
${min_page_width}    1000
${min_page_height}    800

*** Keywords ***
Applitools Close Eyes Session
    [Documentation]    Closes the Applitools Eyes Session
    ...
    ...    *Returns:*
    ...    - _status_ - Status of Eyes Session. Returns "PASS" or "FAIL"
    ...    - _msg_ - Error message of Eyes Session. Parsed by "parse applitools error message"
    ${status}    ${msg}=    Run Keyword And Ignore Error    Close Eyes Session
    ${msg}=    parse applitools error message    ${msg}
    Return From Keyword    ${status}    ${msg}

Applitools Open Eyes Session
    [Arguments]    ${appname}    ${testname}    ${matchlevel}=LAYOUT2    ${includeEyesLog}=False    ${httpDebugLog}=False    ${cssTransition}=True
    ...    ${baselineName}=${None}    ${batch}=${None}
    [Documentation]    Opens an Applitools Eyes Session
    ...    - API key is set, location is grabbed from current page.
    ...    - Testname will append Environment
    ...    - Testname will append Browser if crossbrowser is disabled
    ...
    ...    NOTE: The API key must be set as a Global Variable in your vertical's setup keyword as "APPLITOOLS_APIKEY"
    ...    
    ...    See "Open Eyes Session" for more information.
    ...
    ...    *Arguments:*
    ...    - _appname_ - Application name
    ...    - _testname_ - Test name
    ...    - _matchlevel_ - Applitools Match Level for comparison. Can be STRICT, LAYOUT, LAYOUT2, or CONTENT. Set to LAYOUT2 by default.
    ...    - _includeEyesLog_ - Set to False by default
    ...    - _httpDebugLog_ - Set to False by default
    ...    - _cssTransition_ - Determines whether to scroll through page or use css transitioning. Set to True by default.
    ...    - _baselineName_ - Name of baseline to compare to. Tests with the same baselineName will be tested against each other. Set to None by default.
    ...    - _batch_ - The batch to place the test into. Should be a BatchInfo object created by "Create Eyes Batch". Set to None by default.
    # Check if Applitools API Key was set to a global variable
    ${apikey_available}=    Run Keyword And Return Status    Variable Should Exist    ${APPLITOOLS_APIKEY}
    Run Keyword Unless    ${apikey_available}    override test result to blocked    An Applitools API Key was not available to open a session. The API key must be set as a Global Variable in a setup keyword as "APPLITOOLS_APIKEY"
    # Determine text to attach to test/baseline name
    ${crossBrowser_enabled}=    is applitools cross browser enabled
    ${end_text}=    Set Variable If    ${crossBrowser_enabled}    ${ENVIRONMENT}    ${ENVIRONMENT} ${BROWSER}    # Separated by browser if not crossbrowser
    # Set test/baseline name
    ${testname}=    Catenate    ${testname}    ${end_text}    # Currently separated by environment
    ${baselineName}=    Catenate    ${baselineName}    ${end_text}    # Currently separated by environment
    ${status}    ${message}=    Run Keyword And Ignore Error    Variable Should Exist    ${DEVICE}
    ${device}=    Set Variable If    "${status}" == "FAIL"    ${none}    ${DEVICE.lower()}
    Open Eyes Session    appname=${appname}    testname=${testname}    apikey=${APPLITOOLS_APIKEY}    matchlevel=${matchlevel}    includeEyesLog=${includeEyesLog}
    ...    httpDebugLog=${httpDebugLog}    use_css_transition=${cssTransition}    baselineName=${baselineName}    batch=${batch}

is applitools cross browser enabled
    [Documentation]    Returns whether cross browser testing is enabled
    ...
    ...    *Returns:*
    ...    - _crossBrowser_enabled_ - (Boolean) True if cross browser testing is enabled. False otherwise.
    ${test_is_cross_browser}=    Get Variable Value    ${CROSS_BROWSER_TEST}    ${False}
    ${testrun_is_cross_browser}=    Get Variable Value    ${CROSS_BROWSER_TESTRUN}    ${False}
    ${crossBrowser_enabled}=    Evaluate    '${test_is_cross_browser}'.lower() == 'true' or '${testrun_is_cross_browser}'.lower() == 'true'
    Return From Keyword    ${crossBrowser_enabled}

set test to enable applitools cross browser
    [Documentation]    Sets the current test running this keyword to use cross browser testing for Applitools
    Set Test Variable    ${CROSS_BROWSER_TEST}    ${True}

parse applitools error message
    [Arguments]    ${msg}
    [Documentation]    Parse the Applitools error message to be more readable on TestRail
    ...
    ...    *Returns:*
    ...    - _msg_ - Parsed Applitools error message
    ...
    ...    *Example:*
    ...
    ...    _Original:_
    ...    | TestFailedError: '<TEST_NAME>' of '<APP_NAME>'. See details at <URL> , Existing test [ steps: 1, matches: 0, mismatches: 1, missing: 0 ], URL: <URL>
    ...
    ...    _Parsed:_
    ...    | Applitools Fail: '<TEST_NAME>' of '<APP_NAME>'.
    ...    | URL: [Applitools Eyes Comparison](<URL>)
    ...    | Existing test [ steps: 1, matches: 0, mismatches: 1, missing: 0 ]
    ${is_string}=    Run Keyword And Return Status    Should Be String    ${msg}
    Run Keyword Unless    ${is_string}    Return From Keyword    ${msg}
    # Parse error message
    ${msg}=    Replace String    ${msg}    TestFailedError    Applitools Fail
    ${msg}=    Replace String    ${msg}    See details at${SPACE}    \nURL: [Applitools Eyes Comparison](
    ${msg}=    Replace String    ${msg}    /batches/    /sessions/
    ${msg}=    Replace String    ${msg}    ${SPACE}, Existing test    \nExisting test
    ${msg}=    Replace String Using Regexp    ${msg}    ], URL.*    ]
    Return From Keyword    ${msg}

capture page screenshot and check eyes window
    [Arguments]    ${appname}    ${testname}    ${image_name}    ${set_as_comment}=True    ${matchlevel}=LAYOUT2    ${cssTransition}=True
    ...    ${hideScrollbars}=True    ${includeEyesLog}=False    ${httpDebugLog}=False    ${batch}=${None}
    [Documentation]    Captures a full page screenshot and submits the image to Applitools for comparison
    ...    - Takes a screenshot and returns a list of URLs where the file is hosted.
    ...    - Multiple urls can be given if multiple screenshots had to be taken to capture the whole pages, as is the case when using the Chrome browser.
    ...
    ...    - Returns from keyword if we want to skip Applitools via global variable SKIP_APPLITOOLS
    ...
    ...    - Checks the page against and Applitools baseline. Uses image_name argument as baseline name.
    ...    - See "Open Eyes Session" for more information.
    ...
    ...    *Arguments:*
    ...    - _appname_ - Application name
    ...    - _testname_ - Test name
    ...    - _image_name_ - Name of image(s) to be saved. Do not include the extension.
    ...    - _set_as_comment_ - Set as a TestRail comment. By default it will automatically set the TestRail comment using the correct syntax so the image will appear inline on TestRail.
    ...    - _matchlevel_ - Applitools Match Level for comparison. Can be STRICT, LAYOUT, LAYOUT2, or CONTENT. Set to LAYOUT2 by default.
    ...    - _cssTransition_ - Use CSS Transition instead of actual scrolling for full page screenshots. Set to True by default.
    ...    - _hideScrollbars_ - Hides scrollbars for screenshots. Set to True by default.
    ...    - _includeEyesLog_ - Set to False by default
    ...    - _httpDebugLog_ - Set to False by default
    ...    - _baselineName_ - Name of baseline to compare to. Tests with the same baselineName will be tested against each other. Set to None by default.
    ...    - _batch_ - The batch to place the test into. Should be a BatchInfo object created by "Create Eyes Batch". Set to None by default.
    ...
    ...    *Returns:*
    ...    - _status_ - Applitools Check Window status. Can be "PASS" or "FAIL"
    ...    - _msg_ - Applitools Check Window message
    ...    - _screenshot_data_ - Dictionary containing the following
    ...    - _screenshot_ - URL for full page screenshot taken
    ...    - _comment_msg_ - Message to set as Testrail comment
    # Check if we want to skip applitools check
    ${has_skip_applitools_param}=    Run Keyword And Return Status    Variable Should Exist    ${SKIP_APPLITOOLS}
    ${skip_applitools}=    Set Variable If    ${has_skip_applitools_param}    ${SKIP_APPLITOOLS}    ${False}
    ${skip_applitools}=    Evaluate    '${skip_applitools}'.lower() == 'true'
    # Prepare viewport and return page overflow value
    prepare viewport for full page screenshot
    # Basic screenshot
    ${applitools_message}=    Set Variable If    ${skip_applitools}    Applitools check was skipped. Review screenshots manually.    \#Applitools Testing:#\n- App Name: ${appname}\n- Test Name: ${testname}\n- Test Mode: ${matchlevel}
    ${comment_msg}=    Set Variable    \n${applitools_message}\n\n**Image Name:** ${image_name}
    Run Keyword If    '${set_as_comment}'.lower() == 'true'    set testrail comment    ${comment_msg}
    ${screenshot}=    capture full page screenshot    ${image_name}    ${set_as_comment}    cssTransition=${cssTransition}
    ${screenshot_data}=    Create Dictionary    screenshot=${screenshot}    comment_msg=${comment_msg}
    # Skip applitools
    Run Keyword If    ${skip_applitools}    Maximize Browser Window
    Return From Keyword If    ${skip_applitools}    \FAIL    Applitools check was skipped. Review screenshots manually.    ${screenshot_data}
    # Get image name to pass to Applitools
    ${dir_url} =    create url to log folder
    ${unique_image_name}=    Remove String    ${screenshot}    ${dir_url}/
    # Run applitools check if it is not skipped
    Applitools Open Eyes Session    appname=${appname}    testname=${testname}    matchlevel=${matchlevel}    includeEyesLog=${includeEyesLog}    httpDebugLog=${httpDebugLog}    baselineName=${image_name}
    ...    batch=${batch}    cssTransition=${cssTransition}
    Compare Image    ${OUTPUT_DIR}/${unique_image_name}    ${image_name}
    ${status}    ${msg}=    Applitools Close Eyes Session
    # Cypher will just comment out the keyword "Maximize Browser Window", so going to use the keyword without any safari check
    Maximize Browser Window    # Maximize window again
    Return From Keyword    ${status}    ${msg}    ${screenshot_data}

capture screenshot and check eyes selector
    [Arguments]    ${locator}    ${appname}    ${testname}    ${image_name}    ${set_as_comment}=True    ${matchlevel}=STRICT
    ...    ${scrollToElement}=True    ${includeEyesLog}=False    ${httpDebugLog}=False    ${batch}=${None}    ${force_full_page_screenshots}=True
    [Documentation]    Captures a full page screenshot, crops the image to the element specified, and submits the image to Applitools for comparison
    ...    - Takes a screenshot and returns a list of URLs where the file is hosted.
    ...    - Multiple urls can be given if multiple screenshots had to be taken to capture the whole pages, as is the case when using the Chrome browser.
    ...
    ...    - Returns from keyword if we want to skip Applitools via global variable SKIP_APPLITOOLS
    ...
    ...    - Checks the page against and Applitools baseline. Uses image_name argument as baseline name.
    ...    - See "Open Eyes Session" for more information.
    ...
    ...    *Arguments:*
    ...    - _locator_ - The element locator (Only css or xpath locators are allow).
    ...    - _appname_ - Application name
    ...    - _testname_ - Test name
    ...    - _image_name_ - Name of image(s) to be saved. Do not include the extension.
    ...    - _set_as_comment_ - Set as a TestRail comment. By default it will automatically set the TestRail comment using the correct syntax so the image will appear inline on TestRail.
    ...    - _matchlevel_ - Applitools Match Level for comparison. Can be STRICT, LAYOUT, LAYOUT2, or CONTENT. Set to STRICT by default.
    ...    - _cssTransition_ - Use CSS Transition instead of actual scrolling for full page screenshots. Set to True by default.
    ...    - _hideScrollbars_ - Hides scrollbars for screenshots. Set to True by default.
    ...    - _includeEyesLog_ - Set to False by default
    ...    - _httpDebugLog_ - Set to False by default
    ...    - _baselineName_ - Name of baseline to compare to. Tests with the same baselineName will be tested against each other. Set to None by default.
    ...    - _batch_ - The batch to place the test into. Should be a BatchInfo object created by "Create Eyes Batch". Set to None by default.
    ...
    ...    *Returns:*
    ...    - _status_ - Applitools Check Window status. Can be "PASS" or "FAIL"
    ...    - _msg_ - Applitools Check Window message
    ...    - _screenshot_data_ - Dictionary containing the following
    ...    - _screenshot_ - URL for full page screenshots taken
    ...    - _comment_msg_ - Message to set as Testrail comment
    # Check if we want to skip applitools check
    ${has_skip_applitools_param}=    Run Keyword And Return Status    Variable Should Exist    ${SKIP_APPLITOOLS}
    ${skip_applitools}=    Set Variable If    ${has_skip_applitools_param}    ${SKIP_APPLITOOLS}    ${False}
    ${skip_applitools}=    Evaluate    '${skip_applitools}'.lower() == 'true'
    # Prepare viewport and return page overflow value
    prepare viewport for full page screenshot
    # Basic screenshot
    ${applitools_message}=    Set Variable If    ${skip_applitools}    Applitools check was skipped. Review screenshots manually.    \#Applitools Testing:#\n- App Name: ${appname}\n- Test Name: ${testname}\n- Test Mode: ${matchlevel}
    ${comment_msg}=    Set Variable    \n${applitools_message}\n\n**Image Name:** ${image_name}
    Run Keyword If    '${set_as_comment}'.lower() == 'true'    set testrail comment    ${comment_msg}
    ${screenshot}=    capture element screenshot    ${locator}    ${image_name}    ${set_as_comment}
    ${screenshot_data}=    Create Dictionary    screenshot=${screenshot}    comment_msg=${comment_msg}
    # Skip applitools
    Return From Keyword If    ${skip_applitools}    \FAIL    Applitools check was skipped. Review screenshots manually.    ${screenshot_data}
    # Get image name to pass to Applitools
    ${dir_url} =    create url to log folder
    ${unique_image_name}=    Remove String    ${screenshot}    ${dir_url}/
    # Run applitools check if it is not skipped
    Applitools Open Eyes Session    appname=${appname}    testname=${testname}    matchlevel=${matchlevel}    includeEyesLog=${includeEyesLog}    httpDebugLog=${httpDebugLog}    baselineName=${image_name}
    ...    batch=${batch}
    Compare Image    ${OUTPUT_DIR}/${unique_image_name}    ${image_name}
    ${status}    ${msg}=    Applitools Close Eyes Session
    # Return testrail comment and screenshots
    Return From Keyword    ${status}    ${msg}    ${screenshot_data}
    
calculate optimal viewport size for screenshots
    [Documentation]    Calcuates the best Viewport size to take partial screenshots that stitch into a full page screenshot with minimal whitespace
    ...    - Gets the site dimensions
    ...    - Calculates the maximum viewport size
    ...    - Calculates an optimal viewport size by dividing up pixels
    ...
    ...    *Returns:*
    ...    - _width_ - Viewport width
    ...    - _height_ - Viewport height
    # Get max browser dimensions
    Maximize Browser Window
    ${browser_width}    ${browser_height}=    Get Window Size
    Run Keyword And Ignore Error    Wait Until Keyword Succeeds    2    1    Fail    1 second sleep to wait for window size to settle.
    ${browser_width}    ${browser_height}=    Get Window Size
    ${browser_width}    ${browser_height}=    Get Window Size
    # Get max viewport
    Set Window Size    ${browser_width}    ${browser_height}
    Set Window Position    ${0}    ${0}
    Run Keyword And Ignore Error    Wait Until Keyword Succeeds    2    1    Fail    1 second sleep to wait for window size to settle.
    ${max_width}    ${max_height}=    Execute Javascript    return [window.innerWidth, window.innerHeight]
    # Get site dimensions
    Set Window Size    500    500    # Make window smaller to get min site size
    Run Keyword And Ignore Error    Wait Until Keyword Succeeds    2    1    Fail    1 second sleep to wait for window size to settle.
    ${page_width}    ${page_height}=    Execute Javascript    return [Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) , Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.body.clientHeight, document.documentElement.clientHeight)]
    ${page_width}    ${page_height}=    Set Variable    ${page_width + 2}    ${page_height + 2}    # Add 1 pixel border for edge cases
    # Create lists to pass to for loop, index 0=width, 1=height
    ${page_dimensions}    ${view_dimensions}=    Evaluate    [[${page_width}, ${page_height}] , [${max_width}, ${max_height}]]
    # Calculate viewport size
    : FOR    ${i}    IN RANGE    2    # Width and Height
    \    ${page_size}    ${view_size}=    Set Variable    ${page_dimensions[${i}]}    ${view_dimensions[${i}]}    # Set variables for readability
    \    ${num_screens}=    Evaluate    ${page_size} / ${view_size}    # This is the minimum number of full screenshots
    \    ${leftover_size}=    Evaluate    ${page_size} % ${view_size}    # This is the size of the rest of the page on the partial screenshot
    \    ${num_screens}=    Set Variable If    ${leftover_size} == ${0}    ${num_screens}    ${num_screens + 1}    # Add the partial screenshot that has the leftover
    \    ${whitespace_size}=    Evaluate    ${view_size} - ${leftover_size}    # This is the amount of whitespace there will be on the partial screenshot
    \    ${leftover_per_screen}=    Evaluate    ${whitespace_size} / ${num_screens}    # This is the amount we can subtract from each screenshot to remove whitespace
    \    ${view_size}=    Evaluate    ${view_size} - ${leftover_per_screen}    # Remove the excess space from the width of each screenshot
    \    ${view_size}=    Evaluate    ${view_size} + 1    # Update viewport size by one to make space for leftover pixels. Will have whitespace
    \    Set List Value    ${view_dimensions}    ${i}    ${view_size}    # Update value
    ${width}    ${height}=    Set Variable    @{view_dimensions}
    # Enforce minimum size
    ${width}=    Set Variable If    ${width} < ${min_page_width}    ${min_page_width}    ${width}
    ${height}=    Set Variable If    ${height} < ${min_page_height}    ${min_page_height}    ${height + 50}    # Applitools seems to remove a MAX_SCROLLBAR_HEIGHT, even when scrollbars are hidden...
    # Return
    Return From Keyword    ${width}    ${height}

set viewport size
    [Arguments]    ${width}    ${height}
    [Documentation]    Sets the Viewport size
    ...    - Calculates size of window border
    ...    - Adds window border to viewport size to get total window size
    ...    - Sets window size to new dimensions
    ...
    ...    *Arguments:*
    ...    - _width_ - Viewport width
    ...    - _height_ - Viewport height
    # Sets window size to un-maximize browser
    Set Window Size    ${width}    ${height}
    Wait For Condition    width_init = window.innerWidth; height_init = window.innerHeight; return (width_init == window.innerWidth) && (height_init == window.innerHeight)    # Wait for dimensions to stabilize: Gets initial dimensions. Compares it to new dimensions.
    # Calculate window border
    ${width_diff}    ${height_diff}=    Execute Javascript    return [window.outerWidth - window.innerWidth, window.outerHeight - window.innerHeight] 
    # Calculate total window size
    ${window_width}    ${window_height}=    Evaluate    [${width_diff} + ${width}, ${height_diff} + ${height}]
    # Sets total window size
    Set Window Size    ${window_width}    ${window_height}

prepare viewport for full page screenshot
    [Documentation]    Prepares the viewport to generate a full page screenshot. This keyword helps keep screenshots of pages to a minimum so that they are consistent between browsers/runs.
    ...    
    ...    *Returns:*
    ...    - _original_overflow_ - Page's overflow value is returned so changes can be reverted later
    # Set Viewport
    ${platformname}=    Get Variable Value    ${PLATFORMNAME}    ${EMPTY}
    ${width}    ${height}=    Run Keyword Unless    '${platformname.lower()}' == 'ios' or'${platformname.lower()}' == 'android'    calculate optimal viewport size for screenshots
    # Set viewport size to standardize page checks
    Run Keyword Unless    ${width}==${None} and ${height}==${None}    set viewport size    ${width}    ${height}
    # Scroll to the top
    Execute Javascript    window.scrollTo(0,0);