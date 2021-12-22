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
from unittest import mock

from oslo_config import cfg
from otcextensions.sdk.vlb.v3 import (
    load_balancer as elbv3,
    listener as lsv3,
    pool as plv3,
    member as memv3,
    health_monitor as hmv3,
    l7_policy as l7pv3,
    l7_rule as l7rv3,
    flavor as flv3
)

from octavia_proxy.api.v2.controllers import base as _b
from octavia_proxy.common import exceptions
from octavia_proxy.tests.unit.api.controllers import base

CONF = cfg.CONF


class TestBaseController(base.TestCase):
    def setUp(self):
        super().setUp()
        CONF.api_settings.enabled_provider_drivers = {
            'elbv3': 'The ELBv3 driver.',
        }

        self.bc = _b.BaseController

        self.context = mock.MagicMock()
        self.context.session = mock.MagicMock()
        self.context.project_id = 'id'
        self.session = self.context.session

    def test_basic(self):
        self.assertEqual(self.bc.RBAC_TYPE, None)
        self.assertIsNotNone(getattr(self.bc, 'find_load_balancer'))
        self.assertIsNotNone(getattr(self.bc, 'find_listener'))
        self.assertIsNotNone(getattr(self.bc, 'find_pool'))
        self.assertIsNotNone(getattr(self.bc, 'find_member'))
        self.assertIsNotNone(getattr(self.bc, 'find_health_monitor'))
        self.assertIsNotNone(getattr(self.bc, 'find_l7policy'))
        self.assertIsNotNone(getattr(self.bc, 'find_l7rule'))
        self.assertIsNotNone(getattr(self.bc, 'find_flavor'))
        self.assertIsNotNone(getattr(self.bc, '_convert_sdk_to_type'))
        self.assertIsNotNone(getattr(self.bc, '_validate_protocol'))
        self.assertIsNotNone(
            getattr(self.bc, '_is_only_specified_in_request')
        )
        self.assertIsNotNone(
            getattr(self.bc, '_validate_pool_request_for_tcp_udp')
        )
        self.assertIsNotNone(
            getattr(self.bc, '_validate_healthmonitor_request_for_udp')
        )
        self.assertIsNotNone(getattr(self.bc, '_auth_get_all'))
        self.assertIsNotNone(getattr(self.bc, '_auth_validate_action'))
        self.assertIsNotNone(getattr(self.bc, '_filter_fields'))
        self.assertIsNotNone(getattr(self.bc, '_get_attrs'))

    def test_find_load_balancer(self):
        lb_v3 = elbv3.LoadBalancer(
            id='07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
            name='test_v3',
            created_at='2021-08-10T09:39:24+00:00',
            updated_at='2021-08-10T09:39:24+00:00'
        )
        self.session.vlb.find_load_balancer = mock.MagicMock(
            return_value=lb_v3
        )
        lb = self.bc().find_load_balancer(self.context, 'id')

        self.assertIsNotNone(lb)
        self.session.vlb.find_load_balancer.assert_called_with(
            ignore_missing=True,
            name_or_id='id'
        )

    def test_find_load_balancer_not_found(self):
        self.assertRaises(
            exceptions.NotFound,
            self.bc().find_load_balancer,
            self.context,
            'id')

    def test_find_listener(self):
        ls_v3 = lsv3.Listener(
            id='07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
            loadbalancer_id='07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
            protocol_port=80,
            protocol="TCP",
            name='test_v3',
            created_at='2021-08-10T09:39:24+00:00',
            updated_at='2021-08-10T09:39:24+00:00',
            load_balancers=[{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        )
        self.session.vlb.find_listener = mock.MagicMock(
            return_value=ls_v3
        )
        ls = self.bc().find_listener(self.context, 'id')

        self.assertIsNotNone(ls)
        self.session.vlb.find_listener.assert_called_with(
            ignore_missing=True,
            name_or_id='id'
        )

    def test_find_listener_not_found(self):
        self.assertRaises(
            exceptions.NotFound,
            self.bc().find_listener,
            self.context,
            'id')

    def test_find_pool(self):
        pool_v3 = plv3.Pool(
            id='07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
            name='test_v3',
        )
        self.session.vlb.find_pool = mock.MagicMock(
            return_value=pool_v3
        )
        pool = self.bc().find_pool(self.context, 'id')

        self.assertIsNotNone(pool)
        self.session.vlb.find_pool.assert_called_with(
            ignore_missing=True,
            name_or_id='id'
        )

    def test_find_pool_not_found(self):
        self.assertRaises(
            exceptions.NotFound,
            self.bc().find_pool,
            self.context,
            'id')

    def test_find_member(self):
        member_v3 = memv3.Member(
            id='07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
            name='test_v3',
        )
        self.session.vlb.find_member = mock.MagicMock(
            return_value=member_v3
        )
        member = self.bc().find_member(self.context, 'pid', 'id')

        self.assertIsNotNone(member)
        self.session.vlb.find_member.assert_called_with(
            ignore_missing=True,
            pool='pid',
            name_or_id='id'
        )

    def test_find_member_not_found(self):
        self.assertRaises(
            exceptions.NotFound,
            self.bc().find_member,
            self.context,
            'pid',
            'id')

    def test_find_health_monitor(self):
        hm_v3 = hmv3.HealthMonitor(
            id='07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
            pool_id='07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
            type='TCP',
        )
        self.session.vlb.find_health_monitor = mock.MagicMock(
            return_value=hm_v3
        )
        hm = self.bc().find_health_monitor(self.context, 'id')

        self.assertIsNotNone(hm)
        self.session.vlb.find_health_monitor.assert_called_with(
            ignore_missing=True,
            name_or_id='id'
        )

    def test_find_health_monitor_not_found(self):
        self.assertRaises(
            exceptions.NotFound,
            self.bc().find_health_monitor,
            self.context,
            'id')

    def test_find_l7policy(self):
        pol_v3 = l7pv3.L7Policy(
            id="8a1412f0-4c32-4257-8b07-af4770b604fd",
            listener_id="07f0a424-cdb9-4584-b9c0-6a38fbacdc3a",
        )
        self.session.vlb.find_l7_policy = mock.MagicMock(
            return_value=pol_v3
        )
        pol = self.bc().find_l7policy(self.context, 'id')

        self.assertIsNotNone(pol)
        self.session.vlb.find_l7_policy.assert_called_with(
            ignore_missing=True,
            name_or_id='id'
        )

    def test_find_l7policy_not_found(self):
        self.assertRaises(
            exceptions.NotFound,
            self.bc().find_l7policy,
            self.context,
            'id')

    def test_find_l7rule(self):
        rul_v3 = l7rv3.L7Rule(
            id="8a1412f0-4c32-4257-8b07-af4770b604fd",
        )
        self.session.vlb.find_l7_rule = mock.MagicMock(
            return_value=rul_v3
        )
        rul = self.bc().find_l7rule(self.context, 'pid', 'id')

        self.assertIsNotNone(rul)
        self.session.vlb.find_l7_rule.assert_called_with(
            ignore_missing=True,
            l7_policy='pid',
            name_or_id='id'
        )

    def test_find_l7rule_not_found(self):
        self.assertRaises(
            exceptions.NotFound,
            self.bc().find_l7rule,
            self.context,
            'rid',
            'id')

    def test_find_flavor(self):
        flav_v3 = flv3.Flavor(
            id="8a1412f0-4c32-4257-8b07-af4770b604fd",
            name='flavor',
            shared=True,
            project_id='pid',
        )
        self.session.vlb.get_flavor = mock.MagicMock(
            return_value=flav_v3
        )
        fl = self.bc().find_flavor(self.context, 'id')

        self.assertIsNotNone(fl)
        self.session.vlb.get_flavor.assert_called_with(
            'id'
        )

    def test_find_flavor_not_found(self):
        self.assertRaises(
            exceptions.NotFound,
            self.bc().find_flavor,
            self.context,
            'id')
