# Ansible Cloud Module for AWS
#### Version 0.1 [![Build Status](https://travis-ci.org/pjodouin/ansible-boto3.svg)](https://travis-ci.org/pjodouin/ansible-boto3)

This module helps manage AWS resources using the boto3 SDK.


## Requirements
- python >= 2.6
- ansible >= 2.0
- boto3 >= 1.2.3
- importlib (only for running tests on < python 2.7)

## Module:  aws

Makes a call to the AWS API using the boto3 SDK.

##### Example Command
`> ansible localhost -m aws -a "service=ec2 method=describe_instances"`

##### Example Playbook
```yaml
- hosts: localhost
  connection: local
  gather_facts: no
  vars:
    state: present

  - name: "get EC2 instances"
    aws:
      service: ec2
      method: describe_instances
      params:
        DryRun: False
    register: ec2_instances

  - debug:
      msg: "{{ ec2_instances }}"

  - name: "get RDS instances"
    aws:
      service: rds
      method: describe_db_instances
    register: db_instances

  - debug:
      msg: "{{ db_instances }}"

  - name: "create security group"
    aws:
      service: ec2
      method: create_security_group
      params:
        DryRun: True
        GroupName: Boto3ApiGroup
        Description: boto3 security group created via aws module

    register: ec2_sg

  - debug:
      msg: "{{ ec2_sg }}"
```
___

## Installation

Do the following to install the lambda modules in your Ansible environment:

1. Clone this repository or download the ZIP file.

2. Copy the *.py files from the library directory to your installation custom module directory.  This is, by default, in `./library` which is relative to where your playbooks are located. Refer to the [docs](http://docs.ansible.com/ansible/developing_modules.html#developing-modules) for more information.

3. Make sure boto3 is installed.








