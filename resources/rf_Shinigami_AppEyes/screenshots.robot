*** Settings ***
Documentation     This resource contains keywords pertaining to screenshots
Library           image_handling.py

*** Keywords ***
capture full page screenshot
    [Arguments]    ${image_name}    ${set as comment}=True    ${cssTransition}=${True}
    [Documentation]    Captures a full page screenshot
    ...
    ...    *Arguments:*
    ...    - _image_name_ - Name to give image file
    ...    - _set_as_comment_ - (Boolean) True to set the image as a testrail comment.
    ...    - _cssTransition_ - (Optional) (Boolean) True if CSS transitioning should be used. False if scrolling should be used. Set to True by default
    ...
    ...    *Returns:*
    ...    - _image_url_ - URL of image screenshot
    # Scroll to top
    ${initial_scroll_x}    ${initial_scroll_y}=    Execute Javascript    var initial_scroll = [window.scrollX,window.scrollY]; window.scrollTo(0,0); return initial_scroll
    # Hide scrollbars
    ${overflow}=    Execute Javascript    var orig_overflow = document.documentElement.style['overflow']; document.documentElement.style['overflow'] = 'hidden'; return orig_overflow;
    # Check if full screen screenshot browser and return single screenshot
    ${browsers}=    Create List    ${EMPTY}
    ${single_screenshot}=    Evaluate    '${BROWSER}' in ${browsers}
    ${image_url}=    Run Keyword If    ${single_screenshot}    capture page screenshot and return url    ${image_name}    # Take single screenshot
    Run Keyword If    ${single_screenshot}    Run Keywords    Execute Javascript    document.documentElement.style['overflow'] = '${overflow}';
    ...    AND    Maximize Browser Window    # Reset browser
    Return From Keyword If    ${single_screenshot}    ${image_url}    # Return single screenshot
    # Initialize variables
    ${y_axis} =    set variable    ${0}
    ${image_map}=    Create List
    # Create unique image name for session
    ${rand_string}=    Generate Random String    3
    ${image_name}=    Set Variable    ${image_name}_${rand_string}
    # Determine how much the browser window can display at once
    ${viewport_height}    ${viewport_width}=    Execute Javascript    return [window.innerHeight, window.innerWidth];
    # Determine length of page content
    ${pixel_length} =    Execute Javascript    return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.body.clientHeight, document.documentElement.clientHeight)
    # Determine width of page content
    ${pixel_width} =    Execute Javascript    return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)
    # Determine number of screenshots needed vertically
    ${vert_screenshots}=    Evaluate    math.ceil(float(${pixel_length}) /float(${viewport_height}))    math
    # Determine number of screenshots needed horizontally
    ${horiz_screenshots}=    Evaluate    math.ceil(float(${pixel_width}) /float(${viewport_width}))    math
    # Get original page transformations
    ${original_transform}    ${original_webkit_transform}=    Execute Javascript    return [document.documentElement.style['transform'],document.documentElement.style['-webkit-transform']]
    # Take the screenshots
    : FOR    ${index}    IN RANGE    ${vert_screenshots}
    \    #CSS Transition / Scroll
    \    ${javascript}=    Set Variable If    ${cssTransition}    document.documentElement.style['transform'] = 'translate(0px, -${y_axis}px)'; document.documentElement.style['-webkit-transform'] = 'translate(0px, -${y_axis}px)';    window.scrollTo(0,${y_axis})
    \    Execute Javascript    ${javascript}
    \    Run Keyword And Ignore Error    Wait Until Keyword Succeeds    0.5s    0.5s    Fail    Wait for page to transition...
    \    #Get full width screenshots
    \    ${horiz_images}=    capture horizontal screenshots    ${image_name}_${index}    ${viewport_width}    ${horiz_screenshots}    ${cssTransition}
    \    #Increment page position
    \    ${y_axis} =    Evaluate    ${y_axis} + ${viewport_height}
    \    #Add list to image map
    \    Append To List    ${image_map}    ${horiz_images}
    # Reset page
    Execute Javascript    document.documentElement.style['overflow'] = '${overflow}';
    ${javascript}=    Set Variable If    ${cssTransition}    document.documentElement.style['transform'] = '${original_transform}'; document.documentElement.style['-webkit-transform'] = '${original_webkit_transform}';    window.scrollTo(0,0)
    Execute Javascript    ${javascript}
    Execute Javascript    window.scrollTo(${initial_scroll_x},${initial_scroll_y})
    # Determine location
    ${dir_url} =    create url to log folder
    # Return a list of the names
    Combine And Save Images In Map    ${image_map}    ${OUTPUT_DIR}/${image_name}.png
    # Determine screenshot multiplier
    ${image_width}    ${image_height}=    Get Image Size    ${OUTPUT_DIR}/${image_name}.png
    ${multiplier}=    Evaluate    round(float(${image_width}) / float(${viewport_width}*${horiz_screenshots}), 1)
    ${screenshot_width}    ${screenshot_height}=    Evaluate    [int(round(${pixel_width} * ${multiplier},0)), int(round(${pixel_length} * ${multiplier},0))]
    # Crop any extra space at bottom/right
    Crop Image    ${OUTPUT_DIR}/${image_name}.png    ${0}    ${0}    ${screenshot_width}    ${screenshot_height}
    # Handle for images more than 35k pixels long
    Run Keyword If    ${pixel_length} > ${35000}    Resize Image    ${OUTPUT_DIR}/${image_name}.png    ${OUTPUT_DIR}/${image_name}.png    height=${35000}    ELSE    Resize Image    ${OUTPUT_DIR}/${image_name}.png    ${OUTPUT_DIR}/${image_name}.png    width=${pixel_width}
    # Compress screenshots
    Convert To Jpg    ${OUTPUT_DIR}/${image_name}.png    ${OUTPUT_DIR}/${image_name}.jpg
    # Testrail handling
    ${comment_syntax} =    set variable if    "${JENKINS_URL}" == ""    Paste the following URL into the address bar to view the image.\n${dir_url}/${image_name}.jpg    ![${image_name}] (${dir_url}/${image_name}.jpg)
    run keyword if    '${set as comment}' == 'True'    set testrail comment    ${comment_syntax}
    return from keyword    ${dir_url}/${image_name}.jpg

capture horizontal screenshots
    [Arguments]    ${image_name}    ${viewport_width}    ${num_screenshots}    ${cssTransition}=${True}
    [Documentation]    Captures the full width of the page as screenshots
    ...
    ...    *Arguments:*
    ...    - _image_name_ - Name to give image files
    ...    - _viewport_width_ - Width of the viewport to take screenshot of
    ...    - _num_screenshots_ - Number of Horizontal screenshots to take
    ...    - _cssTransition_ - (Optional) (Boolean) True if CSS transitioning should be used. False if scrolling should be used. Set to True by default
    ...
    ...    *Returns:*
    ...    - _image_list - List of paths for screenshot images
    ...
    ...    *Notes:*
    ...    - Should only be used in "capture full page screenshot"
    # Get starting position
    ${initial_position}    ${initial_position_webkit}=    Execute Javascript    return [document.documentElement.style['transform'],document.documentElement.style['-webkit-transform']]
    ${initial_scroll_x}    ${initial_scroll_y}=    Execute Javascript    return [window.scrollX,window.scrollY]
    # Initialize variables
    ${x_axis}=    Set Variable    ${0}
    ${names} =    create list
    ### CROP MOBILE/TABLET HEADER/FOOTER ###
    ${device}=    get variable value    ${DEVICE.lower()}    ${Empty}
    # iPad
    ${header_height}=    Set Variable If    'ipad' in '${device}'    ${141}    ${0}
    # iPhone
    ${header_height}=    Set Variable If    'iphone' in '${device}'    ${141}    ${header_height}
    ${footer_height}=    Set Variable If    'iphone' in '${device}'    ${89}    ${0}
    # Android - There seem to be 2 android resolution size, need to wait for this to be standardized
    ${header_height}=    Set Variable If    'android' in '${device}'    ${82}    ${header_height}
    #${header_height}=    Set Variable If    'android' in '${device}'    ${108}    ${header_height}
    ### TAKE SCREENSHOT ###
    ${image_list}=    Create List
    : FOR    ${index}    IN RANGE    ${num_screenshots}
    \    #CSS Transition / Scroll
    \    ${javascript}=    Set Variable If    ${cssTransition}    document.documentElement.style['transform'] = '${initial_position} ' + 'translateX(-${x_axis}px)'; document.documentElement.style['-webkit-transform'] = '${initial_position_webkit} ' + 'translateX(-${x_axis}px)';    window.scrollTo(${initial_scroll_x}+${x_axis},${initial_scroll_y})
    \    Execute Javascript    ${javascript}
    \    Run Keyword And Ignore Error    Wait Until Keyword Succeeds    0.5s    0.5s    Fail    Wait for page to transition...
    \    #Screenshot
    \    capture page screenshot    ${image_name}_${index}.png
    \    # Crop any header/footer
    \    ${image_width}    ${image_height}=    Get Image Size    ${OUTPUT_DIR}/${image_name}_${index}.png
    \    ${image_height}=    Evaluate    ${image_height} - ${header_height} - ${footer_height}
    \    Crop Image    ${OUTPUT_DIR}/${image_name}_${index}.png    ${0}    ${header_height}    ${image_width}    ${image_height}
    \    #Increment page position
    \    ${x_axis} =    evaluate    ${x_axis} + ${viewport_width}
    \    #Add screenshot to list
    \    append to list    ${image_list}    ${OUTPUT_DIR}/${image_name}_${index}.png
    # Reset page
    ${javascript}=    Set Variable If    ${cssTransition}    document.documentElement.style['transform'] = '${initial_position}'; document.documentElement.style['-webkit-transform'] = '${initial_position_webkit}';    window.scrollTo(${initial_scroll_x},${initial_scroll_y})    
    Execute Javascript    ${javascript}
    # Return a list of the names
    Return From Keyword    ${image_list}
    
get element position on page and dimensions
    [Arguments]    ${locator}
    [Documentation]    Returns an element's position on the page and dimensions
    ...    
    ...    *Argument:*
    ...    - _locator_ - Locator of element to get position and dimensions
    ...    
    ...    *Returns:*
    ...    - _x_location_ - X coordinate of element
    ...    - _y_location_ - Y coordinate of element
    ...    - _element_width_ - Width of element
    ...    - _element_height_ - Height of element
    # Get existing element ID if possible
    ${id}=    get element attribute    ${locator}    id
    # Assign custom ID to element if it doesn't have one
    ${rand_id} =    generate random string    3    [LOWER]
    run keyword if    '${id}'==''    assign id to element    ${locator}    ${rand_id}
    ${id}=    set variable if    '${id}'==''    ${rand_id}    ${id}
    # Get element position and dimensions
    ${x_location}    ${y_location}    ${element_width}    ${element_height}=    execute javascript    var myElement = document.getElementById("${id}"); var boundingBox = myElement.getBoundingClientRect(); var scrollLeft = window.pageXOffset; var scrollTop = window.pageYOffset; var xCoord = Math.round(boundingBox.left + scrollLeft); var yCoord = Math.round(boundingBox.top + scrollTop); var width = Math.round(boundingBox.width); var height = Math.round(boundingBox.height); return [xCoord, yCoord, width, height];
    Return From Keyword    ${x_location}    ${y_location}    ${element_width}    ${element_height}
    
capture element screenshot
    [Arguments]    ${locator}    ${image_name}    ${set as comment}=True
    [Documentation]    Captures a screenshot for the given element
    ...
    ...    *Arguments:*
    ...    - _locator_ - Locator of element to capture
    ...    - _image_name_ - Name to give image file
    ...    - _set_as_comment_ - (Boolean) True to set the image as a testrail comment.
    ...
    ...    *Returns:*
    ...    - _image_url_ - URL of image screenshot
    # Scroll to the top
    Execute Javascript    window.scrollTo(0,0);
    # Get Element Position/Size
    ${x_coord}    ${y_coord}    ${elem_width}    ${elem_height}=    get element position on page and dimensions    ${locator}
    # Get screenshot
    ${screenshot}=    capture full page screenshot    ${image_name}    ${set_as_comment}
    # Get image name to crop
    ${dir_url} =    create url to log folder
    ${unique_image_name}=    Remove String    ${screenshot}    ${dir_url}/
    ${image_path}=    Set Variable    ${OUTPUT_DIR}/${unique_image_name}
    # Crop image
    Crop Image    ${image_path}    ${x_coord}    ${y_coord}    ${elem_width}    ${elem_height}
    Return From Keyword    ${screenshot}