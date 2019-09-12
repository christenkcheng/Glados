"""
To be imported into glados_keywords.txt

More complicated code is grouped into functions here to avoid cluttering
the glados_keywords.txt file.
"""
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import os
import urllib.request, urllib.parse, urllib.error
import re
from robot.libraries.BuiltIn import BuiltIn
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import sys

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
    
    split_path = output_dir.split(os.sep+'glados'+os.sep+'logs'+os.sep)

    build_name = split_path[0]
    # Possible beginning of output_dir: "/var/www/jenkins/workspace/", "C:/Jenkins/workspace/"
    # remove everything from the beginning of the string to "/jenkins/workspace/" (case insensitive)
    build_name = re.sub(re.compile("^.*?[/\\\\]jenkins[/\\\\]workspace[/\\\\]", re.I), '', build_name)

    subfolder = ""
    if build_name.count(os.sep) > 0:
        build_name, subfolder = build_name.split(os.sep, 1)

    test_run, test_folder = split_path[1].split(os.sep) # e.g. 15049_chrome_1234 as the test run, 'testFolder' as test folder
    
    log_folder_url = url_template.format(jenkins_url_ph=jenkins_url, build_name_ph=build_name, subfolder_ph=subfolder, test_run_ph=test_run, test_folder_ph=test_folder)
    
    # now do some clean up for special characters
    log_folder_url = urllib.parse.quote(log_folder_url, "/:")
    
    
    return log_folder_url
    

def is_a_browser_open():
    """
    Returns True if at least one browser window is open, else returns False
    """
    browserOpen = False
    try:
        driver = BuiltIn().get_library_instance("SeleniumLibrary")
        if driver._current_browser():
            browserOpen = True
    except:
        print(sys.exc_info()[1])

    try:
        driver = BuiltIn().get_library_instance("Selenium2Library")
        if driver._current_browser():
            browserOpen = True
    except:
        print(sys.exc_info()[1])

    try:
        from AppiumLibrary import AppiumLibrary
        myappium = BuiltIn().get_library_instance("SpartanLibrary")
        if myappium.get_driver_instance():
            browserOpen = True
    except:
        print(sys.exc_info()[1])
    return browserOpen

