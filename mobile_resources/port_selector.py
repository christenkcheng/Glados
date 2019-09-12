from builtins import object
import time, random
from database_lib import *

class port_selector(object):
    
    def __init__(self, min=None,max=None):
        self.db = "qaa" # Target port locking database
        self.portMin = min if min != None else 29170
        self.portMax = max if max != None else 29980
    
    def _get_ports_in_use(self):
        """
        Queries the database and gets a list of ports that are currently in use.
        """
        query = "SELECT port from qaa.appium_port_tracking;"
        
        portList = run_query(self.db, query)
        portList_flattened = [int(p[0]) for p in portList]
        return portList_flattened
    
    def generate_free_port_number(self):
        """
        Generates a port number that is most likely free.
        """
        portsInUse = self._get_ports_in_use()
        while True:
            port = random.randint(self.portMin,self.portMax)
            if port not in portsInUse:
                break
        return port
    
    def claim_port(self, port, testcase):
        """
        Enters the port number, test case name, and current time into the port tracking table.
        """
        query = "INSERT INTO qaa.appium_port_tracking VALUES ({},'{}',CURRENT_TIMESTAMP());"
        run_query(self.db, query.format(int(port),testcase))
    
    def release_port(self, port):
        """
        Deletes the entry from the database that matches the given port number, thus releasing it for other tests.
        """
        query = "DELETE FROM qaa.appium_port_tracking WHERE port={};"
        run_query(self.db, query.format(int(port)))
    
    def release_stale_ports(self):
        """
        Deletes all entries from the database where the timestamp is from longer than 2 hour ago, since no single test is going to take 2 full hours to run.
        """
        query = "DELETE FROM qaa.appium_port_tracking WHERE timestamp < DATE_SUB(NOW(), INTERVAL 2 HOUR);"
        run_query(self.db, query)