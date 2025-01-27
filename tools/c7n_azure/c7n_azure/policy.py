# Copyright 2015-2018 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import json

from c7n_azure.function_package import FunctionPackage
from c7n_azure.template_utils import TemplateUtilities

from c7n import utils
from c7n.policy import ServerlessExecutionMode, PullMode, execution


class AzureFunctionMode(ServerlessExecutionMode):
    """A policy that runs/executes in azure functions."""

    schema = {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'provision-options': {
                'type': 'object',
                'location': 'string',
                'appInsightsLocation': 'string',
                'servicePlanName': 'string',
                'sku': 'string',
                'workerSize': 'number',
                'skuCode': 'string'
            }
        }
    }

    POLICY_METRICS = ('ResourceCount', 'ResourceTime', 'ActionTime')

    def __init__(self, policy):
        self.policy = policy
        self.template_util = TemplateUtilities()
        self.log = logging.getLogger('custodian.azure.AzureFunctionMode')

    def run(self, event=None, lambda_context=None):
        """Run the actual policy."""
        raise NotImplementedError("subclass responsibility")

    def provision(self):
        """Provision any resources needed for the policy."""
        parameters = self.get_parameters()
        group_name = parameters['servicePlanName']['value']
        webapp_name = parameters['name']['value']

        existing_webapp = self.template_util.resource_exist(group_name, webapp_name)

        if not existing_webapp:
            self.template_util.create_resource_group(
                group_name, {'location': parameters['location']['value']})

            self.template_util.deploy_resource_template(
                group_name, 'dedicated_functionapp.json', parameters).wait()
        else:
            self.log.info("Found existing App %s (%s) in group %s" %
                          (webapp_name, existing_webapp.location, group_name))

        self.log.info("Building function package for %s" % webapp_name)

        archive = FunctionPackage(self.policy.data)
        archive.build()

        if archive.status(webapp_name):
            archive.publish(webapp_name)
        else:
            self.log.error("Aborted deployment, ensure Application Service is healthy.")

    def get_parameters(self):
        parameters = self.template_util.get_default_parameters(
            'dedicated_functionapp.parameters.json')

        data = self.policy.data

        updated_parameters = {
            'name': (data['mode']['provision-options']['servicePlanName'] +
                     '-' +
                     data['name']).replace(' ', '-').lower(),

            'storageName': data['mode']['provision-options']['servicePlanName']
        }

        if 'mode' in data:
            if 'provision-options' in data['mode']:
                updated_parameters.update(data['mode']['provision-options'])

        parameters = self.template_util.update_parameters(parameters, updated_parameters)

        return parameters

    def get_logs(self, start, end):
        """Retrieve logs for the policy"""
        raise NotImplementedError("subclass responsibility")

    def validate(self):
        """Validate configuration settings for execution mode."""


@execution.register('azure-periodic')
class AzurePeriodicMode(AzureFunctionMode, PullMode):
    """A policy that runs/executes in azure functions at specified
    time intervals."""
    schema = utils.type_schema('azure-periodic',
                               schedule={'type': 'string'},
                               rinherit=AzureFunctionMode.schema)

    def run(self, event=None, lambda_context=None):
        """Run the actual policy."""
        return PullMode.run(self)

    def get_logs(self, start, end):
        """Retrieve logs for the policy"""
        raise NotImplementedError("error - not implemented")


@execution.register('azure-stream')
class AzureStreamMode(AzureFunctionMode):
    """A policy that runs/executes in azure functions from an
    azure activity log stream."""

    schema = utils.type_schema('azure-stream', rinherit=AzureFunctionMode.schema)

    def run(self, event=None, lambda_context=None):
        """Run the actual policy."""
        self.log.info(json.dumps(lambda_context))
        raise NotImplementedError("error - not implemented")

    def get_logs(self, start, end):
        """Retrieve logs for the policy"""
        raise NotImplementedError("error - not implemented")
