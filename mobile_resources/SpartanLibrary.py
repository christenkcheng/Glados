from builtins import str
from builtins import object
from Spartan import Spartan
from robot.libraries.BuiltIn import BuiltIn
import yaml
import os
from device_name_parser import device_name_parser
from port_selector import port_selector

class SpartanLibrary(Spartan):
    
    def __init__(self):
        super(SpartanLibrary, self).__init__()
        self._hardcodedDevices = ('iPhone 6', 'iPhone 6s', 'iPhone 7', 'iPhone 8', 'iPad Air 2', 'AndroidEmulator6', 'AndroidEmulator7','AndroidEmulator8')
        self._ports_list = []
        self.browser = ''
        
    def open_browser(self, url, browser, alias=None, remote_url=False, desired_capabilities=None, ff_profile_dir=None):
        deviceType = BuiltIn().get_variable_value("${DEVICE}")
        device = self._get_device_capabilities(deviceType)
        
        if browser is not None:
            self.browser = browser.lower()
        
        self.open_application(remote_url, **device)
        
        self.go_to(url)
        
        # Switch orientation to landscape when decleared otherwise portrait
        landscape = BuiltIn().get_variable_value("${LANDSCAPE_MODE}")
        
        if str(landscape).lower() == 'true':
            self.landscape()
        else:
            self.portrait()
        
    def maximize_browser_window(self):
        # Mobile has no maximize window
        pass
        
    def go_to(self, url):
        disable_ab_tests = BuiltIn().get_variable_value("${DISABLE_AB_TESTS}")
        if disable_ab_tests:
            script = "window.location.href = '" + url + "';"
            self.execute_script(script);
        else:      
            self.go_to_url(url)
        
    def close_all_browsers(self):
        self.close_all_applications()
        
        # DEBUGGING
        BuiltIn().set_suite_variable('$test_port',self._ports_list)
        
        # Release all ports
        while self._ports_list:
            port = self._ports_list.pop()
            port_selector().release_port(port)
        
        # DEBUGGING
        BuiltIn().set_suite_variable('$end_port',self._ports_list)
        
    def close_browser(self):
        self.close_application()
        
    def execute_javascript(self, script):
        return self.execute_script(script)
        
    def click_button(self, locator):
        self.click_element(locator)
        
    def click_link(self, locator):
        self.click_element(locator)
        
    def page_should_contain(self, text, loglevel='INFO'):
        script = 'var body = document.body; var textContent = body.textContent || body.innertext; return textContent.indexOf("' + text + '");'

        status = self.execute_script(script);
        
        if status > -1:
            return True
        else:
            raise AssertionError("Text NOT Found: " + text)

    def wait_until_page_contains(self, text, timeout=None, error=None):
        def check_visibility():
            try:
                status=self.page_should_contain(text)
            except Exception:
                return error or "Text '%s' was not visible in %s" % (text, self._format_timeout(timeout))
        self._wait_until_no_error(timeout, check_visibility)
    
    def page_should_not_contain(self, text, loglevel='INFO'):
        self.page_should_not_contain_text(text, loglevel)

    def dismiss_alert(self, accept=True):
        alert = self._current_application().switch_to_alert()
        if accept:
            alert.accept()
        else:
            alert.dismiss()      
        
    def get_matching_xpath_count(self, xpath, return_str=True):
        xpath = xpath.replace("'",'"')
        script = "result = []; var nodesSnapshot = document.evaluate('" + xpath + "', document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null ); for ( var i=0 ; i < nodesSnapshot.snapshotLength; i++ ) { result.push( nodesSnapshot.snapshotItem(i) ); } return result.length;"
        count = self.execute_script(script)
        return count
    
    def assign_id_to_element(self, variable, new_id):
        prefix, variable = variable.split('=',1)
        variable = variable.replace('\'','"')
        
        if prefix == 'css':
            # get file
            script = "document.querySelector('" + variable + "').id = '" + new_id + "';"
        else:
            script = "var id = document.evaluate('" + variable + "', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.id = '" + new_id + "';"
        self.execute_script(script)

    def clear_element_text(self, locator):
        self.clear_text(locator)

    def input_text(self, locator, text):
        self.clear_text(locator)
        super(SpartanLibrary, self).input_text(locator, text)

    def mouse_over(self, locator):
        BuiltIn().log('The Mouse Over was removed for mobile tests #', level='WARN')

    def list_windows(self):
        return self.get_window_titles()

    def focus(self, locator):
        BuiltIn().log('Focus was removed for mobile tests.', level='WARN')

    def simulate(self, locator, event):
        if 'event' == 'click':
            self.click_element(locator)
        # TODO: Will need to add anymore event type as we see or need them

    def get_cookie(self,name):
        driver = self._current_application()
        cookie_dict_list = driver.get_cookies()
        
        for cookie_dict in cookie_dict_list:
            # Look for the cookie with the given name
            if cookie_dict['name'] == name:
                cookie = Cookie(cookie_dict)
                return cookie
        
        raise ValueError("Cookie with name %s not found." % name)
    
    def press_key(self, locator, key):
        prefix, locator = locator.split('=',1)
        locator = locator.replace('\'','"')
        
        if prefix == 'css':
            script = 'var e1 = new Event("keydown"); e1.which=' + key + '; window.document.querySelector("' + locator + '").dispatchEvent(e1);'
            script += 'var e2 = new Event("keypress"); e2.which=' + key + '; window.document.querySelector("' + locator + '").dispatchEvent(e2);'
        else:
            script = 'var e1 = new Event("keydown"); e1.which=' + key + '; window.document.evaluate("' + locator + '", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.dispatchEvent(e1);'
            script += 'var e2 = new Event("keypress"); e2.which=' + key + '; window.document.evaluate("' + locator + '", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.dispatchEvent(e2);'
        self.execute_script(script)
    
    def get_cookies(self):
        driver = self._current_application()
        cookie_dict_list = driver.get_cookies()
        
        cookie_string = ''
        
        for cookie_dict in cookie_dict_list:
            # Some of the cookie value needed to be url encoded in the string (cdc is such a example...)
            # Replacing the {} and " value to url encode
            value = cookie_dict['value'].replace('{','%7B')
            value = value.replace('}','%7D')
            value = value.replace('"','%22')
            cookie_string += cookie_dict['name'] + '=' + value + '; '
        
        #Remove the last '; ' before returning the cookie string
        return cookie_string[:-2]
    
    def add_cookie(self, name, value, path=None, domain=None, secure=None, expiry=None):
        driver = self._current_application()
        driver.add_cookie({'name': name, 'value': value, 'path': path, 'domain': domain, 'secure': secure, 'expiry' : expiry})
    
    def get_selected_list_value(self, locator):
        return  self.get_element_attribute(locator, 'value')
    
    #### Physical and Remote device port selection Helpers ####
    def _get_device_capabilities(self, device):
        '''
        Takes the device and version run arguments and generates the capability set required to start an Appium run.
        
        *Returns:*
            - _capabilities_ - A dictionary of capabilities
        '''
        # Check/Set required variables
        if not device:
            BuiltIn.fail('Device must be specified in the run arguments.')
        
        deviceName, platform = device_name_parser().get_device_name_and_platform(device)
        capabilities = {'deviceName':deviceName, 'platform':platform, 'platformName':platform}
        
        # Get correct version value
        version, versionValue = self._get_correct_version_value(deviceName)
        
        # Adding version and platformVersion to capabilities
        capabilities['version'] = versionValue
        capabilities['platformVersion'] = version
        
        # Get necessary ports
        webdriverPort = self._get_random_free_port()
        hardwarePort = self._get_random_free_port()
        
        # Set Browser regardless of which browser was given
        if  platform.lower() == 'ios':
            self.browser = 'safari'
        elif platform.lower() == 'android':
            self.browser = 'chrome'
        
        # Set platform-specific capabilities
        if platform.lower() == 'ios':
            capabilities['wdaLocalPort'] = webdriverPort
            capabilities['webkitDebugProxyPort'] = hardwarePort
            capabilities['automationName'] = 'XCUITest'
            capabilities['browserName'] = self.browser
            capabilities['safariInitialUrl'] = 'https://www.internetbrands.com/wp-content/uploads/2014/01/logo@2x.png'
        elif platform.lower() == 'android':
            capabilities['chromedriverPort'] = webdriverPort
            capabilities['systemPort'] = hardwarePort
            capabilities['automationName'] = 'UIAutomator2'
            capabilities['browserName'] = self.browser
        
        # Physical device app
        physical_value = BuiltIn().get_variable_value("${PHYSICAL}")
        
        if physical_value:
            capabilities['physicalDevice'] = physical_value.lower() == 'true'
        
        # Get App Path (if needed) 
        app = BuiltIn().get_variable_value("${APP}")
        
        if app:
            appPath = self._generate_app_file_path(platform, physical_value, app)
            capabilities['app'] = appPath
            del capabilities['browserName']
            del capabilities['safariInitialUrl']
        
        # Set Suite Variables
        BuiltIn().set_suite_variable('$DEVICE_NAME',deviceName)
        BuiltIn().set_suite_variable('$DEVICE', deviceName)
        BuiltIn().set_suite_variable('$PLATFORM',platform)
        BuiltIn().set_suite_variable('$PLATFORMNAME',platform)
        BuiltIn().set_suite_variable('$DEVICE_OS',platform.lower())
        BuiltIn().set_suite_variable('$PHYSICAL',physical_value)
        BuiltIn().set_suite_variable('$VERSION',version)
        BuiltIn().set_suite_variable('$BROWSER',self.browser)
        
        BuiltIn().set_suite_variable('$DEVICE_CAPABILITIES',capabilities)
        
        return capabilities
        
    def _get_correct_version_value(self, deviceName):
        '''
        Generates the correct version value given the full device name.
            - If device is Android, finds the corresponding exact version number.
            - If device is iOS, checks if version argument is provided. If yes, use it as Version. If no, set it to "12.0"
            - If device is iOS, checks if device is one of the expected, "official" devices. If yes, set version_value to version. If no, set version_value to "Misc iOS".
        
        *Arguments:*
            - _deviceName_ - name of the device to run
        
        *Returns:*
            - _version_ - Actual device version, to be used in the "platformversion" capability
            - _version_value_ - The value for the "version" capability, which might be the exact device version or might be "Misc iOS" depending on the deviceName provided.
        '''
        version = BuiltIn().get_variable_value("${VERSION}")
        
        # Clear out the version variable that was set by default from GlaDos
        if version == '7' or version == '10':
            version = ''
        
        # Android Emulator Version Dictionary
        automotiveEmlatorDic = {'AndroidEmulator6':'6.0', 'AndroidEmulator7':'7.1', 'AndroidEmulator8':'8.0'}
        generalEmulatorDic = {'AndroidEmulator6':'6.0', 'AndroidEmulator7':'7.1', 'AndroidEmulator8':'8.1'}
        
        remote = BuiltIn().get_variable_value("${REMOTE}")
        
        # Set Version if not specified
        if deviceName[0] == 'i':
            version = '12.0'    # iOS
        elif deviceName[0] != 'i' and 'qa-autocom9' in remote:
            version = automotiveEmlatorDic[deviceName]
        elif deviceName[0] != 'i':
            version = generalEmulatorDic[deviceName]
        
        # Assign different version value for misc iOS devices
        version_value = version
        if deviceName not in self._hardcodedDevices:
            version_value = 'Misc iOS'
        
        return version, version_value
        
    def _get_random_free_port(self):
        '''
        Generates a port number that is likely to be free and locks it in the appium_port_tracking database. Then adds it to the list of ports used in this test so that they can be removed later.
        
        *Returns:*
            - _port_ - The chosen port number
        '''
        
        # Release any stale ports
        port_selector().release_stale_ports()
        
        # Generate and claim a new port
        port = port_selector().generate_free_port_number()
        
        testName = BuiltIn().get_variable_value("${TEST_NAME}")
        port_selector().claim_port(port,testName)
        
        # Append the claim port to the list of ports in use
        self._ports_list.append(port)
        
        return port
    
    def _generate_app_file_path(self, platform, physical, app):
        '''
        Generates the absolute file path for the application.
        
        *Precondition*: (for non-None result)
            - _APP_ must exist, with the exact name of the app, minus the file extension.
            - _PATH_MOBILE_APPLICATIONS_ must exist, containing the path to the folder containing all mobile applications (on the remote Macs)
            - _DEVICE_OS_ must be set to either Android or iOS
            - _PHYSICAL_ may be set, but if not, it will default to PHYSICAL=False
        
        *Returns*:
            - _filePath_ - The absolute file path
        '''
        # Determine extension
        extension = ''
        
        if platform.lower() == 'android':
            extension = 'apk'
        elif platform.lower() == 'ios' and physical:
            extension = 'ipa'
        elif platform.lower() == 'ios' and not physical:
            extension = 'app'
        
        # Create the mobile application path url
        path_mobile_applications = BuiltIn().get_variable_value("${PATH_MOBILE_APPLICATIONS}")
        environment = BuiltIn().get_variable_value("${ENVIRONMENT}")
        filepath = '' + path_mobile_applications + '/' + app + '_' + environment.lower() + '.' + extension
        
        return filepath

###############
### OBJECTS ###

class Cookie(object):
    # Cookie object
    def __init__(self, cookie_dict):
        '''
        Takes in the cookie as a dictionary and creates a cookie object
        '''
        self.name = cookie_dict.get("name","")
        self.value = cookie_dict.get("value","")
        self.path = cookie_dict.get("path","")
        self.domain = cookie_dict.get("domain","")
        self.secure = cookie_dict.get("secure","")
        self.httpOnly = cookie_dict.get("httpOnly","")
        self.expiry = cookie_dict.get("expiry","")