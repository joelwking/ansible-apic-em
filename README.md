# ansible-apic-em
Ansible module for APIC-EM integration

# Blog
https://communities.cisco.com/community/developer/blog/2015/07/20/using-apic-em-as-the-single-source-of-truth

# Use Case

This module issues a query to an APIC-EM controller for all reachable network devices and returns the variables documeted in the
https://<apic-em>/swagger#!/network-device/getAllNetworkDevice API.

A sample playbook (ios_show.yml) is included in the repository, which would be used with this sample inventory file and group_vars file.

~/ansible/playbooks/hosts
```
[APIC_EM]
localhost ansible_connection=local ansible_ssh_user=administrator
```

~/ansible/playbooks/group_vars/APIC_EM
```
#
username: admin
debug: off
dest: /tmp
```
