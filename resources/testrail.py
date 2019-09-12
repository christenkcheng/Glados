#
# TestRail API binding for Python (API v2, available since TestRail 3.0)
#
# Learn more:
#
# http://docs.gurock.com/testrail-api2/start
# http://docs.gurock.com/testrail-api2/accessing
#
# Copyright Gurock Software GmbH. See license.md for details.
#

from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

from builtins import object
import requests
import json

class APIClient(object):
    def __init__(self, base_url):
        self.user = ''
        self.password = ''
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'
        self.headers = {'Content-Type': 'application/json'}

    #
    # Send Get
    #
    # Issues a GET request (read) against the API and returns the result
    # (as Python dict).
    #
    # Arguments:
    #
    # uri                 The API method to call including parameters
    #                     (e.g. get_case/1)
    #
    def send_get(self, uri):
        url = self.__url + uri
        try: 
            response = requests.get(url, auth=(self.user, self.password), headers=self.headers)
            if not response.status_code // 100 == 2: 
                raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, response.json()))
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            raise e


    #
    # Send POST
    #
    # Issues a POST request (write) against the API and returns the result
    # (as Python dict).
    #
    # Arguments:
    #
    # uri                 The API method to call including parameters
    #                     (e.g. add_case/1)
    # data                The data to submit as part of the request (as
    #                     Python dict, strings must be UTF-8 encoded)
    #
    def send_post(self, uri, data):
        url = self.__url + uri
        try: 
            response = requests.post(url, data=json.dumps(data), auth=(self.user, self.password), headers=self.headers)
            if not response.status_code // 100 == 2: 
                raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, response.json()))
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            raise e

class APIError(Exception):
    pass
