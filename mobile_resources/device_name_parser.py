from __future__ import print_function
from builtins import str
from builtins import object
import re
import os

REGEX_ANDROID = "^(android)?(emulator)?([\d\.]+)$"
REGEX_IOS = "^i(phone|pad)(.*)$"
REGEX_IPHONE = "(\d)(s)?(plus)?|(\w{1,2})(max)?"
REGEX_IPAD = "^(air|pro)?(2)?([\d\.]+)?(inch|in)?(\d[stndrh]{2})?(gen.*)?$"
DEFAULT_REGEX_ANDROID = "^(android)?(emulator)?$"
DEFAULT_REGEX_IOS = "^i(phone|pad(air)?)$"


class device_name_parser(object):
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    
    def __init__(self):
        return
    
    def _determine_platform(self, device):
        """
        Returns the OS platform name for the given device. Uses self.deviceName if no device provided.
        """
        if re.match(REGEX_IOS,device):
            return "iOS"
        elif re.match(REGEX_ANDROID,device):
            return "Android"
        else:
            raise Exception("The provided device name '{}' does not match the expected formats for either iOS or Android.".format(device))
    
    def _determine_fullname(self, device):
        """
        Takes the deviceName and determines whether it matches the Android format or the iOS format.
        Then runs the corresponding parsing method to generate the proper name of the device.
        
        Arguments:
            device - (optional string) if given, will get the name of that device. If left blank, method will use self.deviceName
        
        Returns:
            fullName - (string) the full, proper name of the device
        """
        androidGroups = re.findall(REGEX_ANDROID, device)
        iosGroups = re.findall(REGEX_IOS, device)
        if iosGroups!=[]:
            deviceType = iosGroups[0][0]
            model = iosGroups[0][1]
            fullName = self._parse_ios(deviceType, model)
        elif androidGroups!=[]:
            androidVersion = androidGroups[0][2]
            fullName = "AndroidEmulator"+androidVersion
        else:
            raise Exception("The provided device name '{}' does not match the expected formats for either iOS or Android.".format(device))
        
        print("Given name '{}' translated to '{}'.".format(device,fullName))
        return fullName
    
    def _parse_ios(self, deviceType, model):
        fullName = "i" + deviceType.title()
        
        if deviceType=="phone":
            try:
                splitModel = re.findall(REGEX_IPHONE,model)[0]
            except IndexError:
                raise Exception("The given iPhone type '{}' does not correspond to a known iPhone model.")
            fullName = fullName + (" " + splitModel[0])*(splitModel[0]!="") # Number (5,6,7,8)
            fullName = fullName + splitModel[1].lower()*(splitModel[1]!="") # s (e.g. "6s")
            fullName = fullName + (" " + splitModel[2].title())*(splitModel[2]!="") # Plus
            fullName = fullName + (" " + splitModel[3].upper())*(splitModel[3]!="") # X/SE/XS/XR
            fullName = fullName + (" " + splitModel[4].title())*(splitModel[4]!="") # Max
        elif deviceType=="pad":
            try:
                splitModel = re.findall(REGEX_IPAD,model)[0]
            except IndexError:
                raise Exception("The given iPad type '{}' does not correspond to a known iPad model.")
            fullName = fullName + (" " + splitModel[0].title())*(splitModel[0]!="") # Air/Pro
            fullName = fullName + (" " + splitModel[1])*(splitModel[1]!="") # 2 (e.g. "Air 2")
            fullName = fullName + (" ({}-inch)".format(splitModel[2]))*(splitModel[2]!="") # Inches
            fullName = fullName + (" ({} generation)".format(splitModel[4]))*(splitModel[4]!="") # Generation
        return fullName
    
    def get_device_name_and_platform(self, device):
        """
        Gets the full name and platform of device.
        
        *Arguments:*
        - _device_ - raw device name/alias from run arguments
        
        *Returns:*
        - _fullName_ - full name of device
        - _platform_ - platform of device
        """
        # Lowercase the device name
        if device is not None:
            device = device.lower()
            device = device.strip().replace(" ","")
        # If given vague iphone/ipad/android then set the default device
        if re.match(DEFAULT_REGEX_IOS,device):
            # Set to default to iphone6 for automotive and iphone7 all other vertical
            if 'iphone' == device:
                '''
                try:
                    directory = str(os.path.abspath(__file__))
                    print "Dir: " + directory
                    if 'Automotive_Automation' in directory:
                        device = 'iphone6'
                    else:
                        device = 'iphone7'
                except:
                    device = 'iphone7'
                '''
                device = 'iphone6'
            else:
                device = 'ipadair2'
        elif re.match(DEFAULT_REGEX_ANDROID,device):
            device = 'androidemulator8'
        
        print("Device: " + str(device))
        # Get full name, and platform
        fullName = self._determine_fullname(device)
        platform = self._determine_platform(device)
        
        print("Actual Name: " + str(fullName))
        print("Actual Name: " + str(platform))
        return fullName, platform
        
if __name__ == "__main__":
    test = device_name_parser()
    print(test.get_device_name_and_platform('iphone'))