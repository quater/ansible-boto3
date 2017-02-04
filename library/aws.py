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

import datetime
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn, camel_dict_to_snake_dict, ec2_argument_spec

try:
    import boto3
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

version_added: "2.4?"

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
  convert_param_case:
    description:
      - When present, this parameter specifies whether to convert the parameter case to that required by the API.
        Some AWS APIs use camelCase, others PascaleCase.  If absent, no case conversion is performed on the parameters.
    required: false
    default: none
    choices: ["camel", "Pascale"]

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
      convert_param_case: Pascale
      params:
        dry_run: True
        group_name: Boto3ApiGroup
        description: boto3 security group created via aws module

    register: ec2_sg

  - debug:
      msg: "{{ ec2_sg }}"

'''

RETURN = '''
---
method_invocation_results:
    description: dictionary of items returned depending of the method called
    returned: success
    type: dict
'''

# ---------------------------------------------------------------------------------------------------
#          Helper functions
# ---------------------------------------------------------------------------------------------------


def pc(key):
    """
    Changes snake_case key into Pascale case equivalent. For example, 'this_function_name' becomes 'ThisFunctionName'.

    :param key:
    :return:
    """
    return "".join([token.capitalize() for token in key.split('_')])


def cc(key):
    """
    Changes snake_case key into camel case equivalent. For example, 'this_function_name' becomes 'thisFunctionName'.
    :param key:
    :return:
    """
    token = pc(key)

    return "{}{}".format(token[0].lower(), token[1:])


def as_is(key):
    """
    Return case as is.

    :param key:
    :return:
    """
    return key


def fix_return(node):
    """
    fix up returned dictionary, converting objects to values.

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


def fix_input(node, key_case=as_is):
    """
    fixup params dictionary with proper parameter case (and to allow for numeric values)

    :param node:
    :param key_case:
    :return:
    """

    if isinstance(node, list):
        node_value = [fix_input(item, key_case) for item in node]
    elif isinstance(node, dict):
        node_value = dict(
            [(key_case(item), fix_input(node[item], key_case))
                for item in node.keys() if not (isinstance(node[item], basestring) and node[item].startswith('__omit_'))
             ]
        )
    elif node.isdigit():
        node_value = int(node)
    elif node.startswith('_') and node[1:].isdigit():
        node_value = str(node[1:])
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
            method=dict(required=True, default=None, aliases=['method_name', 'action']),
            params=dict(type='dict', required=False, default={}, aliases=['method_params']),
            convert_param_case=dict(required=False, default=None, choices=['camel', 'Pascale'])
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

    if module.params['convert_param_case'] == 'camel':
        key_case = cc
    elif module.params['convert_param_case'] == 'Pascale':
        key_case = pc
    else:
        key_case = as_is

    params = fix_input(module.params['params'], key_case)

    try:
        response = service_method(**params)

        meta_data = response.pop('ResponseMetadata')
        response['boto3'] = boto3.__version__
        if str(meta_data['HTTPStatusCode']).startswith('2'):
            response['changed'] = True

    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg="Client error - {0}".format(e))

    module.exit_json(**camel_dict_to_snake_dict(fix_return(response)))

if __name__ == '__main__':
    main()
