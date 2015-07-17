#!/usr/bin/env python

"""
     Copyright (c) 2014 World Wide Technology, Inc. 
     All rights reserved. 

     Revision history:
     17 July 2015  |  1.0 - initial release
 
"""

DOCUMENTATION = '''
---
module: apic_em_gather_facts
author: Joel W. King, World Wide Technology
version_added: "1.0"
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


'''

EXAMPLES = '''

 

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
      Connection class for Python to APIC-EM controller REST Calls, CA2 distribution,
      to test this class use the following from your main program or interpreter:

         k = Connection()
         status, msg = k.aaaLogin("10.255.40.125", 'kingjoe', 'foobar')
         status, msg = k.genericGET("/api/v1/network-device/count")
   
    """
    def __init__(self):                               
        self.version = "1.0"
        self.transport = "https://"
        self.controllername = "192.0.2.1"
        self.username = "admin"
        self.password = "admin"
        self.HEADER = {"Content-Type": "application/json"}
        self.serviceTicket = {"X-Auth-Token: <your-ticket>"}

        return
    def aaaLogin(self, controllername, username, password):
        """ 
         $ curl -k -H "Content-Type: application/json" 
                   -X POST -d '{"username": "<username>", "password": "<password>"}' 
                   https://<controller-ip>/api/v1/ticket
        """
        self.controllername = controllername
        URL = "%s%s/api/v1/ticket" % (self.transport, self.controllername)
        DATA = {"username": username, "password": password}
        try:
            r = requests.post(URL, data=json.dumps(DATA), headers=self.HEADER, verify=False)
        except requests.ConnectionError as e: 
            return (False, e)
        else:
            content = json.loads(r.content)
            try:
                self.version = content["version"]
                self.serviceTicket = {"X-Auth-Token": content["response"]["serviceTicket"]}
            except KeyError:
                return (False, "KeyError")
            else:
                return (r.status_code, content)

    def genericGET(self, URL):
        """
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
# PROCESS
# ---------------------------------------------------------------------------

def process(cntrl):
    """ We have all are variables and parameters set in the object, attempt to 
        login and post the data to the APIC
    """

    if cntrl.aaaLogin() != 200:
        return (1, "Unable to login to controller")

    rc = cntrl.genericGET()
    if rc == 200:
        return (0, format_content(cntrl.get_content()))
    else:
        return (1, "%s: %s" % (rc, httplib.responses[rc]))


# ---------------------------------------------------------------------------
# FORMAT_CONTENT
# ---------------------------------------------------------------------------
def format_content(content):
    """ formats the content into an Ansible fact 

    from ACI a class query returns:
   
     dict         list       dict        dict
    "imdata"    [ aaaUser: attributes: elements, ...]
    "totalcount"
    
    Here is an example of the core setup module

    $ ./bin/ansible 10.255.40.207 -m setup --ask-pass -a 'filter=ansible_all_ipv4_addresses'
    SSH password:
    10.255.40.207 | success >> {
        "ansible_facts": {
            "ansible_all_ipv4_addresses": [
                "10.255.40.207"
            ]
        },
        "changed": false
    }

    """
    element = {}                                           # dictionary to hold the class
    result = { 'ansible_facts': {} }                       # the result is a dictionary with one element called 'ansible_facts'
    content = json.loads(content)["imdata"]                # remove the IMDATA wrapper
    for item in content:                                   # content is a *list* of one or more elements returned for the class query
        d_item = dict(item)
        aci_class = d_item.keys()[0]                       # get the name of the class we queried
        try:
            element[aci_class]
        except KeyError:
            element[aci_class] = []                        # each returned MO is a list element

        attributes = d_item[aci_class]["attributes"]
        element[aci_class].append(attributes)              # append the MO to our class dictionary

    result["ansible_facts"] = element
    return result
        

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():

    module = AnsibleModule(
        argument_spec = dict(
            queryfilter = dict(required=False),
            URI = dict(required=True),
            host = dict(required=True),
            username = dict(required=True),
            password  = dict(required=True),
            debug = dict(required=False)
         ),
        check_invalid_arguments=False,
        add_file_common_args=True
    )
    
    cntrl = AnsibleACI.Connection()
    cntrl.setcontrollerIP(module.params["host"])
    cntrl.setUsername(module.params["username"])                               
    cntrl.setPassword(module.params["password"])

    cntrl.setgeneric_URL("%s://%s" + module.params["URI"] + queryfilter)
                                  
    code, response = process(cntrl)
    cntrl.aaaLogout()

    if code == 1:
        module.fail_json(msg=response)
    else:
        module.exit_json(**response)
  
    return code


from ansible.module_utils.basic import *
main()


