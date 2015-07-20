#!/usr/bin/env python

"""
     Copyright (c) 2015 World Wide Technology, Inc. 
     All rights reserved. 

     Revision history:
     17 July 2015  |  1.0 - initial release
     20 July 2015  |  1.1 - added documentation and error checking
 
"""

DOCUMENTATION = '''
---
module: apic_em_gather_facts
author: Joel W. King, World Wide Technology
version_added: "1.1"
short_description: query the APIC-EM controller for an inventory of network devices
description:
    - This module issues a query of an APIC-EM controller to obtain the addresss of network devices in the inventory
      and return this to the playbook for subsequent tasks in a playbook. The APIC-EM is designed to be a
      "single source of truth" for the network inventory.


references:
      http://docs.ansible.com/add_host_module.html
      https://pynet.twb-tech.com/blog/ansible/dynamic-inventory.html

 
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

 $ ./hacking/test-module -m /home/administrator/ansible/lib/ansible/modules/extras/network/apic_em_gather_facts.py 
                         -a "username=bob password=xxxxxx host=10.255.40.125"             
***********************************
PARSED OUTPUT
{
    "ansible_facts": {
        "mgmtIp": [
            "10.255.138.120",
            "10.255.138.121",
            "10.255.138.123",
            "10.255.138.122"
        ]
    },
    "changed": false
}


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
      Connection class for Python to APIC-EM controller REST Calls, CA2 distribution.

      Examples of how to test interactively from Python.

         k = Connection()
         status, msg = k.aaaLogin("10.255.40.125", 'bob', 'xxxxxx')
         status, msg = k.genericGET("/api/v1/network-device/count")
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
#
#
#
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
#
#
#
    def genericGET(self, URL):
        """
         Issue an HTTP GET base on the URL passed as an argument and example in cURL is:
  
         $ curl -k -H "X-Auth-Token: <your-ticket>" 
                   https://<controller-ip>/api/v1/network-device/count
        """
        URL = "%s%s%s" % (self.transport, self.controllername, URL)
        try:
            r = requests.get(URL, headers=self.serviceTicket, verify=False)
        except requests.ConnectionError as e:
            return (False, e)
        content = json.loads(r.content)
        return (r.status_code, content['response'])



# ---------------------------------------------------------------------------
# get_discovered_devices
# ---------------------------------------------------------------------------

def get_discovered_devices(cntrl):
    """ Query controller for device level reachability information for all devices.
        Returned is a list of dictionaries describing the network device, for example:

        [{u'discoveryId': u'938fb083-be67-4a72-9306-10aacffe26c8',
          u'discoveryStartTime': u'2015-07-17 19:11:16.932452+00',
          u'enablePassword': u'*****',
          u'id': u'035cde8e-bf12-400c-b510-adc23bafcf73',
          u'mgmtIp': u'10.255.138.120',
          u'password': u'*****',
          u'protocolList': u'SSH,TELNET,HTTPS,HTTP',
          u'protocolUsed': u'SSH',
          u'reachabilityStatus': u'Discovered',
          u'userName': u'admin'}]

       Currently only returning the management IP address, but ideally we should return the
       passwords, so we don't have to maintain them in Ansible. 

    """
    element = { 'mgmtIp' : [] }
    result = { 'ansible_facts': {} }                      
    
    status, response = cntrl.genericGET("/api/v1/reachability-info")
    for device in response:
        try:
            if device["reachabilityStatus"] == "Discovered":
                element['mgmtIp'].append(device['mgmtIp'])
        except KeyError:
            pass

    logoff()
    result["ansible_facts"] = element
    return status, result


# ---------------------------------------------------------------------------
# logoff
# ---------------------------------------------------------------------------

def logoff():
    """ Need documentation if logoff is implemented or necessary """
    return


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    "   "
    module = AnsibleModule(
        argument_spec = dict(
            host = dict(required=True),
            username = dict(required=True),
            password  = dict(required=True),
            debug = dict(required=False)
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
main()


