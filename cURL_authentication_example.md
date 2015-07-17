# Documentation on how to authenticate with APIC-EM CA2
This info was provided by Cisco TAC for the CA2 release.

First you need to authenticate with the controller and obtain a
token/ticket:
```
$ curl -k -H "Content-Type: application/json" -X POST -d '{"username": "<username>", "password": "<password>"}' https://<controller-ip>/api/v1/ticket
```
If authentication was successful, the response would be in the following
form:
```
{"response":{"serviceTicket":"<your-ticket>"},"version":"1.0"}
```
Then pass the token you just obtained in the HTTP headers in subsequent API calls:
```
$ curl -k -H "X-Auth-Token: <your-ticket>" https://<controller-ip>/api/v1/network-device/count
```

Documentation on the API is available from the GUI of APIC-EM CA2.

Here is a code snippet of the above implemented in Python:

```
import json
import requests

# ---------------------------------------------------------------------------# APIC-EM Connection Class# ---------------------------------------------------------------------------class Connection(object):
    """      Connection class for Python to APIC-EM controller REST Calls, CA2 distribution,
      to test this class use the following from your main program or interpreter:

         k = Connection()
         status, msg = k.aaaLogin("10.255.40.125", 'kingjoe', 'foobar')
         status, msg = k.genericGET("/api/v1/network-device/count")       """    def __init__(self):                                       self.version = "1.0"
        self.transport = "https://"
        self.controllername = "192.0.2.1"        self.username = "admin"        self.password = "admin"
        self.HEADER = {"Content-Type": "application/json"}
        self.serviceTicket = {"X-Auth-Token: <your-ticket>"}

        return
    def aaaLogin(self, controllername, username, password):        """ 
         $ curl -k -H "Content-Type: application/json" 
                   -X POST -d '{"username": "<username>", "password": "<password>"}' 
                   https://<controller-ip>/api/v1/ticket        """        self.controllername = controllername        URL = "%s%s/api/v1/ticket" % (self.transport, self.controllername)        DATA = {"username": username, "password": password}        try:            r = requests.post(URL, data=json.dumps(DATA), headers=self.HEADER, verify=False)        except requests.ConnectionError as e:             return (False, e)        else:
            content = json.loads(r.content)            try:
                self.version = content["version"]
                self.serviceTicket = {"X-Auth-Token": content["response"]["serviceTicket"]}            except KeyError:                return (False, "KeyError")            else:                return (r.status_code, content)
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
```