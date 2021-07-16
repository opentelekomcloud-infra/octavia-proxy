=========================
Octavia-Proxy Contributor
=========================

Contributor Guidelines
----------------------
.. toctree::
   :glob:
   :maxdepth: 1

   contributing.rst
   HACKING.rst


Developer Setup
---------------

- tox `tox -e py39 --notest`
- source into it
- `rm -rf .tox/py39/lib/python3.9/site-packages/otcextensions*`
- with the venv python go to otcextensions elb branch and do
  `python setup.py develop`
- add into the clouds.yaml
  `load_balancer_endpoint_override: http://127.0.0.1:9876/`.
  IMPORTANT (for now): do not use profile:otc
- get python-openstackclient with python-octaviaclient (otce overrides
  loadbalancer function now, therefore - upstream)
- `python octavia_proxy/cmd/api.py --config-file etc/octavia.conf`
- `openstack loadbalancer list`
