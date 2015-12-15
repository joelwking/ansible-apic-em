#!/usr/bin/env python

"""
     Copyright (c) 2015 World Wide Technology, Inc. 
     All rights reserved. 

     Revision history:
     17 July 2015  |  1.0 - initial release
     20 July 2015  |  1.1 - added documentation and error checking
     15 Dec  2015  |  1.2 - Updates for the GA release, APIC-EM Version 1.0.1.30
                      1.3 - Documentation update
 
"""

DOCUMENTATION = '''
---
module: apic_em_gather_facts
author: Joel W. King, World Wide Technology
version_added: "1.3"
short_description: query the APIC-EM controller for an inventory of network devices.
description:
    - This module issues a query of an APIC-EM controller to obtain the addresss of network devices in the inventory
    - and return this to the playbook for subsequent tasks in a playbook. The APIC-EM is designed to be a
    - single source of truth for the network inventory.


references:
    - The API documenation is available via the web interface of the APIC-EM server

requirements:
    - none

options:
    host:
        description:
            - The IP address or hostname of the APIC-EM controller
        required: true

    username:
        description:
            - Login username
        required: true

    password:
        description:
            - Login password
        required: true

    debug:
        description:
            - debug switch
        required: false


'''

EXAMPLES = '''

    Module

    $ ansible localhost -m apic_em_gather_facts.py -a "host=10.255.93.205 username=admin password=redacted\!"

    Playbook

    ---
    #
    - name:  Gather facts using APIC-EM
      hosts:  localhost
      connection: local
      gather_facts: no

      tasks:
      - name: test
        apic_em_gather_facts:
           host: 192.0.2.1      # APIC-EM server
           username: admin
           password: redacted

      - name: test
        debug: msg="{{item.managementIpAddress}} {{item.series}}"
        with_items: network_device




'''


import sys
import time
import json
import requests



# ---------------------------------------------------------------------------
# APIC-EM Connection Class
# ---------------------------------------------------------------------------

class Connection(object):
    """
      Connection class for Python to APIC-EM controller REST Calls, APIC-EM Version 1.0.1.30

      Testing interactively from Python, load the class and invoke it:

         k = Connection()
         status, msg = k.aaaLogin("10.255.93.205", 'admin', 'redacted')
         status, msg = k.genericGET("/api/v1/network-device/", scope="ALL")
         status, msg = k.genericGET("/api/v1/reachability-info")
   
    """

    def __init__(self):                               
        self.api_version = "1.0"
        self.transport = "https://"
        self.controllername = "192.0.2.1"
        self.username = "admin"
        self.password = "admin"
        self.HEADER = {"Content-Type": "application/json"}
        self.serviceTicket = {"X-Auth-Token: <your-ticket>"}

        return



    def aaaLogin(self, controllername, username, password):
        """ 
        Logon the controller, need to pass the userid and password, and in return we get a token.
        Do not know how log the token is valid. An example in cURL is

         $ curl -k -H "Content-Type: application/json" 
                   -X POST -d '{"username": "<username>", "password": "<password>"}' 
                   https://<controller-ip>/api/v1/ticket
        """
        self.controllername = controllername
        self.username = username
        self.password = password

        URL = "%s%s/api/v1/ticket" % (self.transport, self.controllername)
        DATA = {"username": self.username, "password": self.password}
        try:
            r = requests.post(URL, data=json.dumps(DATA), headers=self.HEADER, verify=False)
        except requests.ConnectionError as e: 
            return (False, str(e))
        else:
            content = json.loads(r.content)
            try:
                self.api_version = content["version"]
                self.serviceTicket = {"X-Auth-Token": content["response"]["serviceTicket"]}
            except KeyError:
                return (False, "Login failure")
            else:
                return (r.status_code, content)



    def genericGET(self, URL, scope="ALL"):
        """
         Issue an HTTP GET base on the URL passed as an argument and example in cURL is:
  
         $ curl -k -H "X-Auth-Token: <your-ticket>" 
                   https://<controller-ip>/api/v1/network-device/count
        """
        URL = "%s%s%s" % (self.transport, self.controllername, URL)
        headers = self.serviceTicket                       # serviceTicket provides authentication
        headers["scope"] = scope                           # GA release needs a scope in the header

        try:
            r = requests.get(URL, headers=headers, verify=False)
        except requests.ConnectionError as e:
            return (False, e)
        content = json.loads(r.content)
        return (r.status_code, content['response'])



    def logoff(self):
        """ Need documentation if logoff is implemented or necessary """
        return

# ---------------------------------------------------------------------------
# MAIN program and functions
# ---------------------------------------------------------------------------

def get_discovered_devices(cntrl):
    """ Query controller for device level reachability information for all devices.
        
        For information on the response body, see the API documentation on the APIC-EM device
        https://<apic-em>/swagger#!/network-device/getAllNetworkDevice

        Only return devices that are reachable. 

    """
    element = { 'network_device' : [] }
    result = { 'ansible_facts': {} }                 
    
    status, response = cntrl.genericGET("/api/v1/network-device", scope="ALL")
    for device in response:
        try:
            if device["reachabilityStatus"] == "Reachable":
                element["network_device"].append(device)
        except KeyError:
            pass

    cntrl.logoff()
    result["ansible_facts"] = element
    return status, result



def main():
    "   "
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True),
            debug=dict(required=False)
         ),
        check_invalid_arguments=False,
        add_file_common_args=True
    )

    cntrl = Connection()
    connected, msg = cntrl.aaaLogin(module.params["host"], module.params["username"], module.params["password"])
    if connected:
        code, response = get_discovered_devices(cntrl)
        if code == 200:
            module.exit_json(**response)
        else:
            module.fail_json(msg="status_code= %s" % code)
    else:
        module.fail_json(msg=msg)



from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
