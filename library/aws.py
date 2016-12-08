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

import sys

try:
    import boto3
    import boto
    from botocore.exceptions import ClientError, EndpointConnectionError, ParamValidationError, MissingParametersError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


DOCUMENTATION = '''
---
module: boto3_api
short_description: Invokes an AWS Lambda function
description:
    - This module has a single purpose of triggering the execution of a specified lambda function.
      Use module M(lambda) to manage the lambda function itself, M(lambda_alias) to manage function aliases and
      M(lambda_event) to manage event source mappings.

version_added: "2.2"

author: Pierre Jodouin (@pjodouin)
options:
  function_name:
    description:
      - The Lambda function name. You can specify an unqualified function name (for example, "Thumbnail") or you can
        specify Amazon Resource Name (ARN) of the function. AWS Lambda also allows you to specify only the account ID
        qualifier (for example, "account-id:Thumbnail"). Note that the length constraint applies only to the ARN.
        If you specify only the function name, it is limited to 64 character in length.
    required: true
  qualifier:
    description:
      - You can use this optional parameter to specify a Lambda function version or alias name. If you specify function
        version, the API uses qualified function ARN to invoke a specific Lambda function. If you specify alias name,
        the API uses the alias ARN to invoke the Lambda function version to which the alias points.
        If you don't provide this parameter, then the API uses unqualified function ARN which results in invocation of
        the $LATEST version.
    required: false
    default: none
  invocation_type:
    description:
      - By default, the Invoke API assumes "RequestResponse" invocation type. You can optionally request asynchronous
        execution by specifying "Event" as the invocation type. You can also use this parameter to request AWS Lambda
        to not execute the function but do some verification, such as if the caller is authorized to invoke the
        function and if the inputs are valid. You request this by specifying "DryRun" as the invocation_type. This is
        useful in a cross-account scenario when you want to verify access to a function without running it.
    required: true
    choices: [
        "RequestResponse",
        "Event",
        "DryRun"
        ]
    default: RequestResponse
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
            # state=dict(required=False, default='present', choices=['present', 'absent']),
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

    # validate_params(module, aws)

    service_method = getattr(client, module.params['method'])

    try:
        response = service_method(**module.params['params'])

        meta_data = response.pop('ResponseMetadata')
        if str(meta_data['HTTPStatusCode']).startswith('2'):
            response['changed'] = True

    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg="Client error - {0}".format(e))

    module.exit_json(**response)


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
