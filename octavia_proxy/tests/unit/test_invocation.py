#    Copyright 2018 Rackspace, US Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from unittest import mock, skip

from oslo_config import cfg
from otcextensions.sdk.elb.v2 import load_balancer as elbv2
from otcextensions.sdk.vlb.v3 import load_balancer as elbv3

import octavia_proxy.tests.unit.base as base
from octavia_proxy.api.common.invocation import driver_invocation

CONF = cfg.CONF


class TestDriverInvocation(base.TestCase):
    attrs_v2 = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'name': 'test_v2',
        'availability_zone': 'eu-de-01',
        'admin_state_up': True,
        'subnet_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'created_at': '2021-08-10T09:39:24+00:00',
        'updated_at': '2021-08-10T09:39:24+00:00',
        'description': 'Test',
        'guaranteed': True,
        'l7policies': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'listeners': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'pools': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'location': None,
        'project_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'provider': 'elbv2',
        'vpc_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'network_ids': ['07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'],
    }
    attrs_v3 = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'name': 'test_v3',
        'availability_zone': 'eu-nl-01',
        'admin_state_up': True,
        'subnet_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'network_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'created_at': '2021-08-10T09:39:24+00:00',
        'updated_at': '2021-08-10T09:39:24+00:00',
        'description': 'Test',
        'guaranteed': True,
        'l7policies': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'listeners': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'pools': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'location': None,
        'project_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'provider': 'elbv3',
        'vpc_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'network_ids': ['07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'],
    }

    def setUp(self):
        super().setUp()
        self.context = mock.MagicMock()
        self.context.session = mock.MagicMock()
        self.session = self.context.session
        self.lb_v2 = elbv2.LoadBalancer(**self.attrs_v2)
        self.lb_v3 = elbv3.LoadBalancer(**self.attrs_v3)
        self.session.elb.find_load_balancer = mock.MagicMock(
            return_value=self.lb_v2
        )
        self.session.vlb.find_load_balancer = mock.MagicMock(
            return_value=self.lb_v3
        )
        self.context.project_id = 'id'
        self.driver_factory = mock.MagicMock()
        self.driver_call = mock.MagicMock()
        self.driver_factory.get_driver = mock.MagicMock()
        self.test_uuid = '29bb7aa5-44d2-4aaf-8e49-993091c7fa42'

    @skip
    def test_parallel_execution(self):
        CONF.api_settings.enabled_provider_drivers = {
            'elbv2': 'The ELBv2 driver.',
            'elbv3': 'The ELBv3 driver.'
        }
        call = driver_invocation(
            self.context,
            'loadbalancer_get',
            True,
            self.test_uuid
        )

    def test_sequential_execution(self):
        CONF.api_settings.enabled_provider_drivers = {
            'elbv2': 'The ELBv2 driver.',
            'elbv3': 'The ELBv3 driver.'
        }
        call = driver_invocation(
            self.context,
            'loadbalancer_get',
            False,
            self.test_uuid
        )
