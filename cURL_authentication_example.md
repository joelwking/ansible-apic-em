* Documentation on how to authenticate with APIC-EM CA2
This info was provided by Cisco TAC for the CA2 release


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

Documentation on the API is available from the GUI of APIC-EM CA2