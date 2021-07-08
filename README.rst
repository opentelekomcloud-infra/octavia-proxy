=============
Octavia Proxy
=============

This project translates Octavia API requests into elbv2 and elbv3 of the Open
Telekom Cloud. It is required due to missing possibility to implement elbv3
support as a native Octavia driver (it doesn't offer admin type of access and
to have primary data source in Octavia).

Goals
-----

- provide customer facing load balancer APIs using Octavia API
- cover elbv3 and elbv2
- Admin APIs are not going to be implemented

Status
------

POC in development phase

Requirements
------------

- validatetoken (fork of keystonemiddleware.auth_token middleware to
  allow token validation in the frontend)
- python-otcextensions (elb branch)

Developer setup
---------------

- tox create venv for octavia-proxy
- source into it
- with the venv python go to otcextensions elb branch and do
  `python setup.py develop`
- add into the clouds.yaml
  `load_balancer_endpoint_override: http://127.0.0.1:9876/`.
  IMPORTANT (for now): do not use profile:otc
- get python-openstackclient with python-octaviaclient (otce overrides
  loadbalancer function now, therefore - upstream)
- `python octavia_proxy/cmd/api.py --config-file etc/octavia.conf`
- `openstack loadbalancer list`
