# Ansible Cloud Module for AWS API - Boto3 SDK
#### Version 0.2 [![Build Status](https://travis-ci.org/pjodouin/ansible-boto3.svg)](https://travis-ci.org/pjodouin/ansible-boto3)

This module helps manage AWS resources using the boto3 SDK.  It is not idempotent and does not support `check` mode but it does allow
one to include new AWS services in playbooks until *CloudFormation* support is provided or a custom Ansible module is written.


## Requirements
- python >= 2.6
- ansible >= 2.0
- boto3 >= 1.2.3
- importlib (only for running tests on < python 2.7)

## Module:  aws

Makes a call to the AWS API using the boto3 SDK.

##### Example Command
`> ansible localhost -m aws -a "service=ec2 method=describe_instances"`

##### Example Playbooks
```yaml
# Describe EC2 & RDS instances and create a security group.
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
```yaml
# Synthesize speech with AWS Polly
- hosts: localhost
  connection: local
  gather_facts: no

  tasks:
  - name: Synthesize Speech
    aws:
      service: polly
      method: synthesize_speech
      params:
        OutputFormat: mp3
        VoiceId: Joanna
        TextType: ssml
        Text: '<speak><prosody rate="medium" volume="medium" pitch="medium"><emphasis level="strong">Hi.</emphasis> I am your personal assistant. <break time="600ms"/>How can I be of assistance?</prosody></speak>'

    register: speech_results

  - debug:
      msg: "{{ speech_results }}"

```

```yaml

#  Example showing how to create Application Load Balancer Target Groups by iterating through a list.  Note support for the use of the 'omit' keyword.

- name: "Create ALB Target Groups"
  aws:
    service: elbv2
    method: create_target_group
    region: "{{ region }}"
    params:
      Name: "{{ item.target_group.name }}"
      Protocol: "{{ item.target_group.protocol | upper }}"
      Port: "{{ item.target_group.port }}"
      VpcId: "{{ vpc_id }}"
      HealthCheckProtocol: "{{ item.target_group.health_check_protocol | default(omit) }}"
      HealthCheckPort: "{{ item.target_group.health_check_port | default(omit) }}"
      HealthCheckPath: "{{ item.target_group.health_check_path | default(omit) }}"
      HealthCheckIntervalSeconds: "{{ item.target_group.health_check_interval_seconds | default(30) }}"
      HealthCheckTimeoutSeconds: "{{ item.target_group.health_check_timeout_seconds | default(5) }}"
      HealthyThresholdCount: "{{ item.target_group.healthy_threshold_count | default(2) }}"
      UnhealthyThresholdCount: "{{ item.target_group.unhealthy_threshold_count | default(omit) }}"
      Matcher: "{{ item.target_group.matcher | default(omit) }}"
  register: tg_info
  with_items: "{{ listener_item.rules }}"

```

___

## Installation

Do the following to install the aws module in your Ansible environment:

1. Clone this repository or download the ZIP file.

2. Copy the *.py files from the library directory to your installation custom module directory.  This is, by default, in `./library` which is relative to where your playbooks are located. Refer to the [docs](http://docs.ansible.com/ansible/developing_modules.html#developing-modules) for more information.

3. Make sure boto3 is installed.








