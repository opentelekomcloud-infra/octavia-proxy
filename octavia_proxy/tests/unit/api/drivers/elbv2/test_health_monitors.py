from unittest import mock

from keystoneauth1 import adapter
from openstack.load_balancer.v2._proxy import Proxy
from openstack.load_balancer.v2.health_monitor import HealthMonitor

from octavia_proxy.api.drivers.elbv2 import driver
from octavia_proxy.tests.unit import base
from octavia_proxy.tests.unit.api.drivers.elbv2.fixtures import FakeResponse

EXAMPLE = {
    'admin_state_up': True,
    'pool_id': 'bb44bffb-05d9-412c-9d9c-b189d9e14193',
    'domain_name': 'www.test.com',
    'delay': 10,
    'max_retries': 10,
    'timeout': 10,
    'type': 'HTTP',
}


class TestElbv2HealthMonitors(base.TestCase):
    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.resp = FakeResponse({})
        self.sess = mock.Mock(spec=adapter.Adapter)
        self.sess.default_microversion = None
        self.sess.elb = Proxy(self.sess)
        self.sess.elb.post = mock.Mock(return_value=self.resp)
        self.sess.elb.get = mock.Mock(return_value=self.resp)
        self.sess.elb.put = mock.Mock(return_value=self.resp)
        self.sess.elb.delete = mock.Mock(
            return_value=FakeResponse({}, status_code=204))

    @property
    def example_monitor(self):
        return {
            'monitor_port': None,
            'name': '',
            'admin_state_up': True,
            'tenant_id': '601240b9c5c94059b63d484c92cfe308',
            'domain_name': None,
            'delay': 5,
            'max_retries': 3,
            'http_method': 'GET',
            'timeout': 10,
            'pools': [
                {
                    'id': 'caef8316-6b65-4676-8293-cf41fb63cc2a'
                }
            ],
            'url_path': '/',
            'type': 'HTTP',
            'id': '1b587819-d619-49c1-9101-fe72d8b361ef'
        }

    def test_list(self):
        response = {
            'healthmonitors': [
                self.example_monitor
            ]
        }

        query = {
            'pool_id': 'bb44bffb-05d9-412c-9d9c-b189d9e14193',
            'delay': 5,
            'max_retries': 3,
            'timeout': 10,
            'type': 'HTTP',
            'admin_state_up': True,
        }
        self.resp.body = response
        monitor_list = self.driver.health_monitors(self.sess, query)
        self.assertEqual(1, len(monitor_list))
        self.sess.elb.get.assert_called_once()
        self.sess.elb.get.assert_called_with(
            '/lbaas/healthmonitors',
            headers={'Accept': 'application/json'},
            params=query,
            microversion=None,
        )

    def test_get(self):
        expected_monitor = self.example_monitor
        self.resp.body = {
            'healthmonitor': self.example_monitor
        }

        monitor = self.driver.health_monitor_get(self.sess, expected_monitor['id'])
        self.sess.elb.get.assert_called_once()
        self.sess.elb.get.assert_called_with(
            f'lbaas/healthmonitors/{expected_monitor["id"]}',
            microversion=None,
            params={},
        )
        self.assertEqual(expected_monitor['id'], monitor.id)
        self.assertEqual(expected_monitor['admin_state_up'], monitor.admin_state_up)

    def test_create(self):
        self.resp.body = {
            'healthmonitor': self.example_monitor
        }
        opts = {
            'delay': 5,
            'max_retries': 3,
            'http_method': 'GET',
            'timeout': 10,
            'pools': [
                {
                    'id': 'caef8316-6b65-4676-8293-cf41fb63cc2a'
                }
            ],
            'url_path': '/',
            'type': 'HTTP',
        }
        self.driver.health_monitor_create(self.sess, opts)
        self.sess.elb.post.assert_called_once()
        self.sess.elb.post.assert_called_with(
            '/lbaas/healthmonitors',
            json={
                'healthmonitor': opts
            },
            headers={},
            params={},
            microversion=None,
        )

    def test_update(self):
        response_monitor = self.example_monitor
        response_monitor["max_retries"] = 5
        response_monitor["delay"] = 10
        response_monitor["timeout"] = 20

        self.resp.body = {
            'healthmonitor': response_monitor
        }
        opts = {
            'delay': 10,
            'max_retries': 5,
            'timeout': 20,
        }
        old = HealthMonitor(**self.example_monitor)
        self.driver.health_monitor_update(self.sess, old, opts)
        self.sess.elb.put.assert_called_once()
        self.sess.elb.put.assert_called_with(
            f'lbaas/healthmonitors/{old.id}',
            json={
                'healthmonitor': opts
            },
            headers={},
            microversion=None,
        )

    def test_delete(self):
        monitor = HealthMonitor(**self.example_monitor)
        self.driver.health_monitor_delete(self.sess, monitor)
        self.sess.elb.delete.assert_called_once()
        self.sess.elb.delete.assert_called_with(
            f'lbaas/healthmonitors/{monitor.id}',
            headers={},
            microversion=None,
        )

    @property
    def invalid_opts(self):
        return {
            'delay': 5,
            'max_retries': 3,
            'http_method': 'GET',
            'timeout': 10,
            'url_path': '/',
            'type': 'INVALID_TYPE',
        }

    def test_create_validate(self):
        self.assertRaises(ValueError,
                          self.driver.health_monitor_create,
                          self.sess, self.invalid_opts)

    def test_update_validate(self):
        self.assertRaises(ValueError,
                          self.driver.health_monitor_update,
                          self.sess, self.example_monitor, self.invalid_opts)
