#!/usr/bin/python
# (c) 2016, Pierre Jodouin <pjodouin(at)virtualcomputing.solutions
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import json

try:
    import boto3
    import boto
    from botocore.response import StreamingBody
    from botocore.exceptions import ClientError, EndpointConnectionError, ParamValidationError, MissingParametersError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


DOCUMENTATION = '''
---
module: boto3_api
short_description: Invokes an AWS Lambda function
description:
    - This module provides a one-to-one mapping to all boto3 methods for each AWS service.  Refer to the Boto3 documentation for parameter syntax and definitions.

version_added: "2.3?"

author: Pierre Jodouin (@pjodouin)
options:
  service:
    description:
      - The AWS service name e.g. ec2, apigateway, cloudformation, lambda, s3,...etc.
    required: true
    default: none
  method:
    description:
      - The name of the client method for the specified service.
    required: true
    default: none
  params:
    description:
      - Valid parameters required or optional relating to the method being called. Refer to Boto3 documentation for parameter syntax and definitions.
    required: false
    default: {}
requirements:
    - boto3
extends_documentation_fragment:
    - aws

'''

EXAMPLES = '''
---
- hosts: localhost
  connection: local
  gather_facts: no
  vars:
    state: present

  tasks:
  - name : Just debugging
    debug:
      msg: "Boto3 api testing"

  - name: "get EC2 instances"
    boto3_api:
      service: ec2
      method: describe_instances
      params:
        DryRun: False
    register: ec2_instances

  - debug:
      msg: "{{ ec2_instances }}"

  - name: "get RDS instances"
    boto3_api:
      service: rds
      method: describe_db_instances
    register: db_instances

  - debug:
      msg: "{{ db_instances }}"

  - name: "create security group"
    boto3_api:
      service: ec2
      method: create_security_group
      params:
        DryRun: True
        GroupName: Boto3ApiGroup
        Description: boto3 security group created via aws module

    register: ec2_sg

  - debug:
      msg: "{{ ec2_sg }}"

'''

RETURN = '''
---
lambda_invocation_results:
    description: dictionary of items returned depending of the method called
    returned: success
    type: dict
'''

# ---------------------------------------------------------------------------------------------------
#          Helper functions
# ---------------------------------------------------------------------------------------------------


def fix_return(node):
    """
    fixup returned dictionary

    :param node:
    :return:
    """

    if isinstance(node, datetime.datetime):
        node_value = str(node)
    elif isinstance(node, list):
        node_value = [fix_return(item) for item in node]
    elif isinstance(node, dict):
        node_value = dict([(item, fix_return(node[item])) for item in node.keys()])
    elif isinstance(node, StreamingBody):
        node_value = node.read()
    else:
        node_value = node

    return node_value


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: ansible facts
    """

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            service=dict(required=True, default=None, aliases=['service_name']),
            method=dict(required=True, default=None, aliases=['method_name']),
            params=dict(type='dict', required=False, default={}, aliases=['method_params']),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        mutually_exclusive=[],
        required_together=[]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')

    try:
        region, endpoint, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        aws_connect_kwargs.update(dict(region=region,
                                       endpoint=endpoint,
                                       conn_type='client',
                                       resource=module.params['service']
                                       ))
        client = boto3_conn(module, **aws_connect_kwargs)
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg="Can't authorize connection - {0}".format(e))
    except EndpointConnectionError as e:
        module.fail_json(msg="Connection Error - {0}".format(e))

    service_method = getattr(client, module.params['method'])

    try:
        response = service_method(**module.params['params'])

        meta_data = response.pop('ResponseMetadata')
        if str(meta_data['HTTPStatusCode']).startswith('2'):
            response['changed'] = True
            response['boto3'] = boto3.__version__

    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg="Client error - {0}".format(e))

    # module.exit_json(**response)
    module.exit_json(**camel_dict_to_snake_dict(fix_return(response)))


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
