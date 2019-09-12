"""
this module is for uploading test run artifacts to a web host. things like screenshots and logs
so they can be linked from testrail
"""
from __future__ import print_function
from builtins import str
from builtins import range
from builtins import object
import ftplib
from datetime import datetime
import os

class TestRailFTP(object):
    """interact with the testrail ftp"""
    UPLOAD_ROOT = "uploads/automation"
    WEB_FOLDER = "/files"
    FTP_USER = "anonymous"
    FTP_PASS = "anonymous"
    FTP_HOST = "testrail.internetbrands.com"
    project_name = None
    upload_path = None
    ftp = None

    def __init__(self, project_name):
        self.project_name = project_name

    @staticmethod
    def _files_and_their_paths(source_directory):
        """internal function to give the file name and full path for easier consumption by ftp.storbinary()"""
        source_pairs = ((file_name, source_directory + os.sep + file_name) for file_name in os.listdir(source_directory))
        return(source_pairs)

    def _create_sub_directories(self):
        """Takes a path and starting from root recursively create each child if it doesn't exist
        """
        directories = self.upload_path.split("/") #don't use os.sep, we may execute this code on windows when ftp is nix
        for i in range(1, len(directories)): #use a 1-based range so we don't hit out of bounds exception
            parent_directory = "/".join(directories[0:i])
            child_directory = parent_directory + "/" + directories[i]
            if child_directory not in self.ftp.nlst(parent_directory):
                print("sub_directory " +  child_directory +  " does not exist, creating it now")
                self.ftp.mkd(child_directory)

    def _find_expired_directories(self, months_to_keep):
        """returns a list of directories past the months_to_keep
        expiration range. doesn't delete them because ftplib doesn't support rm -R
        """
        self.ftp = ftplib.FTP(self.FTP_HOST, self.FTP_USER, self.FTP_PASS)
        year_format = '/'.join((self.UPLOAD_ROOT, self.project_name, '{year_ph}'))
        month_format = '/'.join((year_format, '{month_ph}'))
        today = datetime.now() #break this and the other similar code into init code
        keepers = {}
        year, month = today.year, today.month
        #form a structure to track which years/months to keep, always keep most recent month
        keepers.setdefault(today.year, []).append(today.month)
        while  months_to_keep:
            if not month: #0 isn't a month; back to previous year
                month = 12
                year -= 1
            else:
                keepers.setdefault(year, []).append(month)
                month -= 1
            months_to_keep -= 1
        years_to_keep = [year_format.format(year_ph=year) for year in list(keepers.keys())]
        months_to_keep = [month_format.format(year_ph=year, month_ph=str(month).zfill(2)) for year in list(keepers.keys()) for month in keepers[year]]
        years_to_toss = [year for year in self.ftp.nlst(self.UPLOAD_ROOT + '/' + self.project_name) if year not in years_to_keep]
        months_to_toss = [month for year in years_to_keep for month in self.ftp.nlst(year) if month not in months_to_keep]
        deletion_targets = years_to_toss + months_to_toss
        self.ftp.close()
        return(deletion_targets)

    def upload_output_directory(self, output_directory):
        """FOR USE WITH GLADOS ONLY.
        Given the full path to an output directory, creates a run directory if one does not already exist
        in the web folder, then uploads the output directory to the run directory.

        Returns a url to the output directory.

        EXAMPLE
        output_directory = C:\AutomotiveECommerce\automotive_automation\working_copy\sprint_12\glados\logs\7597_firefox_09102014_114423\quick_quote_daytrade_leads

        Creates, /automation/a2/7597_firefox_09102014_114423
        if it does not already exist then uploads the output directory, quick_quote_daytrade_leads

        Returns the URL, http://172.16.6.74/automation/a2/7597_firefox_09102014_114423/quick_quote_daytrade_leads
        """
        self.ftp = ftplib.FTP(self.FTP_HOST, self.FTP_USER, self.FTP_PASS)

        # Get the test run directory and the output directory
        run_dir_path = os.path.split(output_directory)[0]
        run_dir = os.path.split(run_dir_path)[1]
        output_dir = os.path.split(output_directory)[1]

        # Create a destination on the ftp
        today = datetime.now()
        self.upload_path = "{upload_root_ph}/{project_ph}/{year_ph}/{month_ph}/{run_directory_ph}/{output_directory_ph}".format(upload_root_ph=self.UPLOAD_ROOT, project_ph=self.project_name, year_ph=str(today.year), month_ph=str(today.month).zfill(2), run_directory_ph=run_dir, output_directory_ph=output_dir)
        print(self.upload_path)
        self._create_sub_directories()

        # Upload the output directory and its contents
        self.ftp.cwd(self.upload_path)
        source_pairs = self._files_and_their_paths(output_directory)
        for file_name, full_path in source_pairs:
            self.ftp.storbinary("STOR " + file_name, open(full_path, "rb"))
        web_path = self.ftp.host + self.WEB_FOLDER + self.ftp.pwd()

        # Return URL to the directory
        url = "http://" + web_path
        self.ftp.close()
        return(url)

