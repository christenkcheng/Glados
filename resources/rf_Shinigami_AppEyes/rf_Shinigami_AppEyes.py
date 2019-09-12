#!/usr/bin/env python

from future import standard_library
standard_library.install_aliases()
from builtins import object
import os
import http.client
import base64
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidElementStateException
from robot.libraries.BuiltIn import BuiltIn
from applitools import logger
from applitools.logger import StdoutLogger
from applitools.geometry import Region
from applitools.eyes import Eyes, BatchInfo
from applitools.common import StitchMode
from applitools.utils import image_utils
from applitools.selenium.capture import EyesWebDriverScreenshot
from applitools.selenium.target import Target

__version__ = '3.15.0'



class rf_Shinigami_AppEyes(object):
    """
    rf_Shinigami_AppEyes is a visual verfication library for Robot Framework that leverages
    the Eyes-Selenium and Selenium2 libraries.
    *Before running tests*
    Prior to running tests, rf_Shinigami_AppEyes must first be imported into your Robot test suite.
    Example:
        | Library | rf_Shinigami_AppEyes |
    In order to run the rf_Shinigami_AppEyes library and return results, you have to create a free account https://applitools.com/sign-up/ with Applitools.
    You can retreive your API key from the applitools website and that will need to be passed in your Open Eyes Session keyword.
    *Using Selectors*
    Using the keyword Check Eyes Region By Element. The first four strategies are supported: _CSS SELECTOR_, _XPATH_, _ID_ and _CLASS NAME_.
    Using the keyword Check Eyes Region By Selector. *All* the following strategies are supported:
    | *Strategy*        | *Example*                                                                                                     | *Description*                                   |
    | CSS SELECTOR      | Check Eyes Region By Selector `|` CSS SELECTOR      `|` .first.expanded.dropdown `|`  CssElement              | Matches by CSS Selector                         |
    | XPATH             | Check Eyes Region By Selector `|` XPATH             `|` //div[@id='my_element']  `|`  XpathElement            | Matches with arbitrary XPath expression         |
    | ID                | Check Eyes Region By Selector `|` ID                `|` my_element               `|`  IdElement               | Matches by @id attribute                        |
    | CLASS NAME        | Check Eyes Region By Selector `|` CLASS NAME        `|` element-search           `|`  ClassElement            | Matches by @class attribute                     |
    | LINK TEXT         | Check Eyes Region By Selector `|` LINK TEXT         `|` My Link                  `|`  LinkTextElement         | Matches anchor elements by their link text      |
    | PARTIAL LINK TEXT | Check Eyes Region By Selector `|` PARTIAL LINK TEXT `|` My Li                    `|`  PartialLinkTextElement  | Matches anchor elements by partial link text    |
    | NAME              | Check Eyes Region By Selector `|` NAME              `|` my_element               `|`  NameElement             | Matches by @name attribute                      |
    | TAG NAME          | Check Eyes Region By Selector `|` TAG NAME          `|` div                      `|`  TagNameElement          | Matches by HTML tag name                        |
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = __version__
    
    def create_eyes_batch(self, batchName):
        """
        Creates and returns an Applitools Eyes BatchInfo object
        
        Arguments:
        | Batch Name | Name of Batch to be displayed on the Applitools Dashboard |
        """
        if batchName is None:
            raise ValueError('No batchName was given!')
        else:
            return BatchInfo(batchName)
    
    def get_webdriver_instance(self):
        """
            Grab the Library webdriver instance.
            Will try to grab SpartanLibrary, then Spartan, then Selenium2Library.
            Returns error if none of the above webdriver are running.
        """
        try:
            lib = BuiltIn().get_library_instance('SpartanLibrary')
            return lib._current_application()
        except:
            pass    # Fall back to Spartan
        try:
            lib = BuiltIn().get_library_instance('Spartan')
            return lib._current_application()
        except:
            pass    # Fall back to Selenium2Library
        try:
            lib = BuiltIn().get_library_instance('Selenium2Library')
            return lib._current_browser()
        except:
            return error or "Could not determine webdriver instance library type, tried: SpartanLibrary, Spartan, Selenium2Library"
              
    def open_eyes_session(self, appname, testname, apikey, 
                          matchlevel=None, includeEyesLog=False, httpDebugLog=False, 
                          use_css_transition=False, baselineName=None, batch=None):
        """
        Starts a session with the Applitools Eyes Website.
        Arguments:
                |  Application Name (string)            | The name of the application under test.                                                                     |
                |  Test Name (string)                   | The test name.                                                                                              |
                |  API Key (string)                     | User's Applitools Eyes key.                                                                                 |
                |  (Optional) Match Level (string)      | The match level for the comparison - can be STRICT, LAYOUT or CONTENT                                       |
                |  Include Eyes Log (default=False)     | The Eyes logs will not be included by default. To activate, pass 'True' in the variable.                    |
                |  HTTP Debug Log (default=False)       | The HTTP Debug logs will not be included by default. To activate, pass 'True' in the variable.              |
                |  Use CSS Transition (default=False)           | Uses CSS Transition instead of actual scrolling for full page screenshots. To activate, pass 'True' in the variable. |
                |  (Optional) Baseline Name (string)    | The name of the baseline to compare test to. Should be used for cross browser verification                  |
                |  (Optional) Batch (BatchInfo)         | The batch to place the test into. Should be a BatchInfo object                                              |
        Defines a global driver, and eyes.

        Starts a session with the Applitools Eyes Website. See https://eyes.applitools.com/app/sessions/
        Example:
        | *Keywords*         |  *Parameters*                                                                                                                                                                                                                                 |
        | Open Browser       |  http://www.navinet.net/ | gc                         |                     |                 |                      |                       |                     |                           |                           |                  |
        | ${batch}           |  Create Eyes Batch       | Batch Name                 |                     |                 |                      |                       |                     |                           |                           |                  |
        | Open Eyes Session  |  RobotAppEyes_Test       |  NaviNet_RobotAppEyes_Test |  YourApplitoolsKey  |  matchlevel=LAYOUT   |  includeEyesLog=True  |  httpDebugLog=True  |  use_css_transition=True  |  baselineName='Baseline'  |  batch=${batch}  |
        | Check Eyes Window  |  NaviNet Home            |                            |                     |                 |                      |                       |                     |                           |                           |                  |
        | Close Eyes Session |  False                   |                            |                     |                 |                      |                       |                     |                           |                           |                  |
        """
        global driver
        global eyes
        
        eyes = Eyes()
        eyes.api_key = apikey
        
        driver = self.get_webdriver_instance()

        if includeEyesLog is True:
            logger.set_logger(StdoutLogger())
            logger.open_()
        if httpDebugLog is True:
            http.client.HTTPConnection.debuglevel = 1
        if baselineName is not None:
            eyes.baseline_branch_name = baselineName  # (str)
        if batch is not None:
            eyes.batch = batch
        if matchlevel is not None:
            eyes.match_level = matchlevel
        
        stitch_mode = StitchMode.Scroll
        
        if isinstance(use_css_transition, bool):
            if use_css_transition == True:
                stitch_mode = StitchMode.CSS
        elif use_css_transition.lower() == 'true':
            stitch_mode = StitchMode.CSS
                  
        eyes.stitch_mode = stitch_mode
        
        eyes.open(driver, appname, testname)


    def check_eyes_window(self, name, force_full_page_screenshot=False,
                          includeEyesLog=False, httpDebugLog=False,
                          hide_scrollbars=False):
        """
        Takes a snapshot from the browser using the web driver and matches it with
        the expected output.
        Arguments:
                |  Name (string)                                | Name that will be given to region in Eyes.                                                                           |
                |  Force Full Page Screenshot (default=False)   | Will force the browser to take a screenshot of whole page.                                                           |
                |  Include Eyes Log (default=False)             | The Eyes logs will not be included by default. To activate, pass 'True' in the variable.                             |
                |  HTTP Debug Log (default=False)               | The HTTP Debug logs will not be included by default. To activate, pass 'True' in the variable.                       |
                |  Hide scrollbars (default=True)               | Hides scrollbars for screenshots. To activate, pass 'True' in the variable.                                          |
        Example:
        | *Keywords*         |  *Parameters*                                                                                                       |
        | Open Browser       |  http://www.navinet.net/ | gc                |                            |                        |        |       |
        | Open Eyes Session  |  http://www.navinet.net/ | RobotAppEyes_Test |  NaviNet_RobotAppEyes_Test |  YourApplitoolsKey     |  1024  |  768  |
        | Check Eyes Window  |  NaviNet Home            | True              |  hide_scrollbars=True      |                        |        |       |
        | Close Eyes Session |  False                   |                   |                            |                        |        |       |
        
        NOTE: Still has browser header in mobile tests (Android & iOS)
        """
        if includeEyesLog is True:
            logger.set_logger(StdoutLogger())
            logger.open_()
        if httpDebugLog is True:
            http.client.HTTPConnection.debuglevel = 1
        
        eyes.force_full_page_screenshot = force_full_page_screenshot
        eyes.hide_scrollbars = hide_scrollbars
        
        eyes.check_window(name)

    def check_eyes_region(self, element, width, height, name, includeEyesLog=False, httpDebugLog=False, force_full_page_screenshot=True):
        """
        Takes a snapshot of the given region from the browser using the web driver to locate an xpath element
        with a certain width and height and matches it with the expected output.
        The width and the height cannot be greater than the width and the height specified in the open_eyes_session keyword.
        Arguments:
                |  Element (string)                             | This needs to be passed in as an xpath e.g. //*[@id="navbar"]/div/div                                         |
                |  Width (int)                                  | The width of the region that is tested e.g. 500                                                               |
                |  Height (int)                                 | The height of the region that is tested e.g. 120                                                              |
                |  Name (string)                                | Name that will be given to region in Eyes.                                                                    |
                |  Include Eyes Log (default=False)             | The Eyes logs will not be included by default. To activate, pass 'True' in the variable.                      |
                |  HTTP Debug Log (default=False)               | The HTTP Debug logs will not be included by default. To activate, pass 'True' in the variable.                |
                |  Force Full Page Screenshot (default=True)    | Will force the browser to check the whole page for the value, rather than only search the viewable viewport.  |
        Example:
        | *Keywords*         |  *Parameters*                                                                                                        |
        | Open Browser       |  http://www.navinet.net/     | gc                |                             |                    |        |       |
        | Open Eyes Session  |  http://www.navinet.net/     | RobotAppEyes_Test |  NaviNet_RobotAppEyes_Test  |  YourApplitoolsKey |  1024  |  768  |
        | Check Eyes Region  |  //*[@id="navbar"]/div/div   | 500               |  120                        |  NaviNet Navbar    |        |       |
        | Close Eyes Session |  False                       |                   |                             |                    |        |       |
        """
        if includeEyesLog is True:
            logger.set_logger(StdoutLogger())
            logger.open_()
        if httpDebugLog is True:
            http.client.HTTPConnection.debuglevel = 1

        eyes.force_full_page_screenshot = force_full_page_screenshot
        
        intwidth = int(width)
        intheight = int(height)

        searchElement = driver.find_element_by_xpath(element)
        location = searchElement.location
        region = Region(location["x"], location["y"], intwidth, intheight)
        eyes.check_region(region, name)

    def check_eyes_region_by_selector(self, selector, value, name, includeEyesLog=False, httpDebugLog=False, force_full_page_screenshot=True):
        """
        Takes a snapshot of the region of the element found by calling find_element(by, value) from the browser using the web driver
        and matches it with the expected output. With a choice from eight selectors, listed below to check by.
        Arguments:
                |  Selector (string)                            | This will decide what element will be located. Supported selectors: CSS SELECTOR, XPATH, ID, LINK TEXT, PARTIAL LINK TEXT, NAME, TAG NAME, CLASS NAME.    |
                |  Value (string)                               | The specific value of the selector. e.g. a CSS SELECTOR value .first.expanded.dropdown                                                                    |
                |  Name (string)                                | Name that will be given to region in Eyes.                                                                                                                |
                |  Include Eyes Log (default=False)             | The Eyes logs will not be included by default. To activate, pass 'True' in the variable.                                                                  |
                |  Force Full Page Screenshot (default=True)    | Will force the browser to check the whole page for the value, rather than only search the viewable viewport.                                              |
        Example:
        | *Keywords*                    |  *Parameters*                                                                                                            |
        | Open Browser                  |  http://www.navinet.net/  |  gc                       |                            |                    |        |       |
        | Open Eyes Session             |  http://www.navinet.net/  |  RobotAppEyes_Test        |  NaviNet_RobotAppEyes_Test |  YourApplitoolsKey |  1024  |  768  |
        | Check Eyes Region By Selector |  CSS SELECTOR             |  .first.expanded.dropdown |  NaviNetCssElement         |                    |        |       |
        | Close Eyes Session            |  False                    |                           |                            |                    |        |       |
        
        NOTE: Breaks when attempting to find region to screenshot
        """
        if includeEyesLog is True:
            logger.set_logger(StdoutLogger())
            logger.open_()
        if httpDebugLog is True:
            http.client.HTTPConnection.debuglevel = 1
            
        eyes.force_full_page_screenshot = force_full_page_screenshot

        searchElement = None

        searchByDict = {
            'CSS SELECTOR' : By.CSS_SELECTOR,
            'XPATH' : By.XPATH,
            'ID' : By.ID,
            'LINK TEXT' : By.LINK_TEXT,
            'PARTIAL LINK TEXT' : By.PARTIAL_LINK_TEXT,
            'NAME' : By.NAME,
            'TAG NAME' : By.TAG_NAME,
            'CLASS NAME' : By.CLASS_NAME
        }
        
        selector = selector.upper() 
        
        if selector in searchByDict:
            searchElement = searchByDict[selector]
        else:
            raise InvalidElementStateException('Please select a valid selector: CSS SELECTOR, XPATH, ID, LINK TEXT, PARTIAL LINK TEXT, NAME, TAG NAME, CLASS NAME')
            
        eyes.check_region_by_selector(searchElement, value, name)

    def compare_image(self, path, imagename=None, target=None,ignore_mismatch=False, includeEyesLog=False, httpDebugLog=False):
        """
        Select an image and send it to Eyes for comparison. A name can be used in place of the image's file name.
        Arguments:
                |  Path                             | Path of the image to send to eyes for visual comparison.                                                                   |
                |  imagename (default=None)         | Can manually set the name desired for the image passed in. If no name is passed in it will default file name of the image. |
                |  Include Eyes Log (default=False) | The Eyes logs will not be included by default. To activate, pass 'True' in the variable.                                   |
                |  HTTP Debug Log (default=False)   | The HTTP Debug logs will not be included by default. To activate, pass 'True' in the variable.                             |
        Example:
        | *Keywords*         |  *Parameters*                                                                                                         |
        | Open Browser       |  http://www.navinet.net/   |  gc                   |                            |                    |        |       |
        | Open Eyes Session  |  http://www.navinet.net/   |  RobotAppEyes_Test    |  NaviNet_RobotAppEyes_Test |  YourApplitoolsKey |  1024  |  768  |
        | Compare Image      |  selenium-screenshot-1.png |  Image Name Example   |                            |                    |        |       |
        | Close Eyes Session |                            |                       |                            |                    |        |       |
        """
        if imagename is None:
            tag = os.path.basename(path)
        else:
            tag = imagename
        
        eyes._ensure_running_session()
            
        if includeEyesLog is True:
            logger.set_logger(StdoutLogger())
            logger.open_()
        if httpDebugLog is True:
            http.client.HTTPConnection.debuglevel = 1

        with open(path, 'rb') as image_file:
            screenshot64 = image_file.read().encode('base64')
            screenshot = image_utils.image_from_bytes(base64.b64decode(screenshot64))
            screenshotBytes = EyesWebDriverScreenshot.create_from_image(screenshot, eyes._driver)
        title = eyes._title
        app_output = {'title': title, 'screenshot64': None}
        user_inputs = []
        
        #TODO: Research this aspect
        if target is None:
            target = Target()
                                           
        prepare_match_data = eyes._match_window_task._create_match_data_bytes(
            app_output, user_inputs, tag, ignore_mismatch, screenshotBytes, eyes.default_match_settings, target)
        eyes._match_window_task._agent_connector.match_window(
            eyes._match_window_task._running_session, prepare_match_data)

    def close_eyes_session(self, includeEyesLog=False, httpDebugLog=False):
        """
        Closes a session and returns the results of the session.
        If a test is running, aborts it. Otherwise, does nothing.
        The RobotAppEyesTest.txt test will fail after the first run, this is because a baseline is being created and will be accepted automatically by Applitools Eyes.
        A second test run will show a successful comparison between screens and the test will pass.
        Arguments:
                |  Include Eyes Log (default=False) | The Eyes logs will not be included by default. To activate, pass 'True' in the variable.        |
                |  HTTP Debug Log (default=False)   | The HTTP Debug logs will not be included by default. To activate, pass 'True' in the variable.  |
        Example:
        | *Keywords*                    |  *Parameters*                                                                                                         |
        | Open Browser                  |  http://www.navinet.net/  |  gc                    |                            |                    |        |       |
        | Open Eyes Session             |  http://www.navinet.net/  |  RobotAppEyes_Test     |  NaviNet_RobotAppEyes_Test |  YourApplitoolsKey |  1024  |  768  |
        | Check Eyes Region By Selector |  LINK TEXT                |  RESOURCES             |  NaviNetLinkTextElement    |                    |        |       |
        | Close Eyes Session            |                           |                        |                            |                    |        |       |
        """
        if includeEyesLog is True:
            logger.set_logger(StdoutLogger())
            logger.open_()
        if httpDebugLog is True:
            http.client.HTTPConnection.debuglevel = 1

        eyes.close()
        eyes.abort_if_not_closed()


    def eyes_session_is_open(self):
        """
        Returns True if an Applitools Eyes session is currently running, otherwise it will return False.
        | *Keywords*        |  *Parameters*                                                                                                       |
        | Open Browser      |  http://www.navinet.net/  |  gc                  |                            |                    |        |       |
        | Open Eyes Session |  http://www.navinet.net/  |  RobotAppEyes_Test   |  NaviNet_RobotAppEyes_Test |  YourApplitoolsKey |  1024  |  768  |
        | ${isOpen}=        |  Eyes Session Is Open     |                      |                            |                    |        |       |
        | Run Keyword If    |  ${isOpen}==True          | Close Eyes Session   |                            |                    |        |       |
        """
        return eyes.is_open()