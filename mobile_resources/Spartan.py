from __future__ import print_function
from builtins import str
from builtins import range
import os
import sys
import robot
import time
from AppiumLibrary import AppiumLibrary
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
from appium.webdriver.connectiontype import ConnectionType
from AppiumLibrary.utils import ApplicationCache
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from robot.libraries.BuiltIn import BuiltIn
from robot.api import logger
from selenium.common.exceptions import NoSuchWindowException

class Spartan(AppiumLibrary):
    def get_driver_instance(self):
        return self._current_application()

    def __init__(self):
        super(Spartan, self).__init__()
        # ElementFinder init
        self._strategies = {
            'ios': self._find_by_ios_uiautomator,
            'android': self._find_by_android_uiautomator
        }
        self._strat = {
            'title': self._select_by_title,
            'name': self._select_by_name,
            'url': self._select_by_url,
            None: self._select_by_default
        }

#---------------------------------------- ElementFinder ----------------------------------------

    # private

    def _find_by_ios_uiautomator(self, browser, criteria, tag, constraints):
        """Finds elements by uiautomation in iOS.

        :Args:
        - uia_string - The element name in the iOS UIAutomation library

        :Usage:
            driver.find_elements_by_ios_uiautomation('.elements()[1].cells()[2]')
        """
        return self._filter_elements(
            browser.find_elements_by_ios_uiautomator(criteria),
            tag, constraints)

    def _find_by_android_uiautomator(self, browser, criteria, tag, constraints):
        """Finds elements by uiautomator in Android.

        :Args:
         - uia_string - The element name in the Android UIAutomator library

        :Usage:
            driver.find_elements_by_android_uiautomator('.elements()[1].cells()[2]')
        """
        return self._filter_elements(
            browser.find_elements_by_android_uiautomator(criteria),
            tag, constraints)

#---------------------------------------- ApplicationManagement ----------------------------------------

    # public

    def close_application(self):
        """Closes the current application."""
        if self._cache.current:
            self._debug('Closing application with session id %s' % self._current_application().session_id)
            self._cache.close()

    def reset_application(self):
        """ Reset application """
        driver = self._current_application()
        driver.reset()

    def execute_script(self, script):
        """Executes javascript"""
        if os.path.exists(script) and os.path.isfile(script):
            script = open(script).read().replace('\n', '; ').replace('\r', ' ')
        self._info("executing script: " + script)
        return self._current_application().execute_script(script)

    def get_screen_width(self):
        """Returns the width of the screen in pixels as an int"""
        driver = self._current_application()
        window_size = driver.get_window_size()
        self._info("Screen width is: %d" % (window_size['width']))
        return int(window_size['width'])

    def get_screen_height(self):
        """Returns the height of the screen in pixels as an int"""
        driver = self._current_application()
        window_size = driver.get_window_size()
        self._info("Screen height is: %d" % (window_size['height']))
        return int(window_size['height'])

    def _current_application(self):
        if not self._cache.current:
            raise RuntimeError('No application is open')
        return self._cache.current

    def close_all_tabs(self):
        """Close all open tabs created by the current web driver session"""
        driver = self._current_application()
        context_list = driver.contexts
        try:
            for context in context_list:
                if "WEBVIEW" in context:
                    driver.switch_to.context(context)
                    driver.close()
        except:
            pass

    def accept_alert(self, option="Cancel"):
        """
        Clicks the option in alert according to option text
        Ex.

        | Accept Alert | Continue |
        """
        driver = self._current_application()
        try:
            driver.execute_script('mobile: alert', {'action': 'accept', 'buttonLabel': '%s' %option});
        except:
            pass

    def get_orientation(self):
        driver = self._current_application()
        orientation = driver.orientation
        return orientation

#---------------------------------------- Element ----------------------------------------

    # public

    def set_value(self, locator, value):
        """iOS only. Sets the value of the field directly (does not use keyboard)."""
        el = self._element_find(locator, True, True)
        self._current_application().set_value(el, value)

    def get_value(self,locator, attr="value"):
        """Returns the value attribute of element identified by `locator`.
        """
        element = self._element_find(locator)
        return (element.get_attribute(attr)).strip()

    def get_text(self, locator):
        element = self._element_find(locator)
        text = element.text
        return text

    def select_dropdown(self, locator, value, by="text"):
        """
        Browser only
        Select option from dropdown list. Valid options for "by" include
        text, value, and index. Text is the default
        Ex:

        | Select Dropdown | xpath=//*[@id="makeCode"] | Honda | |
        | Select Dropdown | xpath=//*[@id="makeCode"] | MN | value |
        """
        element = Select(self._element_find(locator))
        if (by.lower() == "text"):
            element.select_by_visible_text(value)
        elif (by.lower() == "value"):
            element.select_by_value(value)
        elif (by.lower() == "index"):
            element.select_by_index(value)
        else:
            raise AssertionError("Valid argument for by is index, value, and text. Got '%s'" % (by))

    def hide_keyboard(self, key_name=None, key=None, strategy=None):
        """
        Hides the software keyboard on the device, using the specified key to
        press. If no key name is given, the keyboard is closed by moving focus
        from the text field.
        """
        driver = self._current_application()
        driver.hide_keyboard(key_name, key, strategy)

    def OLD_page_should_contain_text(self, text, loglevel='INFO'):
        """Verifies that current page contains `text`.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        """
        if not text in self.log_source(loglevel):
            self.log_source(loglevel)
            raise AssertionError("Page should have contained text '%s' "
                                 "but did not" % text)
        self._info("Current page contains text '%s'." % text)

    def page_should_not_contain_text(self, text, loglevel='INFO'):
        """Verifies that current page does not contain `text`.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Giving `NONE` as level disables logging.
        """
        if text in self.log_source(loglevel):
            self.log_source(loglevel)
            raise AssertionError("Page should not have contained text '%s' "
                                 "but did" % text)
        self._info("Current page does not contain text '%s'." % text)

    def page_should_not_contain_element(self, locator, loglevel='INFO'):
        """Verifies that current page not contains `locator` element.

        If this keyword fails, it automatically logs the page source
        using the log level specified with the optional `loglevel` argument.
        Givin
        """
        if self._is_element_present(locator):
            self.log_source(loglevel)
            raise AssertionError("Page should not have contained element '%s' "
                                 "but did" % locator)
        self._info("Current page does not contain element '%s'." % locator)

    def element_should_be_disabled(self, locator):
        """Verifies that element identified with locator is disabled.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        """
        if self._element_find(locator, True, True).is_enabled():
            self.log_source(loglevel)
            raise AssertionError("Element '%s' should be disabled "
                                 "but was not" % locator)
        self._info("Element '%s' is disabled ." % locator)

    def element_should_be_enabled(self, locator):
        """Verifies that element identified with locator is enabled.

        Key attributes for arbitrary elements are `id` and `name`. See
        `introduction` for details about locating elements.
        """
        if not self._element_find(locator, True, True).is_enabled():
            self.log_source(loglevel)
            raise AssertionError("Element '%s' should be enabled "
                                 "but was not" % locator)
        self._info("Element '%s' is enabled ." % locator)

    def send_keys(self, element, value):
        el = self._element_find(element)
        #values array starts at 0
        el.send_keys(str(value))

    # private

    def _find_element_by_class_name(self, class_name, index_or_name):
        elements = self._find_elements_by_class_name(class_name)

        if self._is_index(index_or_name):
            try:
                index = int(index_or_name.split('=')[-1])
                element = elements[index]
            except IndexError as TypeError:
                raise Exception('Cannot find the element with index "%s"' % index_or_name)
        else:
            found = False
            for element in elements:
                self._info("'%s'." % element.text)
                if element.text == index_or_name:
                    found = True
                    break
            if not found:
                raise Exception('Cannot find the element with name "%s"' % index_or_name)

        return element

    def _element_find(self, locator, first_only=True, required=True, tag=None):
        application = self._current_application()
        elements = self._element_finder.find(application, locator, tag)
        if required and len(elements) == 0:
            raise ValueError("Element locator '" + locator + "' did not match any elements.")
        if first_only:
            if len(elements) == 0: return None
            return elements[0]
        return elements

#---------------------------------------- KeyEvent ----------------------------------------

    # public

    def key_event(self, keycode, metastate=None):
        """Sends a keycode to the device. Android only. Possible keycodes can be
        found in http://developer.android.com/reference/android/view/KeyEvent.html.

        :Args:
         - keycode - the keycode to be sent to the device
         - metastate - meta information about the keycode being sent
        """
        self._current_application().keyevent(keycode, metastate)

#---------------------------------------- KeyEvent ----------------------------------------

    # public

    def tap_element(self, locator):
        """ Tap on element """
        driver = self._current_application()
        el = self._element_find(locator, True, True)
        action = TouchAction(driver)
        action.tap(el).perform()

    def tap(self, x, y, duration=500):
        """
        Taps the location of the given coordinates. If the coordinates
        entered are decimal values, they are interpreted as percentages of
        the screen width and height."""
        driver = self._current_application()
        window_size = driver.get_window_size()
        x = float(x)
        y = float(y)
        if (x < 1):
            x = round(x*float(window_size['width']))
        if (y < 1):
            y = round(y*float(window_size['height']))
        self._info("Tapping coordinates: %d, %d." % (x, y))
        driver.tap([(x,y)], duration)

    #add for testing
    def single_tap(self, locator):
        script = """
            var element = arguments[0];
            if ('ontouchend' in document) {
            if (document.createEventObject) { // IE
            element.fireEvent('ontouchstart', document.createEventObject());
            element.fireEvent('ontouchend', document.createEventObject());
            } else {
            var start = document.createEvent('Event');
            start.initEvent("touchstart", true, true);
            var end = document.createEvent('Event');
            end.initEvent("touchend", true, true);
            element.dispatchEvent(start);
            element.dispatchEvent(end);
            }
            return true;
            }
            return false;
            """
        driver = self._current_application()
        element = self._element_find(locator, True, True)
        touched = driver.execute_script(script, element)
        if touched:
            print("touched")
        else:
            print("touched fallback")
#---------------------------------------- KeyEvent ----------------------------------------

    # private

    def _get_log_dir(self):
        logfile = 'NONE'
        BuiltIn().set_global_variable('$logfile', '${LOG FILE}')
        if logfile != 'NONE':
            return os.path.dirname(logfile)
        return BuiltIn().get_variable_value('${OUTPUTDIR}')

#---------------------------------------- KeyEvent ----------------------------------------

    # public

    def set_network_connection_status(self, connectionStatus):
        """Sets the network connection Status.
        Android only.
        Possible values:
            Value |(Alias)          | Data | Wifi | Airplane Mode
            -------------------------------------------------
            0     |(None)           | 0    | 0    | 0
            1     |(Airplane Mode)  | 0    | 0    | 1
            2     |(Wifi only)      | 0    | 1    | 0
            4     |(Data only)      | 1    | 0    | 0
            6     |(All network on) | 1    | 1    | 0
        """
        driver = self._current_application()
        connType = ConnectionType(int(connectionStatus))
        return driver.set_network_connection(connType)

#---------------------------------------- iOS Keywords ----------------------------------------

    def select_checkbox(self, locator):
        """Selects checkbox identified by `locator`.
        Does nothing if checkbox is already selected.
        """
        self._info("Selecting checkbox '%s'." % locator)
        driver = self._current_application()
        el = self._element_find(locator, True, True)
        action = TouchAction(driver)
        if el.is_selected() == False:
            #action.tap(el).perform()
            el.click()

    def unselect_checkbox(self, locator):
        """Removes selection of checkbox identified by `locator`.
        Does nothing if the checkbox is not checked.
        """
        self._info("Unselecting checkbox '%s'." % locator)
        driver = self._current_application()
        el = self._element_find(locator, True, True)
        action = TouchAction(driver)
        if el.is_selected() == True:
            #action.tap(el).perform()
            el.click()

    def checkbox_should_be_selected(self, locator):
        """Verifies checkbox identified by `locator` is selected/checked.
        """
        self._info("Verifying checkbox '%s' is selected." % locator)
        el = self._element_find(locator, True, True)
        if el.is_selected() == False:
            raise AssertionError("Checkbox '%s' should have been selected "
                                    "but was not" % locator)

    def checkbox_should_not_be_selected(self, locator):
        """Verifies checkbox identified by `locator` is not selected/checked.
        """
        self._info("Verifying checkbox '%s' is not selected." % locator)
        el = self._element_find(locator, True, True)
        if el.is_selected() == True:
            raise AssertionError("Checkbox '%s' should not have been selected"
                                    % locator)

    def get_location(self):
        """Returns the url of the current page.
        """
        url = self._current_application().current_url
        return url

    def location_should_be(self, expected_url):
        """Verifies that the current url matches 'expected_url'.
        """
        driver = self._current_application()
        actual_url = driver.current_url
        if actual_url != expected_url:
            raise AssertionError("Location should have been %s but was %s"
                                    % (expected_url, actual_url))

    def log_location(self):
        """Logs and returns the current location.
        """
        url = self._current_application().current_url
        self._info(url)
        return url

    def get_title(self):
        """Returns the title of the current page.
        """
        return self._current_application().title

    def get_element_attribute(self, attribute_locator, attribute=""):
        """Return value of element attribute. Now friendly with SeleniumLibrary 3.0

        `attribute_locator` can be one of two things:
            - an element locator followed by an @ sign and attribute name, for example "element_id@class"
            - a normal element locator
        If `attribute_locator` is in the second format, then `attribute` must be set to an attribute name.
        """
        if "@" in attribute_locator and attribute=="":
            locator = attribute_locator.rpartition('@')[0]
            attribute_name = attribute_locator.rpartition('@')[-1]
        else:
            locator = attribute_locator
            attribute_name = attribute
        element = self._element_find(locator, True, False)
        if element is None:
            raise ValueError("Element '%s' not found." % (locator))
        return element.get_attribute(attribute_name)

    def element_text_should_be(self, locator, expected_text, message=""):
        """Verifies that the element's text matches 'expected_text'.
        """
        el = self._element_find(locator, True, True)
        if el.text != expected_text:
            errmsg = "Element text should have been %s but was %s" % (expected_text, el.text)
            if message != "":
                errmsg = message
            raise AssertionError(errmsg)

    def element_should_contain(self, locator, expected_text, message=""):
        """Verifies that the element's text contains 'expected_text'.
        """
        el = self._element_find(locator, True, True)
        if expected_text not in el.text:
            errmsg = "Element %s should have contained %s but did not. Element's text was %s" % (locator, expected_text, el.text)
            if message != "":
                errmsg = message
            raise AssertionError(errmsg)

    def element_should_not_contain(self, locator, expected_text, message=""):
        """Verifies that the element's text contains 'expected_text'.
        """
        el = self._element_find(locator, True, True)
        if expected_text in el.text:
            errmsg = "Element %s should not have contained %s but did. Element's text was %s" % (locator, expected_text, el.text)
            if message != "":
                errmsg = message
            raise AssertionError(errmsg)

    def delete_all_cookies(self):
        """Deletes all browser cookies
        """
        driver = self._current_application()
        driver.delete_all_cookies()

    def get_cookie_value(self, name):
        """Returns value of cookie found at 'name'
        """
        cookie = self._current_application().get_cookie(name)
        if cookie is not None:
            return cookie
        raise ValueError("Cookie with name %s not found." % name)

    def location_should_contain(self, expected):
        """Verifies that current URL contains 'expected'
        """
        driver = self._current_application()
        actual = driver.current_url
        if expected not in actual:
            raise AssertionError("Location should have contained %s but did not" % (expected))

    def select_frame(self, locator):
        """Sets frame identified by 'locator' as current frame
        """
        self._info("Selecting frame '%s'." % locator)
        element = self._element_find(locator)
        driver = self._current_application()
        driver.switch_to_frame(element)

    def unselect_frame(self):
        """Sets the top frame as the current frame
        """
        self._info("Unselecting frame.")
        self._current_application().switch_to_default_content()

    def reload_page(self):
        """Simulates user reloading page.
        """
        self._current_application().refresh()

    def element_should_be_visible(self, locator, message=''):
        """Verifies that the element identified by 'locator' is visible.

        Herein, visible means that the element is logically visible, not optically
        visible in the current brower viewport.

        'message' can be used to override the default error message
        """
        self._info("Verifiying element '%s' is visible." % locator)
        try:
            el = self._element_find(locator)
        except:
            if not message:
                message = "Element locator '%s' did not match any elements." % locator
            raise AssertionError(message)
        if not el.is_displayed():
            if not message:
                message = "The element '%s' should be visible, but it is not." % locator
            raise AssertionError(message)

    def element_should_not_be_visible(self, locator, message=''):
        """Verifies that the element identified by 'locator' is NOT visible.

        This is opposite of 'Element Should Be Visible'.

        'message' can be used to override the default error message
        """
        self._info("Verifiying element '%s' is NOT visible." % locator)
        try:
            el = self._element_find(locator)
        except:
            return
        if el.is_displayed():
            if not message:
                message = "The element '%s' should NOT be visible, but it is." % locator
            raise AssertionError(message)

    def wait_until_element_is_visible(self, locator, timeout=None, error=None):
        """Waits until element specified with `locator` is visible.

        Fails if `timeout` expires before the element is visible. See
        `introduction` for more information about `timeout` and its
        default value.

        `error` can be used to override the default error message.

        """
        def check_visibility():
            el = self._element_find(locator, required=False)
            if el is None:
                return error or "Element locator '%s' did not match any elements after %s" % (locator, self._format_timeout(timeout))
            elif el.is_displayed():
                return
            else:
                return error or "Element '%s' was not visible in %s" % (locator, self._format_timeout(timeout))
        self._info("locator " + locator + " is visible")
        self._wait_until_no_error(timeout, check_visibility)

    def wait_until_element_is_not_visible(self, locator, timeout=None, error=None):
        """Waits until element specified with `locator` is not visible.

        Fails if `timeout` expires before the element is not visible. See
        `introduction` for more information about `timeout` and its
        default value.

        `error` can be used to override the default error message.

        """
        def check_visibility():
            try:
                el=self._element_find(locator)
            except Exception:
                return
            if not el.is_displayed():
                return
            else:
                return error or "Element '%s' was visible in %s" % (locator, self._format_timeout(timeout))
        self._info("locator " + locator + " is not visible")
        self._wait_until_no_error(timeout, check_visibility)

    def _wait_until_no_error(self, timeout, wait_func, *args):
        timeout = robot.utils.timestr_to_secs(timeout) if timeout is not None else self._timeout_in_secs
        maxtime = time.time() + timeout
        while True:
            timeout_error = wait_func(*args)
            if not timeout_error: return
            if time.time() > maxtime:
                raise AssertionError(timeout_error)
            time.sleep(0.2)

    def select_from_list(self, locator, *items):
        """Selects `*items` from list identified by `locator`

        If more than one value is given for a single-selection list, the last
        value will be selected. If the target list is a multi-selection list,
        and `*items` is an empty list, all values of the list will be selected.

        *items try to select by value then by label.

        It's faster to use 'by index/value/label' functions.

        An exception is raised for a single-selection list if the last
        value does not exist in the list and a warning for all other non-
        existing items. For a multi-selection list, an exception is raised
        for any and all non-existing values.

        Select list keywords work on both lists and combo boxes. Key attributes for
        select lists are `id` and `name`. See `introduction` for details about
        locating elements.
        """
        non_existing_items = []

        items_str = items and "option(s) '%s'" % ", ".join(items) or "all options"
        self._info("Selecting %s from list '%s'." % (items_str, locator))

        driver = self._current_application()
        el_list = locator.split('=', 1)[1]
        locator_type = locator.split('=', 1)[0]
        if locator_type == "css":
            select = Select(driver.find_element_by_css_selector(el_list))
        elif locator_type == "xpath":
            select = Select(driver.find_element_by_xpath(el_list))
        else:
            raise ValueError('Locator type was not defined as "css" or "xpath": ' + locator)

        if not items:
            for i in range(len(select.options)):
                select.select_by_index(i)
            return

        for item in items:
            try:
                select.select_by_value(item)
            except:
                try:
                    select.select_by_visible_text(item)
                except:
                    non_existing_items = non_existing_items + [item]
                    continue

        if any(non_existing_items):
            if select.is_multiple:
                raise ValueError("Options '%s' not in list '%s'." % (", ".join(non_existing_items), locator))
            else:
                if any (non_existing_items[:-1]):
                    items_str = non_existing_items[:-1] and "Option(s) '%s'" % ", ".join(non_existing_items[:-1])
                    self._warn("%s not found within list '%s'." % (items_str, locator))
                if items and items[-1] in non_existing_items:
                    raise ValueError("Option '%s' not in list '%s'." % (items[-1], locator))

    def select_from_list_by_value(self, locator, *items):
        """
        """

        items_str = items and "option(s) '%s'" % ", ".join(items) or "all options"
        self._info("Selecting %s from list '%s'." % (items_str, locator))

        driver = self._current_application()
        el_list = locator.split('=', 1)[1]
        locator_type = locator.split('=', 1)[0]
        self._info(locator_type)
        if locator_type == "css":
            select = Select(driver.find_element_by_css_selector(el_list))
        elif locator_type == "xpath":
            select = Select(driver.find_element_by_xpath(el_list))
        for item in items:
            select.select_by_value(item)

    def select_from_list_by_label(self, locator, *items):
        """
        """

        items_str = items and "option(s) '%s'" % ", ".join(items) or "all options"
        self._info("Selecting %s from list '%s'." % (items_str, locator))

        driver = self._current_application()
        el_list = locator.split('=', 1)[1]
        locator_type = locator.split('=', 1)[0]
        self._info(locator_type)
        if locator_type == "css":
            select = Select(driver.find_element_by_css_selector(el_list))
        elif locator_type == "xpath":
            select = Select(driver.find_element_by_xpath(el_list))
        for item in items:
            select.select_by_visible_text(item)

    def submit_form(self, locator=None):
        """Submits a form identified by 'locator'.
        if 'locator' is empty, first form on the page will be submitted.
        Key attributes for forms are 'id' and 'name'.
        """

        self._info("Submitting form '%s'." % locator)
        if not locator:
            locator = 'xpath=//form'
        element = self._element_find(locator, True, True, 'form')
        element.submit()

    def double_click_element(self, locator):
        """Double click element identified by 'locator'.
        """

        self._info("Double clicking element '%s'." % locator)
        element = self._element_find(locator, True, True)
        element.click()
        element.click()

    def select_radio_button(self, group_name, value):
        """Sets selection of radio buton group identified by 'group_name' to 'value'.

        The radio button to be selected is located by two arguments:
        -'group_name' is used as the name of the radio input
        -'value' is used for the value attribute or for the id attribute
        """

        self._info("Selecting '%s' from radio button '%s'." % (value, group_name))
        driver = self._current_application()
        element = driver.find_elements_by_name(group_name)
        length = len(element)
        self._info(length)
        for x in range(0, length):
            el_id = element[x].get_attribute("id")
            if el_id == value:
                element[x].click()

    def current_frame_contains(self, text, loglevel='INFO'):
        """Verifies that current frame contains 'text'.
        """
        driver = self._current_application()
        bodyText = driver.find_element_by_tag_name('body').text
        if text in bodyText:
            self._info("Current page contains text '%s'." % text)
        else:
            raise AssertionError("Page should have contained text '%s' but did not." % text)

    def current_frame_should_not_contain(self, text, loglevel='INFO'):
        """Verifies that current frame contains 'text'.
        """
        driver = self._current_application()
        bodyText = driver.find_element_by_tag_name('body').text
        if text in bodyText:
            raise AssertionError("Page should not have contained text '%s' but did." % text)
        else:
            self._info("Current page does not contain text '%s'." % text)

    def select_window(self, locator="MAIN"):
        """Selects the window matching locator and return previous window handle

        locator: NEW, MAIN (default), CURRENT (case-insensitive)
        DOES NOT SUPPORT: Locator, Name, Text, etc

        return: current window handle before selecting.
        """
        driver = self._current_application()
        current = driver.current_context
        if locator.lower() == "new":
            context = driver.contexts[-1]
            driver.switch_to.context(context)
            return current
        elif locator.lower() == "main":
            context = driver.contexts[1]
            driver.switch_to.context(context)
            return current
        elif locator.lower() == "current":
            return current
        else:
            raise ValueError("Currently the locator '%s' is not supported, please use 'NEW', 'MAIN', or 'CURRENT' only for now." % locator)

    def get_current_window_info(self):
        """Returns a list of the current window: id, name, title, url"""
        return self.execute_script("return [ window.id, window.name, document.title, document.URL ];")

    def get_window_titles(self):
        """Returns titles of all windows
        """
        return [ window_info[2] for window_info in self._get_window_infos(self._current_application()) ]

    def _get_window_infos(self, browser):
        window_infos = []
        try:
            starting_handle = browser.current_window_handle
        except NoSuchWindowException:
            starting_handle = None
        try:
            for handle in browser.window_handles:
                time.sleep(3) # Needs a bit of sleep to allow handle to load and switch
                browser.switch_to.window(handle)
                window_infos.append(self.get_current_window_info())
        finally:
            if starting_handle:
                browser.switch_to_window(starting_handle)
        return window_infos

    def alert_should_be_present(self, text=''):
        """Verifies an alert is present and dismisses it.
        If `text` is a non-empty string, then it is also verified that the
        message of the alert equals to `text`.
        Will fail if no alert is present. Note that following keywords
        will fail unless the alert is dismissed by this
        keyword or another like `Get Alert Message`.
        """
        self._current_application().switch_to_alert()
        alert_text = self.get_alert_message()
        if text and alert_text != text:
            raise AssertionError("Alert text should have been "
                                 "'%s' but was '%s'"
                                 % (text, alert_text))

    def get_alert_message(self, dismiss=True):
        """Returns the text of current JavaScript alert.
        By default the current JavaScript alert will be dismissed.
        This keyword will fail if no alert is present. Note that
        following keywords will fail unless the alert is
        dismissed by this keyword or another like `Get Alert Message`.
        """
        if dismiss:
            return self._close_alert()
        else:
            return self._read_alert()

    def _close_alert(self, confirm=True):
        text = self._read_alert()
        self._handle_alert(confirm)
        return text

    def _read_alert(self):
        alert = self._wait_alert()
        # collapse new lines chars
        return ' '.join(alert.text.splitlines())

    def _handle_alert(self, confirm=True):
        alert = self._wait_alert()
        if not confirm:
            alert.dismiss()
            return False
        else:
            alert.accept()
            return True

    def _wait_alert(self):
        return WebDriverWait(self._current_application(), 1).until(
            EC.alert_is_present())

    def select(self, browser, locator):
        """Selects a window given the locator. Take a look at 'select_window'"""
        assert browser is not None
        if locator is not None:
            if isinstance(locator, list):
                self._select_by_excludes(browser, locator)
                return
            if locator.lower() == "self" or locator.lower() == "current":
                return
            if locator.lower() == "new" or locator.lower() == "popup":
                self._select_by_last_index(browser)
                return
        (prefix, criteria) = self._parse_locator(locator)
        strategy = self._strat.get(prefix)
        if strategy is None:
            raise ValueError("Window locator with prefix '" + prefix + "' is not supported")
        return strategy(browser, criteria)

    # Strategy routines, private

    def _select_by_title(self, browser, criteria):
        self._select_matching(
            browser,
            lambda window_info: window_info[2].strip().lower() == criteria.lower(),
            "Unable to locate window with title '" + criteria + "'")

    def _select_by_name(self, browser, criteria):
        self._select_matching(
            browser,
            lambda window_info: window_info[1].strip().lower() == criteria.lower(),
            "Unable to locate window with name '" + criteria + "'")

    def _select_by_url(self, browser, criteria):
        self._select_matching(
            browser,
            lambda window_info: window_info[3].strip().lower() == criteria.lower(),
            "Unable to locate window with URL '" + criteria + "'")

    def _select_by_default(self, browser, criteria):
        if criteria is None or len(criteria) == 0 or criteria.lower() == "null":
            handles = browser.window_handles
            browser.switch_to.window(handles[0])
            return
        try:
            starting_handle = browser.current_window_handle
        except NoSuchWindowException:
            starting_handle = None
        for handle in browser.window_handles:
            browser.switch_to.window(handle)
            if criteria == handle:
                return
            for item in self.get_current_window_info()[1:3]:
                if item.strip().lower() == criteria.lower():
                    return
        if starting_handle:
            browser.switch_to.window(starting_handle)
        raise ValueError("Unable to locate window with handle or name or title or URL '" + criteria + "'")

    def _select_by_last_index(self, browser):
        handles = browser.get_window_handles()
        try:
            if handles[-1] == browser.current_window_handle:
                raise AssertionError("No new window at last index. Please use '@{ex}= | List Windows' + new window trigger + 'Select Window | ${ex}' to find it.")
        except IndexError:
            raise AssertionError("No window found")
        except NoSuchWindowException:
            raise AssertionError("Currently no focus window. where are you making a popup window?")
        browser.switch_to.window(handles[-1])

    def _select_by_excludes(self, browser, excludes):
        for handle in browser.window_handles:
            if handle not in excludes:
                browser.switch_to.window(handle)
                return
        raise ValueError("Unable to locate new window")

    # Private

    def _parse_locator(self, locator):
        prefix = None
        criteria = locator
        if locator is not None and len(locator) > 0:
            locator_parts = locator.partition('=')
            if len(locator_parts[1]) > 0:
                prefix = locator_parts[0].strip().lower()
                criteria = locator_parts[2].strip()
        if prefix is None or prefix == 'name':
            if criteria is None or criteria.lower() == 'main':
                criteria = ''
        return (prefix, criteria)

    def _select_matching(self, browser, matcher, error):
        try:
            starting_handle = browser.current_window_handle
        except NoSuchWindowException:
            starting_handle = None
        for handle in browser.window_handles:
            browser.switch_to.window(handle)
            if matcher(self.get_current_window_info()):
                return
        if starting_handle:
            browser.switch_to.window(starting_handle)
        raise ValueError(error)

    def scroll_to_element(self,locator):
        """
        Scrolls to and centers the targeted element in the browser window.
        :param robot_locator:
        """
        driver = self._current_application()
        element = self._element_find(locator)
        script = """var box = arguments[0].getBoundingClientRect();
                var y = ((box.top + box.bottom) / 2) - (window.innerHeight / 2);
                var x= ((box.left + box.right) / 2) - (window.innerWidth / 2);
                window.scrollBy(x, y);"""
        driver.execute_script(script, element)


    
    def get_list_items(self,locator,values=False):
        options = self._get_options(locator)
        if bool(values):
            return self._get_values(options)
        else:
            return self._get_labels(options)

    def _get_select_list(self, locator):
        el = self._element_find(locator)
        return Select(el)

    def _get_options(self, locator):
        return self._get_select_list(locator).options

    def _get_labels(self, options):
        return [opt.text for opt in options]

    def _get_values(self, options):
        return [opt.get_attribute('value') for opt in options]


