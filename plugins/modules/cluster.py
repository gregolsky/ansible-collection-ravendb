#!/usr/bin/python
# -*- coding: utf-8 -*-

# MIT License
# Copyright: (c) 2021, Grzegorz Lachowski <gregory.lachowski@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
 
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_test_info

short_description: This is my test info module

version_added: "1.0.0"

description: This is my longer description explaining my test info module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test_info:
    name: hello world
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
my_useful_info:
    description: The dictionary containing information about your system.
    type: dict
    returned: always
    sample: {
        'foo': 'bar',
        'answer': 42,
    }
'''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

def get_cluster_topology(node_url, client_cert=None, client_key=None):

    cluster_topology_ep = '/cluster/topology'
    cluster_topology_url = node_url + cluster_topology_ep

    #https://github.com/ansible/ansible/blob/devel/lib/ansible/module_utils/urls.py#L1558
    open_url(
        url_action,
        method="GET",
        headers=headers,
        url_username=module.params.get('user'),
        url_password=module.params.get('pwd'),
        force_basic_auth=True,data=json.dumps(payload))

def add_node_to_cluster(first_cluster_node_url, node_url_to_be_added):
    # TODO
    pass

def update_cluster(current_topology, target_topology):

    # TODO case-insensitive node tags in args

    current_node = set(current_topology.items())
    target_node = set(target_node_tags.items())

    # should usually be A
    common_node = sorted(current_node_tags.intersection(target_node_tags))[0]
    if not common_node:
        raise Error('Could not find a common node in between the actual and target cluster topology.')
    

    for node_tag in target_topology.keys():
        if node_tag not in actual_topology:
            return False
        
        try:
            actual_node = actual_topology[node_tag]
        except KeyError:
            raise Error()
            

        if actual_topology[node_tag] != expected_topology[node_tag]:
            return False

def run_module():
    # define available arguments/parameters a user can pass to the module
    # nodes { A: "https://a.test.ravendb.run"... }
    module_args = dict(
        name=dict(type='str', required=True),
        nodes=dict(type='dict', elements='str', required=True),
        client_cert=dict(type='str'),
        client_key=dict(type='str'),
        validate_certs=dict(type='bool', default=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message='',
        cluster_topology=None,
    )


    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    args = dict(**module.params)
    nodes_arg = list(args['nodes'].items())
    client_cert = args['client_cert']
    client_key = args['client_key']

    first_node_url = nodes_arg[1].rstrip('/')

    cluster_topology = get_cluster_topology(first_node_url, client_cert, client_key)

    current_cluster_topology = cluster_topology['Topology']['AllNodes']
    result['cluster_topology'] = current_cluster_topology

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)



    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = module.params['name']
    result['message'] = 'goodbye'
    result['my_useful_info'] = {
        'foo': 'bar',
        'answer': 42,
    }
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()